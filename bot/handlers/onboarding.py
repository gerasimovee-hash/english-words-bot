import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main import main_keyboard
from bot.keyboards.onboarding import (
    onboarding_next_keyboard,
    word_check_keyboard,
)
from bot.services.dictionary import add_word, get_or_create_user
from bot.services.llm import explain_word
from bot.services.onboarding import (
    create_session,
    get_next_word,
    get_session,
    remove_session,
)

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "onboard_self")
async def on_self_add(callback: CallbackQuery) -> None:
    await callback.message.edit_text(  # type: ignore[union-attr]
        "Отлично! Просто отправь мне незнакомое английское слово или фразу, "
        "и я объясню значение и сохраню в твой словарь."
    )
    await callback.message.answer(  # type: ignore[union-attr]
        "Используй кнопки внизу для навигации 👇",
        reply_markup=main_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "onboard_test")
async def on_test_start(callback: CallbackQuery, session: AsyncSession) -> None:
    telegram_id = callback.from_user.id
    user = await get_or_create_user(session, telegram_id)

    ob_session = create_session(telegram_id, user.id)
    word = await get_next_word(ob_session)

    if not word:
        await callback.message.edit_text(  # type: ignore[union-attr]
            "Не удалось загрузить слова. Попробуй позже или отправь слово сам."
        )
        remove_session(telegram_id)
        await callback.answer()
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Знаешь ли ты слово <b>{word}</b>?",
        reply_markup=word_check_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "onboard_know")
async def on_know(callback: CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    ob_session = get_session(telegram_id)

    if not ob_session:
        await callback.answer("Сессия не найдена. Начни заново с /start.")
        return

    word = await get_next_word(ob_session)
    if not word:
        await callback.message.edit_text(  # type: ignore[union-attr]
            "Слова закончились! Ты знаешь все предложенные слова. "
            "Попробуй отправить незнакомое слово сам."
        )
        remove_session(telegram_id)
        await callback.answer()
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Знаешь ли ты слово <b>{word}</b>?",
        reply_markup=word_check_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "onboard_dont_know")
async def on_dont_know(callback: CallbackQuery, session: AsyncSession) -> None:
    telegram_id = callback.from_user.id
    ob_session = get_session(telegram_id)

    if not ob_session or not ob_session.current_word:
        await callback.answer("Сессия не найдена. Начни заново с /start.")
        return

    word = ob_session.current_word

    try:
        explanation = await explain_word(word)
    except Exception:
        logger.exception("Failed to explain word during onboarding: %s", word)
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"Не удалось объяснить слово <b>{word}</b>. Пропускаем.",
            reply_markup=onboarding_next_keyboard(),
        )
        await callback.answer()
        return

    display_word = explanation.corrected_word or word
    await add_word(
        session=session,
        user_id=ob_session.user_id,
        word=display_word,
        translation=explanation.translation,
        explanation=explanation.raw_text,
        translations=explanation.translations,
    )

    ob_session.unknown_count += 1
    remaining = ob_session.target_unknown - ob_session.unknown_count

    if ob_session.unknown_count >= ob_session.target_unknown:
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"<b>{display_word}</b> — {explanation.translation}\n"
            f"Сохранено! ({ob_session.unknown_count}/{ob_session.target_unknown})\n\n"
            f"🎉 Отлично! Собрано {ob_session.target_unknown} слов в твой словарь. "
            "Теперь я буду присылать квизы для закрепления!"
        )
        await callback.message.answer(  # type: ignore[union-attr]
            "Используй кнопки внизу для навигации 👇",
            reply_markup=main_keyboard(),
        )
        remove_session(telegram_id)
    else:
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"<b>{display_word}</b> — {explanation.translation}\n"
            f"Сохранено! ({ob_session.unknown_count}/{ob_session.target_unknown})\n\n"
            f"Осталось найти ещё {remaining} незнакомых слов.",
            reply_markup=onboarding_next_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data == "onboard_next")
async def on_next(callback: CallbackQuery) -> None:
    telegram_id = callback.from_user.id
    ob_session = get_session(telegram_id)

    if not ob_session:
        await callback.answer("Сессия не найдена. Начни заново с /start.")
        return

    word = await get_next_word(ob_session)
    if not word:
        await callback.message.edit_text(  # type: ignore[union-attr]
            "Слова закончились! Попробуй отправить незнакомое слово сам."
        )
        remove_session(telegram_id)
        await callback.answer()
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Знаешь ли ты слово <b>{word}</b>?",
        reply_markup=word_check_keyboard(),
    )
    await callback.answer()
