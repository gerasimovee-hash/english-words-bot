from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main import BTN_DICTIONARY, BTN_QUIZ, BTN_STATS, main_keyboard
from bot.keyboards.onboarding import onboarding_choice_keyboard
from bot.models.user import User

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    telegram_id = message.from_user.id  # type: ignore[union-attr]

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        await message.answer(
            "👋 Привет! Я помогу тебе учить английские слова.\n\n"
            "Слова сохраняются в твой личный словарь, "
            "а я буду присылать тесты для закрепления.\n\n"
            "Как хочешь начать?",
            reply_markup=onboarding_choice_keyboard(),
        )
    else:
        await message.answer(
            "С возвращением! Отправь мне слово на английском, и я помогу его выучить. 📚",
            reply_markup=main_keyboard(),
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Как пользоваться ботом:</b>\n\n"
        "1. Отправь незнакомое английское слово или фразу\n"
        "2. Я объясню значение и покажу перевод\n"
        "3. Сохрани слово в свой словарь\n"
        "4. Я буду присылать тесты для закрепления\n\n"
        "<b>Команды:</b>\n"
        "/words — твой словарь\n"
        "/stats — статистика изучения\n"
        "/quiz — начать тест прямо сейчас\n"
        "/help — эта справка"
    )


@router.message(F.text == BTN_DICTIONARY)
async def btn_dictionary(message: Message, session: AsyncSession) -> None:
    from bot.handlers.dictionary import cmd_words

    await cmd_words(message, session)


@router.message(F.text == BTN_QUIZ)
async def btn_quiz(message: Message, session: AsyncSession) -> None:
    from bot.handlers.quiz import cmd_quiz

    await cmd_quiz(message, session)


@router.message(F.text == BTN_STATS)
async def btn_stats(message: Message, session: AsyncSession) -> None:
    from bot.handlers.dictionary import cmd_stats

    await cmd_stats(message, session)
