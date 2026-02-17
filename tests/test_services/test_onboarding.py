from bot.services.onboarding import (
    OnboardingSession,
    create_session,
    get_next_word_with_options,
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


def test_get_next_word_with_options():
    session = OnboardingSession(user_id=1)

    result = get_next_word_with_options(session)
    assert result is not None
    assert "word" in result
    assert "correct" in result
    assert "options" in result
    assert len(result["options"]) == 4
    assert result["correct"] in result["options"]
    assert result["word"] in session.shown_words
    assert session.current_word == result["word"]


def test_get_next_word_options_shuffled():
    """Options should contain the correct answer among distractors."""
    session = OnboardingSession(user_id=1)

    result = get_next_word_with_options(session)
    assert result is not None
    assert result["correct_index"] == result["options"].index(result["correct"])


def test_session_tracks_shown_words():
    session = OnboardingSession(user_id=1)

    words = set()
    for _ in range(5):
        result = get_next_word_with_options(session)
        assert result is not None
        words.add(result["word"])

    assert len(words) == 5  # all unique
    assert len(session.shown_words) == 5
