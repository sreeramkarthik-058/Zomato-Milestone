"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATASET_URL = (
    "https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation"
)


class Settings(BaseSettings):
    """Runtime settings for the recommendation pipeline."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(
        default="llama-3.3-70b-versatile",
        alias="LLM_MODEL",
        description="Groq model id (https://console.groq.com/docs/models)",
    )
    llm_provider: Literal["groq", "mock"] = Field(default="groq", alias="LLM_PROVIDER")

    dataset_url: str = Field(default=DEFAULT_DATASET_URL, alias="DATASET_URL")
    cache_path: Path = Field(default=Path("./data/restaurants.parquet"), alias="CACHE_PATH")
    force_refresh: bool = Field(default=False, alias="FORCE_REFRESH")

    max_candidates: int = Field(default=20, ge=1, alias="MAX_CANDIDATES")
    top_n: int = Field(default=5, ge=1, alias="TOP_N")
    prompt_version: str = Field(default="v1", alias="PROMPT_VERSION")

    max_additional_preferences_length: int = Field(
        default=2000,
        description="Max characters for optional free-text preferences (EC-INP-16).",
    )

    @field_validator("cache_path", mode="before")
    @classmethod
    def _coerce_cache_path(cls, value: str | Path) -> Path:
        return Path(value)

    @field_validator("force_refresh", mode="before")
    @classmethod
    def _parse_force_refresh(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (reload process to pick up env changes)."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings (useful in tests)."""
    get_settings.cache_clear()
