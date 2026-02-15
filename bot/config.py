from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    gigachat_credentials: str
    database_url: str = "postgresql+asyncpg://localhost:5432/english_words_bot"

    # Quiz scheduler settings
    quiz_hours: list[int] = [10, 14, 19]  # Hours (UTC) to send quizzes
    quiz_words_per_session: int = 5


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
