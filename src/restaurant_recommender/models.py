"""Pydantic domain models shared across pipeline stages."""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class Budget(str, Enum):
    """User budget tier mapped to cost bands at filter time."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationStatus(str, Enum):
    """Outcome of a recommendation request."""

    SUCCESS = "success"
    NO_MATCHES = "no_matches"
    ERROR = "error"


class Restaurant(BaseModel):
    """Normalized restaurant record from the dataset store."""

    id: str
    name: str
    location: str
    city: str | None = None
    cuisines: list[str] = Field(default_factory=list)
    rating: float = Field(ge=0)
    approx_cost: float | None = Field(default=None, ge=0)
    cost_band: str | None = None

    @classmethod
    def generate_id(cls, name: str, location: str) -> str:
        """Stable id from name and location (architecture §6.2)."""
        key = f"{name.strip().lower()}|{location.strip().lower()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


class UserPreferences(BaseModel):
    """User input collected by the presentation layer."""

    location: str = Field(min_length=1)
    budget: Budget
    cuisine: str = Field(min_length=1)
    min_rating: float = Field(ge=0.0, le=5.0)
    additional_preferences: str | None = None

    @field_validator("location", "cuisine", mode="before")
    @classmethod
    def _strip_required_strings(cls, value: str) -> str:
        if not isinstance(value, str):
            raise TypeError("expected string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("additional_preferences", mode="before")
    @classmethod
    def _normalize_additional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("expected string or null")
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def _cap_additional_preferences(self) -> Self:
        if (
            self.additional_preferences is not None
            and len(self.additional_preferences) > 2000
        ):
            raise ValueError("additional_preferences must be at most 2000 characters")
        return self


class Candidate(BaseModel):
    """Slim restaurant payload sent to the LLM."""

    id: str
    name: str
    location: str
    cuisines: list[str]
    rating: float
    approx_cost: float | None = None

    @classmethod
    def from_restaurant(cls, restaurant: Restaurant) -> Self:
        return cls(
            id=restaurant.id,
            name=restaurant.name,
            location=restaurant.location,
            cuisines=restaurant.cuisines,
            rating=restaurant.rating,
            approx_cost=restaurant.approx_cost,
        )


class CandidateList(BaseModel):
    """Filtered shortlist passed to the prompt builder."""

    items: list[Candidate] = Field(default_factory=list)

    def __len__(self) -> int:
        return len(self.items)

    def ids(self) -> set[str]:
        return {item.id for item in self.items}


class PromptPayload(BaseModel):
    """Rendered prompts for the LLM provider (Groq chat.completions)."""

    system_prompt: str
    user_prompt: str
    prompt_version: str = "v1"

    def to_chat_messages(self) -> list[dict[str, str]]:
        """Messages list for Groq/OpenAI-compatible chat APIs."""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]


class LLMRecommendationItem(BaseModel):
    """Single ranked item from parsed LLM JSON (architecture §5.3)."""

    restaurant_id: str
    rank: int = Field(ge=1)
    explanation: str = Field(min_length=1)


class LLMResponse(BaseModel):
    """Parsed LLM response before store enrichment."""

    recommendations: list[LLMRecommendationItem]
    summary: str | None = None


class RecommendationResult(BaseModel):
    """User-facing recommendation row (architecture §5.4)."""

    rank: int = Field(ge=1)
    restaurant_name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str
    restaurant_id: str | None = None


class RecommendationResponse(BaseModel):
    """Final orchestrator response."""

    status: RecommendationStatus
    recommendations: list[RecommendationResult] = Field(default_factory=list)
    summary: str | None = None
    message: str | None = None
