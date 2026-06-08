import pytest

from restaurant_recommender.config import Settings
from restaurant_recommender.llm.prompt_builder import PromptBuilder
from restaurant_recommender.models import Budget, Candidate, CandidateList, UserPreferences


@pytest.fixture
def preferences() -> UserPreferences:
    return UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="North Indian",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )


@pytest.fixture
def candidates() -> CandidateList:
    return CandidateList(
        items=[
            Candidate(
                id="abc123",
                name="Jalsa",
                location="Banashankari, Bangalore",
                cuisines=["North Indian", "Chinese"],
                rating=4.1,
                approx_cost=800.0,
            ),
        ]
    )


def test_build_prompt_includes_all_preference_fields(
    preferences: UserPreferences,
    candidates: CandidateList,
):
    payload = PromptBuilder(settings=Settings(prompt_version="v1", top_n=3)).build(
        preferences,
        candidates,
        top_n=3,
    )

    assert "Bangalore" in payload.user_prompt
    assert "medium" in payload.user_prompt
    assert "North Indian" in payload.user_prompt
    assert "4.0" in payload.user_prompt
    assert "family-friendly" in payload.user_prompt
    assert payload.prompt_version == "v1"


def test_build_prompt_embeds_candidates_json(
    preferences: UserPreferences,
    candidates: CandidateList,
):
    payload = PromptBuilder(settings=Settings(top_n=5)).build(preferences, candidates)

    assert '"id": "abc123"' in payload.user_prompt
    assert '"name": "Jalsa"' in payload.user_prompt
    assert "Candidate restaurants" in payload.user_prompt


def test_build_prompt_snapshot_stable(
    preferences: UserPreferences,
    candidates: CandidateList,
):
    builder = PromptBuilder(settings=Settings(prompt_version="v1", top_n=5))
    first = builder.build(preferences, candidates)
    second = builder.build(preferences, candidates)

    assert first.system_prompt == second.system_prompt
    assert first.user_prompt == second.user_prompt


def test_to_chat_messages_for_groq(preferences: UserPreferences, candidates: CandidateList):
    payload = PromptBuilder().build(preferences, candidates)
    messages = payload.to_chat_messages()

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "JSON" in messages[0]["content"]


def test_missing_template_version_raises(preferences: UserPreferences, candidates: CandidateList):
    with pytest.raises(FileNotFoundError):
        PromptBuilder(settings=Settings(prompt_version="v999")).build(
            preferences,
            candidates,
        )
