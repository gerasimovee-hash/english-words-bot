import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from bot.config import settings
from bot.db.session import async_session
from bot.handlers.quiz import send_quiz_question
from bot.models.user import User
from bot.services.dictionary import get_word_count
from bot.services.quiz import create_session, remove_session

logger = logging.getLogger(__name__)


async def send_scheduled_quizzes(bot: Bot) -> None:
    """Send first quiz question to all users who have enough words.

    Users continue the quiz interactively by clicking "Next question".
    """
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            try:
                count = await get_word_count(session, user.id)
                if count < 2:
                    continue

                # Clean up any leftover session
                remove_session(user.telegram_id)
                create_session(
                    user.telegram_id, user.id, total_questions=settings.quiz_words_per_session
                )

                chat_id = user.telegram_id

                async def send_func(text, *, _chat_id=chat_id, **kwargs):
                    await bot.send_message(
                        chat_id=_chat_id, text=text, parse_mode="HTML", **kwargs
                    )

                sent = await send_quiz_question(session, user.telegram_id, send_func=send_func)
                if not sent:
                    remove_session(user.telegram_id)
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
