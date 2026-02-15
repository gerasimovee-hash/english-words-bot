# English Words Bot

Telegram-бот для изучения английских слов. Пользователь отправляет незнакомое слово/фразу — бот объясняет значение, варианты перевода, устойчивые выражения (через OpenAI API), сохраняет в личный словарь и периодически присылает тесты для закрепления.

## Tech Stack

- **Язык:** Python 3.11+
- **Фреймворк бота:** aiogram 3.x (async)
- **LLM:** OpenAI API (GPT-4o-mini для объяснений, GPT-4o для сложных случаев)
- **БД:** PostgreSQL + asyncpg / SQLAlchemy 2.0 (async)
- **Миграции:** Alembic
- **Тесты:** pytest + pytest-asyncio
- **Деплой:** VPS (systemd / supervisor)
- **Конфиг:** pydantic-settings, переменные окружения через `.env`

## Project Structure

```
bot/
├── __init__.py
├── __main__.py          # Точка входа
├── config.py            # Настройки (pydantic-settings)
├── handlers/            # Хэндлеры aiogram (команды, сообщения)
│   ├── __init__.py
│   ├── start.py         # /start, /help
│   ├── word.py          # Обработка новых слов
│   ├── quiz.py          # Тесты/квизы
│   └── dictionary.py   # Просмотр словаря
├── services/            # Бизнес-логика
│   ├── __init__.py
│   ├── llm.py           # Взаимодействие с OpenAI API
│   ├── dictionary.py    # Работа со словарём пользователя
│   └── quiz.py          # Генерация и проверка тестов
├── models/              # SQLAlchemy модели
│   ├── __init__.py
│   ├── user.py
│   └── word.py
├── db/                  # Подключение к БД, сессии
│   ├── __init__.py
│   └── session.py
├── middlewares/         # Middleware aiogram
│   └── __init__.py
├── keyboards/           # Inline/Reply клавиатуры
│   └── __init__.py
├── scheduler/           # Планировщик тестов (APScheduler)
│   └── __init__.py
└── utils/               # Вспомогательные утилиты
    └── __init__.py
alembic/                 # Миграции Alembic
tests/                   # Тесты pytest
├── conftest.py
├── test_services/
└── test_handlers/
```

## Architecture Decisions

- **Async everywhere:** Весь код асинхронный (aiogram 3, asyncpg, httpx для OpenAI).
- **Слой сервисов:** Хэндлеры не содержат бизнес-логику — только вызывают сервисы.
- **Формат тестов:** Бот присылает слово + 4 варианта перевода (inline-кнопки). Правильный вариант и дистракторы генерируются из словаря пользователя или через LLM.
- **Планировщик:** APScheduler для отправки тестов несколько раз в день по расписанию.
- **Промпты LLM:** Хранятся в отдельных константах/файлах, не захардкожены в логике.

## Conventions

- Язык кода и комментариев: **английский**.
- Именование: snake_case для функций/переменных, PascalCase для классов.
- Типизация: использовать type hints везде.
- Форматирование: ruff (linter + formatter).
- Коммиты: conventional commits (feat:, fix:, refactor:, test:, docs:).
- Секреты (BOT_TOKEN, OPENAI_API_KEY, DATABASE_URL) только в `.env`, **никогда** не коммитить.

## Key Commands

```bash
# Запуск бота
python -m bot

# Тесты
pytest

# Линтер
ruff check .
ruff format .

# Миграции
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Environment Variables

```
BOT_TOKEN=           # Telegram Bot Token
OPENAI_API_KEY=      # OpenAI API Key
DATABASE_URL=        # postgresql+asyncpg://user:pass@host:port/dbname
```
