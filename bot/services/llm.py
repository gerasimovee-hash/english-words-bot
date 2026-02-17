import json
import logging
from dataclasses import dataclass

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from bot.config import settings

logger = logging.getLogger(__name__)

RANDOM_WORDS_PROMPT = """\
Generate a list of {count} random English words at B2-C1 level (upper-intermediate to advanced).
The words should be diverse: mix nouns, verbs, adjectives, and adverbs.
Prefer less common, more challenging vocabulary that an educated
adult might encounter in books, articles, or academic texts.
Do NOT include these words: {exclude}

Respond ONLY with a valid JSON array of strings, for example:
["word1", "word2", "word3"]
"""


EXPLAIN_PROMPT = """\
You are an English language tutor helping a Russian-speaking student.
The student encountered an unfamiliar English word or phrase while reading.

Given the word/phrase, provide:
1. "corrected_word" — if the word contains a typo or spelling mistake, return
   the corrected version. If the spelling is correct, return the word as-is.
2. "translation" — the most common Russian translation
3. "translations" — a list of 2-4 different Russian translations (synonyms),
   from most common to least common
4. "distractors" — a list of exactly 3 WRONG but plausible Russian translations
   that could be confused with the correct one. They must NOT be synonyms of
   the correct translation. They should be real Russian words of the same part
   of speech when possible.
5. "meanings" — a list of different meanings with short explanations in Russian
6. "examples" — 2-3 example sentences in English with Russian translations
7. "collocations" — common collocations and fixed expressions that use this word, with translations

Respond ONLY with valid JSON in this exact format:
{
  "corrected_word": "corrected spelling or same word",
  "translation": "основной перевод",
  "translations": ["перевод 1", "перевод 2", "перевод 3"],
  "distractors": ["неправильный 1", "неправильный 2", "неправильный 3"],
  "meanings": [
    {"meaning": "значение 1", "explanation": "пояснение на русском"},
    {"meaning": "значение 2", "explanation": "пояснение на русском"}
  ],
  "examples": [
    {"en": "Example sentence", "ru": "Перевод примера"}
  ],
  "collocations": [
    {"en": "expression", "ru": "перевод"}
  ]
}
"""


@dataclass
class WordExplanation:
    translation: str
    translations: list[str]
    distractors: list[str]
    corrected_word: str | None
    meanings: list[dict[str, str]]
    examples: list[dict[str, str]]
    collocations: list[dict[str, str]]
    raw_text: str  # Formatted text for display


async def generate_random_words(count: int = 20, exclude: list[str] | None = None) -> list[str]:
    """Generate a batch of random English words at B1-B2 level via LLM."""
    exclude_str = ", ".join(exclude) if exclude else "none"
    prompt = RANDOM_WORDS_PROMPT.format(count=count, exclude=exclude_str)

    async with GigaChat(
        credentials=settings.gigachat_credentials,
        model="GigaChat-2-Max",
        scope="GIGACHAT_API_PERS",
        verify_ssl_certs=False,
    ) as client:
        response = await client.achat(
            Chat(
                messages=[
                    Messages(role=MessagesRole.USER, content=prompt),
                ],
                temperature=0.9,
            )
        )

    content = response.choices[0].message.content or "[]"
    # Strip markdown fences if present
    if "```" in content:
        lines = content.split("\n")
        json_lines = []
        inside = False
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                json_lines.append(line)
        if json_lines:
            content = "\n".join(json_lines)

    try:
        words = json.loads(content)
        if isinstance(words, list):
            return [w for w in words if isinstance(w, str)]
    except json.JSONDecodeError:
        logger.error("Failed to parse random words response: %s", content)

    return []


