import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main import BUTTON_TEXTS
from bot.keyboards.word import correction_keyboard, save_word_keyboard
from bot.services.dictionary import add_word, get_or_create_user
from bot.services.llm import explain_word

logger = logging.getLogger(__name__)

router = Router()

# Temporary storage for pending explanations (user_id -> explanation)
_pending: dict[int, dict] = {}


@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(BUTTON_TEXTS))
async def handle_word(message: Message, session: AsyncSession) -> None:
    word = message.text.strip()  # type: ignore[union-attr]
    if not word or len(word) > 200:
        await message.answer("Отправь слово или короткую фразу на английском (до 200 символов).")
        return

    telegram_id = message.from_user.id  # type: ignore[union-attr]
    await message.answer("🔍 Ищу информацию...")

    try:
        explanation = await explain_word(word)
    except Exception:
        logger.exception("Failed to explain word: %s", word)
        await message.answer("Не удалось получить объяснение. Попробуй ещё раз позже.")
        return

    _pending[telegram_id] = {
        "word": explanation.corrected_word or word,
        "original_word": word,
        "translation": explanation.translation,
        "translations": explanation.translations,
        "explanation": explanation.raw_text,
    }

    # If spell-check detected a correction, ask user first
    if explanation.corrected_word:
        await message.answer(
            f"Возможно, вы имели в виду <b>{explanation.corrected_word}</b>?",
            reply_markup=correction_keyboard(explanation.corrected_word, word),
        )
        return

    await message.answer(explanation.raw_text, reply_markup=save_word_keyboard(word))


@router.callback_query(F.data.startswith("correct_yes:"))
async def accept_correction(callback: CallbackQuery) -> None:
    """User accepts the spelling correction."""
    telegram_id = callback.from_user.id
    pending = _pending.get(telegram_id)
    if pending is None:
        await callback.answer("Устарело.", show_alert=True)
        return

    # Word is already set to corrected version in _pending
    await callback.message.edit_text(  # type: ignore[union-attr]
        pending["explanation"],
        reply_markup=save_word_keyboard(pending["word"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("correct_no:"))
async def reject_correction(callback: CallbackQuery) -> None:
    """User rejects correction, keeps original word."""
    telegram_id = callback.from_user.id
    pending = _pending.get(telegram_id)
    if pending is None:
        await callback.answer("Устарело.", show_alert=True)
        return

    # Revert to original word
    pending["word"] = pending["original_word"]
    await callback.message.edit_text(  # type: ignore[union-attr]
        pending["explanation"],
        reply_markup=save_word_keyboard(pending["original_word"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("save:"))
async def save_word_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    telegram_id = callback.from_user.id
    pending = _pending.pop(telegram_id, None)

    if pending is None:
        await callback.answer("Слово уже сохранено или устарело.", show_alert=True)
        return

    user = await get_or_create_user(session, telegram_id)
    await add_word(
        session=session,
        user_id=user.id,
        word=pending["word"],
        translation=pending["translation"],
        explanation=pending["explanation"],
        translations=pending.get("translations"),
    )

    await callback.answer("Слово сохранено! ✅")
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]


@router.callback_query(F.data == "skip")
async def skip_word_callback(callback: CallbackQuery) -> None:
    _pending.pop(callback.from_user.id, None)
    await callback.answer("Окей, пропускаем.")
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
