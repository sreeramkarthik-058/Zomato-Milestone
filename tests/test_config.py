import pytest
from pydantic import ValidationError

from restaurant_recommender.config import (
    DEFAULT_DATASET_URL,
    Settings,
    clear_settings_cache,
    get_settings,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_settings_defaults():
    settings = Settings()
    assert settings.llm_model == "llama-3.3-70b-versatile"
    assert settings.llm_provider == "groq"
    assert settings.dataset_url == DEFAULT_DATASET_URL
    assert settings.max_candidates == 20
    assert settings.top_n == 5
    assert settings.prompt_version == "v1"
    assert settings.force_refresh is False


def test_settings_load_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "llama-3.1-8b-instant")
    monkeypatch.setenv("MAX_CANDIDATES", "15")
    monkeypatch.setenv("TOP_N", "3")
    monkeypatch.setenv("CACHE_PATH", "/tmp/test.parquet")
    monkeypatch.setenv("FORCE_REFRESH", "true")

    settings = Settings()

    assert settings.llm_api_key == "test-key"
    assert settings.llm_model == "llama-3.1-8b-instant"
    assert settings.max_candidates == 15
    assert settings.top_n == 3
    assert str(settings.cache_path) == "/tmp/test.parquet"
    assert settings.force_refresh is True


def test_get_settings_cached():
    first = get_settings()
    second = get_settings()
    assert first is second


@pytest.mark.parametrize("max_candidates", [0, -1])
def test_settings_rejects_invalid_max_candidates(max_candidates: int):
    with pytest.raises(ValidationError):
        Settings(max_candidates=max_candidates)


@pytest.mark.parametrize("top_n", [0, -2])
def test_settings_rejects_invalid_top_n(top_n: int):
    with pytest.raises(ValidationError):
        Settings(top_n=top_n)


def test_settings_no_hardcoded_api_key():
    """Default in code must be empty; local .env may supply a key at runtime."""
    assert Settings.model_fields["llm_api_key"].default == ""
