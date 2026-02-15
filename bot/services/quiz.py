import random

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.word import Word
from bot.services.dictionary import get_words_for_review


async def generate_quiz(session: AsyncSession, user_id: int) -> dict | None:
    """Generate a quiz question for the user.

    Returns dict with keys: word_id, word, correct_answer, options
    or None if user has fewer than 2 words.
    """
    words = await get_words_for_review(session, user_id, limit=1)
    if not words:
        return None

    target = words[0]

    # Get distractors from user's other words
    result = await session.execute(
        select(Word.translation)
        .where(Word.user_id == user_id, Word.id != target.id)
        .order_by(func.random())
        .limit(3)
    )
    distractors = [row[0] for row in result.all()]

    # If user doesn't have enough words for distractors, skip quiz
    if len(distractors) < 1:
        return None

    options = [target.translation] + distractors
    random.shuffle(options)

    return {
        "word_id": target.id,
        "word": target.word,
        "correct_answer": target.translation,
        "options": options,
    }
