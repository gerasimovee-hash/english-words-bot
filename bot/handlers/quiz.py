import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.quiz import next_question_keyboard, quiz_keyboard
from bot.models.word import Word
from bot.services.dictionary import get_or_create_user, update_user_score, update_word_review
from bot.services.quiz import (
    calculate_points,
    create_session,
    generate_quiz,
    get_session,
    remove_session,
)

logger = logging.getLogger(__name__)

router = Router()


def _question_text(word: str, current: int, total: int) -> str:
    return f"🧠 Вопрос {current}/{total}\n\nКак переводится <b>{word}</b>?"


def _result_summary(correct: int, total: int, score: int) -> str:
    return (
        f"🏁 <b>Квиз завершён!</b>\n\n"
        f"Правильных ответов: {correct}/{total}\n"
        f"Заработано очков: +{score}"
    )


async def send_quiz_question(
    session: AsyncSession,
    telegram_id: int,
    edit_message=None,
    send_func=None,
) -> bool:
    """Generate and send/edit a quiz question. Returns True if sent."""
    quiz_session = get_session(telegram_id)
    if quiz_session is None:
        return False

    quiz = await generate_quiz(
        session, quiz_session.user_id, exclude_word_ids=quiz_session.asked_word_ids
    )
    if quiz is None:
        # No more words available — finish early
        total_score = quiz_session.score
        correct = quiz_session.correct_count
        total = quiz_session.current_question
        remove_session(telegram_id)
        text = _result_summary(correct, total, total_score)
        if edit_message:
            await edit_message.edit_text(text)
        elif send_func:
            await send_func(text)
        return False

    quiz_session.current_question += 1
    quiz_session.asked_word_ids.append(quiz["word_id"])

    text = _question_text(
        quiz["word"], quiz_session.current_question, quiz_session.total_questions
    )
    keyboard = quiz_keyboard(quiz["word_id"], quiz["options"])

    if edit_message:
        await edit_message.edit_text(text, reply_markup=keyboard)
    elif send_func:
        await send_func(text, reply_markup=keyboard)

    return True


@router.message(Command("quiz"))
async def cmd_quiz(message: Message, session: AsyncSession) -> None:
    telegram_id = message.from_user.id  # type: ignore[union-attr]
    user = await get_or_create_user(session, telegram_id)

    # Remove any existing session
    remove_session(telegram_id)
    create_session(telegram_id, user.id, total_questions=5)

    sent = await send_quiz_question(session, telegram_id, send_func=message.answer)
    if not sent:
        remove_session(telegram_id)
        await message.answer(
            "В твоём словаре пока мало слов для теста. Добавь хотя бы 2 слова, отправив их мне."
        )


@router.callback_query(F.data.startswith("quiz:"))
async def handle_quiz_answer(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":")  # type: ignore[union-attr]
    if len(parts) != 3:
        await callback.answer("Ошибка данных.")
        return

    word_id = int(parts[1])
    chosen_idx = int(parts[2])

    telegram_id = callback.from_user.id
    quiz_session = get_session(telegram_id)

    # Get the options from the keyboard
    keyboard = callback.message.reply_markup  # type: ignore[union-attr]
    if keyboard is None:
        await callback.answer("Тест уже завершён.")
        return

    options = [row[0].text for row in keyboard.inline_keyboard]
    chosen_answer = options[chosen_idx]

    # Get the correct answer from the word
    result = await session.execute(select(Word).where(Word.id == word_id))
    word = result.scalar_one_or_none()

    if word is None:
        await callback.answer("Слово не найдено.")
        return

    # Check against all translations
    all_correct = word.translations or [word.translation]
    is_correct = chosen_answer in all_correct
    await update_word_review(session, word_id, is_correct)

    points_earned = 0
    if quiz_session:
        if is_correct:
            quiz_session.streak += 1
            points_earned = calculate_points(quiz_session.streak)
            quiz_session.score += points_earned
            quiz_session.correct_count += 1
            user = await get_or_create_user(session, telegram_id)
            await update_user_score(session, user.id, points_earned)
        else:
            quiz_session.streak = 0

    points_text = f"\n+{points_earned} очков!" if points_earned > 0 else ""

    if is_correct:
        text = f"✅ Правильно! <b>{word.word}</b> — {word.translation}{points_text}"
    else:
        text = (
            f"❌ Неправильно. <b>{word.word}</b> — {word.translation}\nТы выбрал: {chosen_answer}"
        )

    # Check if quiz continues
    is_last = not quiz_session or quiz_session.current_question >= quiz_session.total_questions
    if is_last and quiz_session:
        total_score = quiz_session.score
        correct = quiz_session.correct_count
        total = quiz_session.total_questions
        remove_session(telegram_id)
        text += f"\n\n{_result_summary(correct, total, total_score)}"
        await callback.message.edit_text(text, reply_markup=None)  # type: ignore[union-attr]
    elif quiz_session:
        await callback.message.edit_text(  # type: ignore[union-attr]
            text, reply_markup=next_question_keyboard()
        )
    else:
        # No session (old-style single quiz or expired)
        await callback.message.edit_text(text, reply_markup=None)  # type: ignore[union-attr]

    await callback.answer()


@router.callback_query(F.data == "quiz_next")
async def handle_next_question(callback: CallbackQuery, session: AsyncSession) -> None:
    telegram_id = callback.from_user.id
    quiz_session = get_session(telegram_id)

    if quiz_session is None:
        await callback.answer("Квиз уже завершён.")
        await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
        return

    await send_quiz_question(
        session,
        telegram_id,
        edit_message=callback.message,  # type: ignore[arg-type]
    )
    await callback.answer()
