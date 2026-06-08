"""LLM provider abstraction with Groq and mock implementations."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from restaurant_recommender.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MAX_RETRIES = 2
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class LLMProviderError(RuntimeError):
    """Raised when the LLM provider call fails after retries."""


class LLMProvider(ABC):
    """Provider interface for chat completion (Groq-compatible message format)."""

    @abstractmethod
    def complete(self, messages: list[dict[str, str]]) -> str:
        """Return the assistant message content."""


class GroqProvider(LLMProvider):
    """Groq chat completions via the official `groq` SDK."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._settings = settings or get_settings()
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

        if not self._settings.llm_api_key.strip():
            raise LLMProviderError(
                "LLM_API_KEY is not set. Add your Groq API key to .env "
                "(https://console.groq.com/keys)."
            )

        from groq import Groq

        self._client = Groq(
            api_key=self._settings.llm_api_key,
            timeout=self._timeout_seconds,
        )

    def complete(self, messages: list[dict[str, str]]) -> str:
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._settings.llm_model,
                    messages=messages,
                    temperature=0.2,
                )
                content = response.choices[0].message.content
                if not content or not str(content).strip():
                    raise LLMProviderError("Groq returned an empty response")
                return str(content).strip()
            except Exception as exc:
                last_error = exc
                if attempt >= self._max_retries or not _is_retryable(exc):
                    break
                delay = 2**attempt
                logger.warning(
                    "Groq request failed (attempt %s/%s): %s; retrying in %ss",
                    attempt + 1,
                    self._max_retries + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)

        raise LLMProviderError(f"Groq API call failed: {last_error}") from last_error


class MockLLMProvider(LLMProvider):
    """Deterministic provider for tests (no network)."""

    def __init__(self, response: str) -> None:
        self._response = response
        self.call_count = 0
        self.last_messages: list[dict[str, str]] | None = None

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.call_count += 1
        self.last_messages = messages
        return self._response


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Factory: Groq for production, mock only when constructed directly in tests."""
    settings = settings or get_settings()
    if settings.llm_provider == "groq":
        return GroqProvider(settings)
    raise LLMProviderError(
        f"Unsupported LLM_PROVIDER={settings.llm_provider!r}. "
        "Use 'groq' or pass MockLLMProvider in tests."
    )


def _is_retryable(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in _RETRYABLE_STATUS_CODES:
        return True
    name = type(exc).__name__.lower()
    return "timeout" in name or "connection" in name or "rate" in name
