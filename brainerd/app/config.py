"""Central configuration — reads from environment / .env file."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ollama
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "mistral:7b"

    # Google AI (optional)
    google_ai_api_key: str = ""
    google_ai_model: str = "gemini-2.0-flash"

    # Routing
    ai_provider: str = "auto"  # ollama | google | auto

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_secret_key: str = "change-me-in-production-32chars+"

    # Database
    database_url: str = "sqlite+aiosqlite:////data/brainerd.db"

    # CORS
    allowed_origins: str = "*"

    # RPG
    rpg_max_history: int = 50
    rpg_default_world: str = "fantasy"

    # Logging
    log_level: str = "INFO"

    @property
    def google_enabled(self) -> bool:
        return bool(self.google_ai_api_key)

    @property
    def use_google(self) -> bool:
        if self.ai_provider == "google" and self.google_enabled:
            return True
        if self.ai_provider == "auto" and self.google_enabled:
            return True
        return False

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
