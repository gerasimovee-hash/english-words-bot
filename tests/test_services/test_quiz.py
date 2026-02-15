from bot.services.dictionary import add_word, get_or_create_user
from bot.services.quiz import generate_quiz


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
    assert "options" in quiz
    assert quiz["correct_answer"] in quiz["options"]
    assert len(quiz["options"]) >= 2


async def test_generate_quiz_empty_dictionary(session):
    user = await get_or_create_user(session, telegram_id=1003)
    quiz = await generate_quiz(session, user.id)
    assert quiz is None
