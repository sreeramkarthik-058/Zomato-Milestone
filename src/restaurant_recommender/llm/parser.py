"""Parse and validate JSON responses from Groq chat completions."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from restaurant_recommender.models import LLMRecommendationItem, LLMResponse

logger = logging.getLogger(__name__)

_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class ParseLLMResponseError(ValueError):
    """Raised when LLM output cannot be parsed or validated."""


def strip_markdown_fences(raw: str) -> str:
    """Remove ```json fences if present (EC-LLM-06)."""
    text = raw.strip()
    if text.startswith("```"):
        text = _FENCE_PATTERN.sub("", text).strip()
    return text


def repair_json(raw: str) -> str:
    """
    Best-effort cleanup: strip fences and isolate the outermost JSON object.
    """
    text = strip_markdown_fences(raw)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    return text


def parse_llm_response(
    raw: str,
    *,
    valid_restaurant_ids: set[str],
    top_n: int,
    attempt_repair: bool = True,
) -> LLMResponse:
    """
    Parse Groq model output into LLMResponse.

    Drops unknown restaurant ids (EC-LLM-14). Resolves duplicate ranks by
    keeping the first occurrence (EC-LLM-12).
    """
    payload = _load_json_payload(raw, attempt_repair=attempt_repair)
    recommendations_raw = payload.get("recommendations")
    if not isinstance(recommendations_raw, list):
        raise ParseLLMResponseError("Missing or invalid 'recommendations' array")

    seen_ranks: set[int] = set()
    parsed: list[LLMRecommendationItem] = []

    for entry in recommendations_raw:
        if not isinstance(entry, dict):
            logger.warning("Skipping non-object recommendation entry: %r", entry)
            continue

        restaurant_id = str(entry.get("restaurant_id", "")).strip()
        if restaurant_id not in valid_restaurant_ids:
            logger.warning("Dropping unknown restaurant_id from LLM response: %s", restaurant_id)
            continue

        try:
            rank = int(entry["rank"])
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Skipping recommendation with invalid rank: %r", entry)
            continue

        if rank in seen_ranks:
            logger.warning("Duplicate rank %s; keeping first occurrence", rank)
            continue
        if rank < 1 or rank > top_n:
            logger.warning("Rank %s out of range 1..%s; skipping", rank, top_n)
            continue

        explanation = str(entry.get("explanation", "")).strip()
        if not explanation:
            logger.warning("Skipping recommendation with empty explanation: %s", restaurant_id)
            continue

        try:
            item = LLMRecommendationItem(
                restaurant_id=restaurant_id,
                rank=rank,
                explanation=explanation,
            )
        except ValidationError as exc:
            logger.warning("Invalid recommendation item %s: %s", restaurant_id, exc)
            continue

        seen_ranks.add(rank)
        parsed.append(item)

    parsed.sort(key=lambda item: item.rank)
    if len(parsed) > top_n:
        parsed = parsed[:top_n]

    if not parsed:
        raise ParseLLMResponseError("No valid recommendations after validation")

    summary = payload.get("summary")
    if summary is not None and not isinstance(summary, str):
        summary = str(summary)
    if isinstance(summary, str) and not summary.strip():
        summary = None

    return LLMResponse(recommendations=parsed, summary=summary)


def _load_json_payload(raw: str, *, attempt_repair: bool) -> dict[str, Any]:
    text = raw.strip()
    attempts = [text]
    if attempt_repair:
        attempts.append(repair_json(text))

    last_error: Exception | None = None
    for candidate in attempts:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if not isinstance(data, dict):
            raise ParseLLMResponseError("LLM response JSON must be an object")
        return data

    raise ParseLLMResponseError("Invalid JSON in LLM response") from last_error
