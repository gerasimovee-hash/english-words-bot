import logging
import random
from dataclasses import dataclass, field

from bot.services.llm import WordExplanation
from bot.services.word_bank import get_random_words

logger = logging.getLogger(__name__)


@dataclass
class OnboardingSession:
    user_id: int
    target_unknown: int = 10
    unknown_count: int = 0
    shown_words: list[str] = field(default_factory=list)
    word_bank: list[dict] = field(default_factory=list)
    current_word: str | None = None
    current_options: list[str] = field(default_factory=list)
    correct_index: int = 0
    current_translation: str | None = None
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


def get_next_word_with_options(session: OnboardingSession) -> dict | None:
    """Get next word with quiz options instantly from pre-built bank.

    No LLM calls — everything is pre-defined.
    """
    if not session.word_bank:
        session.word_bank = get_random_words(count=30, exclude=session.shown_words)

    if not session.word_bank:
        return None

    entry = session.word_bank.pop(0)
    word = entry["word"]
    correct = entry["translation"]
    distractors = list(entry["distractors"])

    session.shown_words.append(word)
    session.current_word = word
    session.current_translation = correct
    session.current_explanation = None

    options = [correct] + distractors
    random.shuffle(options)
    correct_index = options.index(correct)

    session.current_options = options
    session.correct_index = correct_index

    return {
        "word": word,
        "correct": correct,
        "options": options,
        "correct_index": correct_index,
    }
