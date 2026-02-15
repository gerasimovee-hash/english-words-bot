import os

# Set dummy env vars before any bot imports
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("GIGACHAT_CREDENTIALS", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from unittest.mock import AsyncMock, MagicMock, patch  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.models import Base  # noqa: E402


@pytest.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    async_sess = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_sess() as sess:
        yield sess


@pytest.fixture
def mock_gigachat():
    mock_message = MagicMock()
    mock_message.content = (
        '{"translation": "пример", '
        '"meanings": [{"meaning": "пример", "explanation": "образец"}], '
        '"examples": [{"en": "For example", "ru": "Например"}], '
        '"collocations": [{"en": "set an example", "ru": "подать пример"}]}'
    )
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = AsyncMock()
    mock_client.achat = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("bot.services.llm.GigaChat", return_value=mock_client) as mock:
        yield mock
