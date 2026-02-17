import logging
import random
from dataclasses import dataclass, field

from bot.services.llm import (
    WordExplanation,
    explain_word,
    generate_random_words,
)

logger = logging.getLogger(__name__)


@dataclass
class OnboardingSession:
    user_id: int
    target_unknown: int = 10
    unknown_count: int = 0
    shown_words: list[str] = field(default_factory=list)
    word_bank: list[str] = field(default_factory=list)
    current_word: str | None = None
    current_options: list[str] = field(default_factory=list)
    correct_index: int = 0
    current_explanation: WordExplanation | None = None


_onboarding_sessions: dict[int, OnboardingSession] = {}


def create_session(telegram_id: int, user_id: int) -> OnboardingSession:
    session = OnboardingSession(user_id=user_id)
    _onboarding_sessions[telegram_id] = session
    return session


def get_session(telegram_id: int) -> OnboardingSession | None:
    return _onboarding_sessions.get(telegram_id)


def remove_session(telegram_id: int) -> None:
    _onboarding_sessions.pop(telegram_id, None)


async def get_next_word(session: OnboardingSession) -> str | None:
    """Get the next word from the bank, fetching more from LLM if needed."""
    if not session.word_bank:
        new_words = await generate_random_words(count=20, exclude=session.shown_words)
        session.word_bank.extend(new_words)

    if not session.word_bank:
        return None

    word = session.word_bank.pop(0)
    session.shown_words.append(word)
    session.current_word = word
    session.current_options = []
    session.correct_index = 0
    session.current_explanation = None
    return word


async def get_word_with_options(
    session: OnboardingSession,
) -> dict | None:
    """Get current word with quiz options (correct translation + distractors).

    Uses distractors from the explain_word response (single LLM call).
    """
    if not session.current_word:
        return None

    word = session.current_word

    try:
        explanation = await explain_word(word)
    except Exception:
        logger.exception("Failed to explain word for onboarding quiz: %s", word)
        return None

    session.current_explanation = explanation
    correct_translation = explanation.translation

    distractors = explanation.distractors[:3]
    # Fallback if LLM returned too few distractors
    fallback = ["ошибка", "неизвестно", "другое"]
    while len(distractors) < 3:
        distractors.append(fallback[len(distractors)])

    options = [correct_translation] + distractors
    random.shuffle(options)
    correct_index = options.index(correct_translation)

    session.current_options = options
    session.correct_index = correct_index

    return {
        "word": word,
        "correct": correct_translation,
        "options": options,
        "correct_index": correct_index,
        "explanation": explanation,
    }
