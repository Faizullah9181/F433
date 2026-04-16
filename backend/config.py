"""
Configuration settings from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://footbot:footbot@localhost:5432/footbot"
    chaos_db_url: str = ""
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

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3035,http://localhost:5173,http://localhost:5035,https://faiz-ai.dev,https://www.faiz-ai.dev,https://api.faiz-ai.dev,https://f433.faiz-ai.dev"

    # Content generation
    auto_generate: bool = True
    generation_interval_minutes: int = 5  # Autonomous engine cycle interval

    # Agent profile moderation
    agent_llm_validation_enabled: bool = True

    @property
    def use_unsloth(self) -> bool:
        return self.model.lower().strip() == "unsloth"

    class Config:
        env_file = (".env", "../.env")
        extra = "ignore"


settings = Settings()
