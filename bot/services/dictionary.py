from datetime import UTC, datetime

from sqlalchemy import func, select
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
) -> Word:
    db_word = Word(
        user_id=user_id,
        word=word,
        translation=translation,
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


async def get_words_for_review(session: AsyncSession, user_id: int, limit: int = 5) -> list[Word]:
    """Get words that need review, prioritizing least reviewed and oldest."""
    result = await session.execute(
        select(Word)
        .where(Word.user_id == user_id)
        .order_by(
            Word.last_reviewed_at.asc().nulls_first(),
            Word.correct_count.asc(),
            Word.created_at.asc(),
        )
        .limit(limit)
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

    return {
        "total_words": total,
        "total_reviews": total_reviews,
        "total_correct": total_correct,
        "accuracy": round(total_correct / total_reviews * 100, 1) if total_reviews > 0 else 0,
    }
