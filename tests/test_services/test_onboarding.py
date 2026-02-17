from unittest.mock import AsyncMock, patch

from bot.services.onboarding import (
    OnboardingSession,
    create_session,
    get_next_word,
    get_session,
    remove_session,
)


def test_create_and_get_session():
    session = create_session(telegram_id=111, user_id=1)
    assert session.user_id == 1
    assert session.unknown_count == 0
    assert session.target_unknown == 10

    retrieved = get_session(111)
    assert retrieved is session

    remove_session(111)
    assert get_session(111) is None


def test_remove_nonexistent_session():
    remove_session(999)  # should not raise


async def test_get_next_word_from_bank():
    session = OnboardingSession(
        user_id=1,
        word_bank=["hello", "world", "test"],
    )

    word = await get_next_word(session)
    assert word == "hello"
    assert word in session.shown_words
    assert session.current_word == "hello"
    assert len(session.word_bank) == 2


async def test_get_next_word_fetches_from_llm():
    session = OnboardingSession(user_id=1, word_bank=[])

    with patch(
        "bot.services.onboarding.generate_random_words",
        new_callable=AsyncMock,
        return_value=["apple", "banana", "cherry"],
    ):
        word = await get_next_word(session)

    assert word == "apple"
    assert session.current_word == "apple"
    assert "banana" in session.word_bank
    assert "cherry" in session.word_bank


async def test_get_next_word_returns_none_when_empty():
    session = OnboardingSession(user_id=1, word_bank=[])

    with patch(
        "bot.services.onboarding.generate_random_words",
        new_callable=AsyncMock,
        return_value=[],
    ):
        word = await get_next_word(session)

    assert word is None


def test_session_tracks_shown_words():
    session = create_session(telegram_id=222, user_id=2)
    session.word_bank = ["a", "b", "c"]
    # Clean up
    remove_session(222)
