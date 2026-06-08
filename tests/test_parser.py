import json

import pytest

from restaurant_recommender.llm.parser import (
    ParseLLMResponseError,
    parse_llm_response,
    repair_json,
    strip_markdown_fences,
)


VALID_IDS = {"id1", "id2"}


def _response_body(**overrides: object) -> str:
    payload = {
        "summary": "Great options for your criteria.",
        "recommendations": [
            {
                "restaurant_id": "id1",
                "rank": 1,
                "explanation": "Matches cuisine and rating.",
            },
            {
                "restaurant_id": "id2",
                "rank": 2,
                "explanation": "Good budget fit.",
            },
        ],
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_strip_markdown_fences():
    raw = '```json\n{"recommendations": []}\n```'
    assert strip_markdown_fences(raw).startswith("{")


def test_repair_json_extracts_object():
    raw = 'Here is the result:\n```json\n{"recommendations": [{"restaurant_id": "id1", "rank": 1, "explanation": "x"}]}\n```'
    repaired = repair_json(raw)
    data = json.loads(repaired)
    assert "recommendations" in data


def test_parse_valid_json():
    result = parse_llm_response(_response_body(), valid_restaurant_ids=VALID_IDS, top_n=5)
    assert len(result.recommendations) == 2
    assert result.recommendations[0].rank == 1
    assert result.summary == "Great options for your criteria."


def test_parse_markdown_wrapped_json():
    wrapped = f"```json\n{_response_body()}\n```"
    result = parse_llm_response(wrapped, valid_restaurant_ids=VALID_IDS, top_n=5)
    assert len(result.recommendations) == 2


def test_parse_drops_unknown_restaurant_id():
    body = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "id1", "rank": 1, "explanation": "ok"},
                {"restaurant_id": "unknown", "rank": 2, "explanation": "skip"},
            ]
        }
    )
    result = parse_llm_response(body, valid_restaurant_ids=VALID_IDS, top_n=5)
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant_id == "id1"


def test_parse_duplicate_ranks_keeps_first():
    body = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "id1", "rank": 1, "explanation": "first"},
                {"restaurant_id": "id2", "rank": 1, "explanation": "duplicate rank"},
            ]
        }
    )
    result = parse_llm_response(body, valid_restaurant_ids=VALID_IDS, top_n=5)
    assert len(result.recommendations) == 1


def test_parse_rejects_invalid_json():
    with pytest.raises(ParseLLMResponseError):
        parse_llm_response("not json at all", valid_restaurant_ids=VALID_IDS, top_n=5)


def test_parse_rejects_missing_recommendations_key():
    with pytest.raises(ParseLLMResponseError):
        parse_llm_response('{"summary": "hi"}', valid_restaurant_ids=VALID_IDS, top_n=5)


def test_parse_raises_when_all_ids_invalid():
    body = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "bad", "rank": 1, "explanation": "nope"},
            ]
        }
    )
    with pytest.raises(ParseLLMResponseError):
        parse_llm_response(body, valid_restaurant_ids=VALID_IDS, top_n=5)


def test_parse_caps_to_top_n():
    body = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "id1", "rank": 1, "explanation": "a"},
                {"restaurant_id": "id2", "rank": 2, "explanation": "b"},
                {"restaurant_id": "id1", "rank": 3, "explanation": "c"},
            ]
        }
    )
    result = parse_llm_response(body, valid_restaurant_ids=VALID_IDS, top_n=2)
    assert len(result.recommendations) == 2
