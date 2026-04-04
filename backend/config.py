"""
Configuration settings from environment variables.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://f433:f433@localhost:5432/f433"
    redis_url: str = "redis://localhost:6379"

    # Google AI
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # API-Football
    api_football_key: str = ""

    # Content generation
    auto_generate: bool = True
    generation_interval_minutes: int = 5  # Autonomous engine cycle interval

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
