import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from bot.config import settings
from bot.db.session import async_session
from bot.keyboards.quiz import quiz_keyboard
from bot.models.user import User
from bot.services.dictionary import get_word_count
from bot.services.quiz import generate_quiz

logger = logging.getLogger(__name__)


async def send_scheduled_quizzes(bot: Bot) -> None:
    """Send quizzes to all users who have enough words."""
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            try:
                count = await get_word_count(session, user.id)
                if count < 2:
                    continue

                for _ in range(settings.quiz_words_per_session):
                    quiz = await generate_quiz(session, user.id)
                    if quiz is None:
                        break
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=f"🧠 Как переводится <b>{quiz['word']}</b>?",
                        reply_markup=quiz_keyboard(quiz["word_id"], quiz["options"]),
                        parse_mode="HTML",
                    )
            except Exception:
                logger.exception("Failed to send quiz to user %s", user.telegram_id)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    for hour in settings.quiz_hours:
        scheduler.add_job(
            send_scheduled_quizzes,
            "cron",
            hour=hour,
            minute=0,
            args=[bot],
            id=f"quiz_{hour}",
            replace_existing=True,
        )

    return scheduler
