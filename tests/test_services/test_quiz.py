from bot.services.dictionary import add_word, get_or_create_user
from bot.services.quiz import (
    calculate_points,
    create_session,
    generate_quiz,
    get_session,
    remove_session,
)


async def test_generate_quiz_not_enough_words(session):
    user = await get_or_create_user(session, telegram_id=1001)
    await add_word(session, user.id, "lonely", "одинокий", "")

    quiz = await generate_quiz(session, user.id)
    assert quiz is None  # Need at least 2 words


async def test_generate_quiz(session):
    user = await get_or_create_user(session, telegram_id=1002)
    await add_word(session, user.id, "red", "красный", "")
    await add_word(session, user.id, "blue", "синий", "")
    await add_word(session, user.id, "green", "зелёный", "")

    quiz = await generate_quiz(session, user.id)
    assert quiz is not None
    assert "word" in quiz
    assert "correct_answer" in quiz
    assert "all_correct" in quiz
    assert "options" in quiz
    assert quiz["correct_answer"] in quiz["options"]
    assert len(quiz["options"]) >= 2


async def test_generate_quiz_empty_dictionary(session):
    user = await get_or_create_user(session, telegram_id=1003)
    quiz = await generate_quiz(session, user.id)
    assert quiz is None


async def test_generate_quiz_with_exclude(session):
    user = await get_or_create_user(session, telegram_id=1004)
    w1 = await add_word(session, user.id, "cat", "кот", "")
    w2 = await add_word(session, user.id, "dog", "собака", "")
    await add_word(session, user.id, "bird", "птица", "")

    quiz = await generate_quiz(session, user.id, exclude_word_ids=[w1.id, w2.id])
    assert quiz is not None
    assert quiz["word"] == "bird"


async def test_generate_quiz_random_translation(session):
    user = await get_or_create_user(session, telegram_id=1005)
    await add_word(
        session, user.id, "run", "бежать", "", translations=["бежать", "бегать", "работать"]
    )
    await add_word(session, user.id, "walk", "ходить", "")

    quiz = await generate_quiz(session, user.id)
    if quiz and quiz["word"] == "run":
        assert quiz["correct_answer"] in ["бежать", "бегать", "работать"]
        assert quiz["all_correct"] == ["бежать", "бегать", "работать"]


def test_quiz_session_lifecycle():
    telegram_id = 9999

    assert get_session(telegram_id) is None

    qs = create_session(telegram_id, user_id=1, total_questions=5)
    assert qs.total_questions == 5
    assert qs.current_question == 0
    assert qs.score == 0

    assert get_session(telegram_id) is qs

    removed = remove_session(telegram_id)
    assert removed is qs
    assert get_session(telegram_id) is None


def test_calculate_points():
    # Normal correct answer (streak < 3)
    assert calculate_points(1) == 10
    assert calculate_points(2) == 10

    # Streak bonus starts at 3
    assert calculate_points(3) == 15  # 10 + 5*1
    assert calculate_points(4) == 20  # 10 + 5*2
    assert calculate_points(5) == 25  # 10 + 5*3
