import logging
from dataclasses import dataclass, field

from bot.services.llm import generate_random_words

logger = logging.getLogger(__name__)


@dataclass
class OnboardingSession:
    user_id: int
    target_unknown: int = 10
    unknown_count: int = 0
    shown_words: list[str] = field(default_factory=list)
    word_bank: list[str] = field(default_factory=list)
    current_word: str | None = None


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
    return word
