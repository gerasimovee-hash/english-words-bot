import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.quiz import quiz_keyboard
from bot.services.dictionary import get_or_create_user, update_word_review
from bot.services.quiz import generate_quiz

logger = logging.getLogger(__name__)

router = Router()


async def send_quiz(
    session: AsyncSession,
    user_id: int,
    send_func,
) -> bool:
    """Generate and send a quiz. Returns True if quiz was sent."""
    quiz = await generate_quiz(session, user_id)
    if quiz is None:
        return False

    await send_func(
        f"🧠 Как переводится <b>{quiz['word']}</b>?",
        reply_markup=quiz_keyboard(quiz["word_id"], quiz["options"]),
    )
    return True


@router.message(Command("quiz"))
async def cmd_quiz(message: Message, session: AsyncSession) -> None:
    telegram_id = message.from_user.id  # type: ignore[union-attr]
    user = await get_or_create_user(session, telegram_id)

    sent = await send_quiz(session, user.id, message.answer)
    if not sent:
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

    # Get the options from the keyboard
    keyboard = callback.message.reply_markup  # type: ignore[union-attr]
    if keyboard is None:
        await callback.answer("Тест уже завершён.")
        return

    options = [row[0].text for row in keyboard.inline_keyboard]
    chosen_answer = options[chosen_idx]

    # Get the correct answer from the word
    from sqlalchemy import select

    from bot.models.word import Word

    result = await session.execute(select(Word).where(Word.id == word_id))
    word = result.scalar_one_or_none()

    if word is None:
        await callback.answer("Слово не найдено.")
        return

    is_correct = chosen_answer == word.translation
    await update_word_review(session, word_id, is_correct)

    if is_correct:
        text = f"✅ Правильно! <b>{word.word}</b> — {word.translation}"
    else:
        text = (
            f"❌ Неправильно. <b>{word.word}</b> — {word.translation}\nТы выбрал: {chosen_answer}"
        )

    await callback.message.edit_text(text, reply_markup=None)  # type: ignore[union-attr]
    await callback.answer()
