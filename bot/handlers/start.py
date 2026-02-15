from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
            "Просто отправь мне незнакомое слово или фразу на английском, "
            "и я объясню значение, покажу варианты перевода и примеры.\n\n"
            "Слова сохраняются в твой личный словарь, "
            "а я буду присылать тесты для закрепления.\n\n"
            "Команды:\n"
            "/words — твой словарь\n"
            "/stats — статистика\n"
            "/quiz — начать тест\n"
            "/help — помощь"
        )
    else:
        await message.answer(
            "С возвращением! Отправь мне слово на английском, и я помогу его выучить. 📚"
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
