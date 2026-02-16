import random
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.word import Word
from bot.services.dictionary import get_words_for_review

POINTS_CORRECT = 10
POINTS_STREAK_BONUS = 5
STREAK_THRESHOLD = 3


@dataclass
class QuizSession:
    user_id: int
    total_questions: int = 5
    current_question: int = 0
    correct_count: int = 0
    score: int = 0
    streak: int = 0
    asked_word_ids: list[int] = field(default_factory=list)


# In-memory quiz sessions: telegram_id -> QuizSession
_quiz_sessions: dict[int, QuizSession] = {}


def get_session(telegram_id: int) -> QuizSession | None:
    return _quiz_sessions.get(telegram_id)


def create_session(telegram_id: int, user_id: int, total_questions: int = 5) -> QuizSession:
    session = QuizSession(user_id=user_id, total_questions=total_questions)
    _quiz_sessions[telegram_id] = session
    return session


def remove_session(telegram_id: int) -> QuizSession | None:
    return _quiz_sessions.pop(telegram_id, None)


def calculate_points(streak: int) -> int:
    """Calculate points for a correct answer, including streak bonus."""
    points = POINTS_CORRECT
    if streak >= STREAK_THRESHOLD:
        points += POINTS_STREAK_BONUS * (streak - STREAK_THRESHOLD + 1)
    return points


async def generate_quiz(
    session: AsyncSession,
    user_id: int,
    exclude_word_ids: list[int] | None = None,
) -> dict | None:
    """Generate a quiz question for the user.

    Returns dict with keys: word_id, word, correct_answer, all_correct, options
    or None if user has fewer than 2 words.
    """
    words = await get_words_for_review(
        session, user_id, limit=1, exclude_word_ids=exclude_word_ids
    )
    if not words:
        return None

    target = words[0]

    # Pick a random translation for the correct answer display
    all_translations = target.translations or [target.translation]
    correct_answer = random.choice(all_translations)

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

    options = [correct_answer] + distractors
    random.shuffle(options)

    return {
        "word_id": target.id,
        "word": target.word,
        "correct_answer": correct_answer,
        "all_correct": all_translations,
        "options": options,
    }
