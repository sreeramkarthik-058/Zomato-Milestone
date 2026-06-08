"""LLM prompt construction and response parsing (Groq chat completions)."""

from restaurant_recommender.llm.parser import (
    ParseLLMResponseError,
    parse_llm_response,
    repair_json,
    strip_markdown_fences,
)
from restaurant_recommender.llm.engine import RecommendationEngine
from restaurant_recommender.llm.prompt_builder import PromptBuilder
from restaurant_recommender.llm.provider import (
    GroqProvider,
    LLMProvider,
    LLMProviderError,
    MockLLMProvider,
    create_llm_provider,
)

__all__ = [
    "GroqProvider",
    "LLMProvider",
    "LLMProviderError",
    "MockLLMProvider",
    "ParseLLMResponseError",
    "PromptBuilder",
    "RecommendationEngine",
    "create_llm_provider",
    "parse_llm_response",
    "repair_json",
    "strip_markdown_fences",
]
