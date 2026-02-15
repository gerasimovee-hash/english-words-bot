import json
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from bot.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)

EXPLAIN_PROMPT = """\
You are an English language tutor helping a Russian-speaking student.
The student encountered an unfamiliar English word or phrase while reading.

Given the word/phrase, provide:
1. "translation" — the most common Russian translation(s)
2. "meanings" — a list of different meanings with short explanations in Russian
3. "examples" — 2-3 example sentences in English with Russian translations
4. "collocations" — common collocations and fixed expressions that use this word, with translations

Respond ONLY with valid JSON in this exact format:
{
  "translation": "основной перевод",
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
    meanings: list[dict[str, str]]
    examples: list[dict[str, str]]
    collocations: list[dict[str, str]]
    raw_text: str  # Formatted text for display


async def explain_word(word: str) -> WordExplanation:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": EXPLAIN_PROMPT},
            {"role": "user", "content": word},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    content = response.choices[0].message.content or "{}"
    data = json.loads(content)

    translation = data.get("translation", "—")
    meanings = data.get("meanings", [])
    examples = data.get("examples", [])
    collocations = data.get("collocations", [])

    raw_text = format_explanation(word, translation, meanings, examples, collocations)

    return WordExplanation(
        translation=translation,
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
