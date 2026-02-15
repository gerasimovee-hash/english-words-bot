from bot.services.dictionary import (
    add_word,
    delete_word,
    get_or_create_user,
    get_stats,
    get_word_count,
    get_words,
    get_words_for_review,
    update_word_review,
)


async def test_get_or_create_user(session):
    user = await get_or_create_user(session, telegram_id=12345)
    assert user.telegram_id == 12345
    assert user.id is not None

    # Should return existing user
    same_user = await get_or_create_user(session, telegram_id=12345)
    assert same_user.id == user.id


async def test_add_and_get_words(session):
    user = await get_or_create_user(session, telegram_id=111)

    await add_word(session, user.id, "hello", "привет", "greeting")
    await add_word(session, user.id, "world", "мир", "the earth")

    words = await get_words(session, user.id)
    assert len(words) == 2

    count = await get_word_count(session, user.id)
    assert count == 2


async def test_delete_word(session):
    user = await get_or_create_user(session, telegram_id=222)
    word = await add_word(session, user.id, "test", "тест", "")

    deleted = await delete_word(session, word.id, user.id)
    assert deleted is True

    count = await get_word_count(session, user.id)
    assert count == 0


async def test_delete_word_wrong_user(session):
    user1 = await get_or_create_user(session, telegram_id=333)
    user2 = await get_or_create_user(session, telegram_id=444)
    word = await add_word(session, user1.id, "secret", "секрет", "")

    deleted = await delete_word(session, word.id, user2.id)
    assert deleted is False


async def test_update_word_review(session):
    user = await get_or_create_user(session, telegram_id=555)
    word = await add_word(session, user.id, "apple", "яблоко", "")

    await update_word_review(session, word.id, is_correct=True)
    await session.refresh(word)

    assert word.review_count == 1
    assert word.correct_count == 1
    assert word.last_reviewed_at is not None


async def test_get_words_for_review(session):
    user = await get_or_create_user(session, telegram_id=666)
    await add_word(session, user.id, "cat", "кот", "")
    await add_word(session, user.id, "dog", "собака", "")

    words = await get_words_for_review(session, user.id, limit=5)
    assert len(words) == 2


async def test_get_stats(session):
    user = await get_or_create_user(session, telegram_id=777)
    word = await add_word(session, user.id, "sun", "солнце", "")
    await update_word_review(session, word.id, is_correct=True)
    await update_word_review(session, word.id, is_correct=False)

    stats = await get_stats(session, user.id)
    assert stats["total_words"] == 1
    assert stats["total_reviews"] == 2
    assert stats["total_correct"] == 1
    assert stats["accuracy"] == 50.0
