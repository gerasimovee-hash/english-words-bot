from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User
from bot.models.word import Word


async def get_or_create_user(session: AsyncSession, telegram_id: int) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def add_word(
    session: AsyncSession,
    user_id: int,
    word: str,
    translation: str,
    explanation: str,
    translations: list[str] | None = None,
) -> Word:
    db_word = Word(
        user_id=user_id,
        word=word,
        translation=translation,
        translations=translations or [translation],
        explanation=explanation,
    )
    session.add(db_word)
    await session.commit()
    await session.refresh(db_word)
    return db_word


async def get_words(
    session: AsyncSession, user_id: int, limit: int = 20, offset: int = 0
) -> list[Word]:
    result = await session.execute(
        select(Word)
        .where(Word.user_id == user_id)
        .order_by(Word.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_word_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(func.count(Word.id)).where(Word.user_id == user_id))
    return result.scalar_one()


async def delete_word(session: AsyncSession, word_id: int, user_id: int) -> bool:
    result = await session.execute(select(Word).where(Word.id == word_id, Word.user_id == user_id))
    word = result.scalar_one_or_none()
    if word is None:
        return False
    await session.delete(word)
    await session.commit()
    return True


async def word_exists(session: AsyncSession, user_id: int, word: str) -> bool:
    """Check if a word already exists in the user's dictionary (case-insensitive)."""
    result = await session.execute(
        select(Word.id).where(
            Word.user_id == user_id,
            func.lower(Word.word) == word.lower(),
        )
    )
    return result.scalar_one_or_none() is not None


async def get_words_for_review(
    session: AsyncSession,
    user_id: int,
    limit: int = 5,
    exclude_word_ids: list[int] | None = None,
) -> list[Word]:
    """Get words that need review, prioritizing low accuracy and least reviewed.

    Priority order:
    1. Never reviewed words first (last_reviewed_at IS NULL)
    2. Low accuracy words (correct_count / review_count ASC)
    3. Oldest reviewed words
    4. Random tie-breaking
    """
    safe_review_count = case((Word.review_count > 0, Word.review_count), else_=1)
    accuracy = Word.correct_count * 1.0 / safe_review_count
    query = select(Word).where(Word.user_id == user_id)
    if exclude_word_ids:
        query = query.where(Word.id.notin_(exclude_word_ids))
    result = await session.execute(
        query.order_by(
            Word.last_reviewed_at.asc().nulls_first(),
            accuracy.asc(),
            Word.last_reviewed_at.asc(),
            func.random(),
        ).limit(limit)
    )
    return list(result.scalars().all())


async def update_word_review(session: AsyncSession, word_id: int, is_correct: bool) -> None:
    result = await session.execute(select(Word).where(Word.id == word_id))
    word = result.scalar_one_or_none()
    if word is None:
        return
    word.review_count += 1
    if is_correct:
        word.correct_count += 1
    word.last_reviewed_at = datetime.now(UTC)
    await session.commit()


async def update_user_score(session: AsyncSession, user_id: int, points: int) -> int:
    """Add points to user's score. Returns new total score."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return 0
    user.score += points
    await session.commit()
    return user.score


async def get_stats(session: AsyncSession, user_id: int) -> dict:
    total = await get_word_count(session, user_id)

    result = await session.execute(
        select(
            func.coalesce(func.sum(Word.review_count), 0),
            func.coalesce(func.sum(Word.correct_count), 0),
        ).where(Word.user_id == user_id)
    )
    row = result.one()
    total_reviews = row[0]
    total_correct = row[1]

    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    score = user.score if user else 0

    return {
        "total_words": total,
        "total_reviews": total_reviews,
        "total_correct": total_correct,
        "accuracy": round(total_correct / total_reviews * 100, 1) if total_reviews > 0 else 0,
        "score": score,
    }
