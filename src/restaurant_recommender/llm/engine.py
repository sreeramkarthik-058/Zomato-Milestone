"""Recommendation engine: Groq call, parse, enrich from store."""

from __future__ import annotations

import logging
import time

from restaurant_recommender.config import Settings, get_settings
from restaurant_recommender.formatting.output_formatter import to_recommendation_result
from restaurant_recommender.llm.parser import ParseLLMResponseError, parse_llm_response
from restaurant_recommender.llm.provider import (
    LLMProvider,
    LLMProviderError,
    create_llm_provider,
)
from restaurant_recommender.models import (
    CandidateList,
    LLMRecommendationItem,
    LLMResponse,
    PromptPayload,
    RecommendationResponse,
    RecommendationResult,
    RecommendationStatus,
    Restaurant,
)
from restaurant_recommender.store.restaurant_store import RestaurantStore

logger = logging.getLogger(__name__)

_REPAIR_USER_MESSAGE = (
    "Your previous response was not valid JSON. "
    "Return only a single valid JSON object matching the required schema. "
    "No markdown fences or extra text."
)


class RecommendationEngine:
    """Call LLM (Groq), validate output, and enrich with dataset fields."""

    def __init__(
        self,
        settings: Settings | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._provider = provider or create_llm_provider(self._settings)

    def recommend(
        self,
        prompt: PromptPayload,
        candidates: CandidateList,
        store: RestaurantStore,
        *,
        top_n: int | None = None,
    ) -> RecommendationResponse:
        """
        Run Groq chat completion, parse rankings, enrich from store.

        Dataset fields (name, cuisine, rating, cost) always come from the store,
        not from the LLM (architecture §4.5).
        """
        limit = top_n if top_n is not None else self._settings.top_n
        valid_ids = candidates.ids()

        if not valid_ids:
            return RecommendationResponse(
                status=RecommendationStatus.NO_MATCHES,
                message="No candidates to rank.",
            )

        messages = prompt.to_chat_messages()
        start = time.perf_counter()

        try:
            raw = self._provider.complete(messages)
            llm_response = self._parse_with_optional_repair(
                raw,
                messages=messages,
                valid_restaurant_ids=valid_ids,
                top_n=limit,
            )
        except (LLMProviderError, ParseLLMResponseError) as exc:
            logger.exception("Recommendation engine failed")
            return RecommendationResponse(
                status=RecommendationStatus.ERROR,
                message=str(exc),
            )

        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "llm_latency_ms=%s candidates=%s results=%s",
            latency_ms,
            len(valid_ids),
            len(llm_response.recommendations),
        )

        results = self._enrich(llm_response.recommendations, store)
        if not results:
            return RecommendationResponse(
                status=RecommendationStatus.ERROR,
                message="Could not enrich any recommendations from the store.",
            )

        return RecommendationResponse(
            status=RecommendationStatus.SUCCESS,
            recommendations=results,
            summary=llm_response.summary,
        )

    def _parse_with_optional_repair(
        self,
        raw: str,
        *,
        messages: list[dict[str, str]],
        valid_restaurant_ids: set[str],
        top_n: int,
    ) -> LLMResponse:
        try:
            return parse_llm_response(
                raw,
                valid_restaurant_ids=valid_restaurant_ids,
                top_n=top_n,
            )
        except ParseLLMResponseError as first_error:
            logger.warning("LLM parse failed, attempting repair: %s", first_error)
            repair_messages = [
                *messages,
                {"role": "assistant", "content": raw},
                {"role": "user", "content": _REPAIR_USER_MESSAGE},
            ]
            repaired_raw = self._provider.complete(repair_messages)
            return parse_llm_response(
                repaired_raw,
                valid_restaurant_ids=valid_restaurant_ids,
                top_n=top_n,
            )

    def _enrich(
        self,
        items: list[LLMRecommendationItem],
        store: RestaurantStore,
    ) -> list[RecommendationResult]:
        enriched: list[RecommendationResult] = []
        for item in sorted(items, key=lambda i: i.rank):
            restaurant = store.get_by_id(item.restaurant_id)
            if restaurant is None:
                logger.warning(
                    "Restaurant id %s missing from store after LLM rank",
                    item.restaurant_id,
                )
                continue
            enriched.append(to_recommendation_result(item, restaurant))
        enriched.sort(key=lambda r: r.rank)
        return enriched
