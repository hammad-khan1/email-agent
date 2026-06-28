"""Application configuration loaded from .env file."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_SECRET_KEY: str = "changeme_secret"
    APP_ENV: str = "development"
    HR_USERNAME: str = "admin"
    HR_PASSWORD: str = "admin123"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/gmail/callback"
    DATABASE_URL: str = "sqlite:///./email_agent.db"
    DEFAULT_SENDER_NAME: str = "HR Team"
    MAX_EMAILS_PER_MINUTE: int = 10
    SCHEDULER_TIMEZONE: str = "Asia/Karachi"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
