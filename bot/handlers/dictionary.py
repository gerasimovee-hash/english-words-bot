from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.dictionary import delete_word, get_or_create_user, get_stats, get_words

router = Router()

WORDS_PER_PAGE = 10


def words_page_keyboard(words, page: int, has_next: bool) -> InlineKeyboardMarkup:
    buttons = []
    for w in words:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ {w.word} — {w.translation}",
                    callback_data=f"delword:{w.id}",
                )
            ]
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"words_page:{page - 1}"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"words_page:{page + 1}"))
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("words"))
async def cmd_words(message: Message, session: AsyncSession) -> None:
    telegram_id = message.from_user.id  # type: ignore[union-attr]
    user = await get_or_create_user(session, telegram_id)
    await show_words_page(message.answer, session, user.id, page=0)


async def show_words_page(send_func, session: AsyncSession, user_id: int, page: int) -> None:
    offset = page * WORDS_PER_PAGE
    words = await get_words(session, user_id, limit=WORDS_PER_PAGE + 1, offset=offset)

    has_next = len(words) > WORDS_PER_PAGE
    words = words[:WORDS_PER_PAGE]

    if not words and page == 0:
        await send_func("Твой словарь пуст. Отправь мне слово на английском, чтобы начать!")
        return

    await send_func(
        f"📚 <b>Твой словарь</b> (стр. {page + 1}):\n\nНажми на слово, чтобы удалить.",
        reply_markup=words_page_keyboard(words, page, has_next),
    )


@router.callback_query(F.data.startswith("words_page:"))
async def handle_words_page(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    telegram_id = callback.from_user.id
    user = await get_or_create_user(session, telegram_id)

    offset = page * WORDS_PER_PAGE
    words = await get_words(session, user.id, limit=WORDS_PER_PAGE + 1, offset=offset)
    has_next = len(words) > WORDS_PER_PAGE
    words = words[:WORDS_PER_PAGE]

    if not words:
        await callback.answer("Нет больше слов.")
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"📚 <b>Твой словарь</b> (стр. {page + 1}):\n\nНажми на слово, чтобы удалить.",
        reply_markup=words_page_keyboard(words, page, has_next),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delword:"))
async def handle_delete_word(callback: CallbackQuery, session: AsyncSession) -> None:
    word_id = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    telegram_id = callback.from_user.id
    user = await get_or_create_user(session, telegram_id)

    deleted = await delete_word(session, word_id, user.id)
    if deleted:
        await callback.answer("Слово удалено.")
    else:
        await callback.answer("Слово не найдено.")

    # Refresh the list
    words = await get_words(session, user.id, limit=WORDS_PER_PAGE + 1)
    has_next = len(words) > WORDS_PER_PAGE
    words = words[:WORDS_PER_PAGE]

    if not words:
        await callback.message.edit_text("Твой словарь пуст.")  # type: ignore[union-attr]
    else:
        await callback.message.edit_text(  # type: ignore[union-attr]
            "📚 <b>Твой словарь</b> (стр. 1):\n\nНажми на слово, чтобы удалить.",
            reply_markup=words_page_keyboard(words, 0, has_next),
        )


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession) -> None:
    telegram_id = message.from_user.id  # type: ignore[union-attr]
    user = await get_or_create_user(session, telegram_id)
    stats = await get_stats(session, user.id)

    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"Слов в словаре: {stats['total_words']}\n"
        f"Всего повторений: {stats['total_reviews']}\n"
        f"Правильных ответов: {stats['total_correct']}\n"
        f"Точность: {stats['accuracy']}%"
    )
