"""AI-powered restaurant recommendation service (Zomato milestone)."""

from restaurant_recommender.config import Settings, get_settings
from restaurant_recommender.filtering import FilterService
from restaurant_recommender.ingestion import DataIngestionService, IngestionReport
from restaurant_recommender.llm import (
    PromptBuilder,
    RecommendationEngine,
    create_llm_provider,
    parse_llm_response,
)
from restaurant_recommender.models import (
    Budget,
    Candidate,
    CandidateList,
    LLMRecommendationItem,
    LLMResponse,
    PromptPayload,
    RecommendationResponse,
    RecommendationResult,
    RecommendationStatus,
    Restaurant,
    UserPreferences,
)

__all__ = [
    "DataIngestionService",
    "FilterService",
    "IngestionReport",
    "PromptBuilder",
    "RecommendationEngine",
    "create_llm_provider",
    "parse_llm_response",
    "Budget",
    "Candidate",
    "CandidateList",
    "LLMRecommendationItem",
    "LLMResponse",
    "PromptPayload",
    "RecommendationResponse",
    "RecommendationResult",
    "RecommendationStatus",
    "Restaurant",
    "Settings",
    "UserPreferences",
    "get_settings",
]

__version__ = "0.1.0"
