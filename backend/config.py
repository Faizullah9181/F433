"""
Configuration settings from environment variables.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://f433:f433@localhost:5432/f433"
    redis_url: str = "redis://localhost:6379"

    # ── Model selector: "google" | "unsloth" ─────────────────
    model: str = "google"  # which LLM backend to use

    # Google AI (Gemini via ADK)
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Unsloth Studio (uses LiteLLM → ADK bridge)
    # When running in Docker, set UNSLOTH_BASE_URL=http://host.docker.internal:8888
    # When running locally, default 127.0.0.1:8888 works
    unsloth_base_url: str = "http://127.0.0.1:8888"
    unsloth_username: str = "unsloth"
    unsloth_password: str = "12345678"
    unsloth_model: str = ""  # auto-detected from active model if empty

    # API-Football
    api_football_key: str = ""

    # Content generation
    auto_generate: bool = True
    generation_interval_minutes: int = 5  # Autonomous engine cycle interval

    @property
    def use_unsloth(self) -> bool:
        return self.model.lower().strip() == "unsloth"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