async def explain_word(word: str) -> WordExplanation:
    async with GigaChat(
        credentials=settings.gigachat_credentials,
        model="GigaChat-2-Max",
        scope="GIGACHAT_API_PERS",
        verify_ssl_certs=False,
    ) as client:
        response = await client.achat(
            Chat(
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=EXPLAIN_PROMPT),
                    Messages(role=MessagesRole.USER, content=word),
                ],
                temperature=0.3,
            )
        )

    content = response.choices[0].message.content or "{}"
    data = _parse_json(content)

    translation = data.get("translation", "—")
    translations = data.get("translations", [translation])
    if not translations:
        translations = [translation]
    distractors = data.get("distractors", [])
    if not isinstance(distractors, list):
        distractors = []
    corrected_word_raw = data.get("corrected_word", word)
    corrected_word = (
        corrected_word_raw
        if corrected_word_raw and corrected_word_raw.lower() != word.lower()
        else None
    )
    meanings = data.get("meanings", [])
    examples = data.get("examples", [])
    collocations = data.get("collocations", [])

    display_word = corrected_word if corrected_word else word
    raw_text = format_explanation(display_word, translation, meanings, examples, collocations)

    return WordExplanation(
        translation=translation,
        translations=translations,
        distractors=distractors,
        corrected_word=corrected_word,
        meanings=meanings,
        examples=examples,
        collocations=collocations,
        raw_text=raw_text,
    )


def format_explanation(
    word: str,
    translation: str,
    meanings: list[dict[str, str]],
    examples: list[dict[str, str]],
    collocations: list[dict[str, str]],
) -> str:
    lines = [f"<b>{word}</b> — {translation}\n"]

    if meanings:
        lines.append("<b>Значения:</b>")
        for i, m in enumerate(meanings, 1):
            lines.append(f"  {i}. {m.get('meaning', '')} — {m.get('explanation', '')}")
        lines.append("")

    if examples:
        lines.append("<b>Примеры:</b>")
        for ex in examples:
            lines.append(f"  • {ex.get('en', '')}")
            lines.append(f"    <i>{ex.get('ru', '')}</i>")
        lines.append("")

    if collocations:
        lines.append("<b>Устойчивые выражения:</b>")
        for col in collocations:
            lines.append(f"  • {col.get('en', '')} — {col.get('ru', '')}")

    return "\n".join(lines)


DISTRACTORS_PROMPT = """\
You are an English language tutor. Given an English word and its correct Russian \
translation, generate {count} WRONG but plausible Russian translations (distractors).

The distractors should:
- Be real Russian words (nouns, verbs, adjectives as appropriate)
- Be somewhat related or similar-sounding to the correct translation, but clearly wrong
- Be the same part of speech as the correct translation when possible
- NOT be synonyms of the correct translation

Word: {word}
Correct translation: {correct_translation}

Respond ONLY with a JSON array of {count} strings, for example:
["неправильный1", "неправильный2", "неправильный3"]
"""


async def generate_distractors(word: str, correct_translation: str, count: int = 3) -> list[str]:
    """Generate plausible wrong translations for a quiz."""
    prompt = DISTRACTORS_PROMPT.format(
        word=word, correct_translation=correct_translation, count=count
    )

    async with GigaChat(
        credentials=settings.gigachat_credentials,
        model="GigaChat-2-Max",
        scope="GIGACHAT_API_PERS",
        verify_ssl_certs=False,
    ) as client:
        response = await client.achat(
            Chat(
                messages=[
                    Messages(role=MessagesRole.USER, content=prompt),
                ],
                temperature=0.7,
            )
        )

    content = response.choices[0].message.content or "[]"
    parsed = _parse_json_array(content)
    if len(parsed) >= count:
        return parsed[:count]
    # Fallback if LLM returned too few
    fallback = ["ошибка", "неизвестно", "другое"]
    while len(parsed) < count:
        parsed.append(fallback[len(parsed) % len(fallback)])
    return parsed


def _parse_json_array(text: str) -> list[str]:
    """Extract and parse a JSON array from LLM response."""
    if "```" in text:
        lines = text.split("\n")
        inside = False
        json_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                json_lines.append(line)
        if json_lines:
            text = "\n".join(json_lines)

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return [s for s in result if isinstance(s, str)]
    except json.JSONDecodeError:
        pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, list):
                return [s for s in result if isinstance(s, str)]
        except json.JSONDecodeError:
            pass

    return []


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from LLM response, handling markdown fences and extra text."""
    # Strip markdown code fences
    if "```" in text:
        lines = text.split("\n")
        inside = False
        json_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                json_lines.append(line)
        if json_lines:
            text = "\n".join(json_lines)

    # Try parsing as-is first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the first { and last } to extract JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])

    return {}
