import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main import main_keyboard
from bot.keyboards.onboarding import (
    onboarding_next_keyboard,
    onboarding_quiz_keyboard,
)
from bot.services.dictionary import add_word, get_or_create_user
from bot.services.onboarding import (
    create_session,
    get_next_word,
    get_session,
    get_word_with_options,
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


async def _show_quiz(callback: CallbackQuery, ob_session) -> None:  # noqa: ANN001
    """Helper to show a quiz question for the current word."""
    quiz_data = await get_word_with_options(ob_session)

    if not quiz_data:
        await callback.message.edit_text(  # type: ignore[union-attr]
            f"Не удалось подготовить вопрос для слова "
            f"<b>{ob_session.current_word}</b>. Пропускаем.",
            reply_markup=onboarding_next_keyboard(),
        )
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Как переводится <b>{quiz_data['word']}</b>?",
        reply_markup=onboarding_quiz_keyboard(quiz_data["options"]),
    )


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

    await _show_quiz(callback, ob_session)
    await callback.answer()


@router.callback_query(F.data.startswith("ob_answer:"))
async def on_quiz_answer(callback: CallbackQuery, session: AsyncSession) -> None:
    telegram_id = callback.from_user.id
    ob_session = get_session(telegram_id)

    if not ob_session or not ob_session.current_word:
        await callback.answer("Сессия не найдена. Начни заново с /start.")
        return

    answer_index = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    is_correct = answer_index == ob_session.correct_index

    if is_correct:
        # User knows this word — move to next
        word = await get_next_word(ob_session)
        if not word:
            await callback.message.edit_text(  # type: ignore[union-attr]
                "✅ Верно!\n\n"
                "Слова закончились! Ты знаешь все предложенные слова. "
                "Попробуй отправить незнакомое слово сам."
            )
            await callback.message.answer(  # type: ignore[union-attr]
                "Используй кнопки внизу для навигации 👇",
                reply_markup=main_keyboard(),
            )
            remove_session(telegram_id)
            await callback.answer()
            return

        await callback.message.edit_text(  # type: ignore[union-attr]
            "✅ Верно! Значит ты знаешь это слово.",
        )
        # Show next quiz question as a new message
        await callback.message.answer(  # type: ignore[union-attr]
            f"Как переводится <b>{word}</b>?",
        )
        quiz_data = await get_word_with_options(ob_session)
        if quiz_data:
            await callback.message.answer(  # type: ignore[union-attr]
                f"Как переводится <b>{quiz_data['word']}</b>?",
                reply_markup=onboarding_quiz_keyboard(quiz_data["options"]),
            )
        else:
            await callback.message.answer(  # type: ignore[union-attr]
                f"Не удалось подготовить вопрос для <b>{word}</b>.",
                reply_markup=onboarding_next_keyboard(),
            )
    else:
        # User doesn't know — save word and show explanation
        explanation = ob_session.current_explanation
        if not explanation:
            await callback.answer("Ошибка. Попробуй ещё раз.")
            return

        display_word = explanation.corrected_word or ob_session.current_word
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

        correct_answer = ob_session.current_options[ob_session.correct_index]

        if ob_session.unknown_count >= ob_session.target_unknown:
            await callback.message.edit_text(  # type: ignore[union-attr]
                f"❌ Правильный ответ: <b>{correct_answer}</b>\n\n"
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
                f"❌ Правильный ответ: <b>{correct_answer}</b>\n\n"
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
        await callback.message.answer(  # type: ignore[union-attr]
            "Используй кнопки внизу для навигации 👇",
            reply_markup=main_keyboard(),
        )
        remove_session(telegram_id)
        await callback.answer()
        return

    await _show_quiz(callback, ob_session)
    await callback.answer()
