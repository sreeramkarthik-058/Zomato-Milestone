"""Build versioned prompts for Groq chat completions."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from restaurant_recommender.config import Settings, get_settings
from restaurant_recommender.models import CandidateList, PromptPayload, UserPreferences

# Project root: .../src/restaurant_recommender/llm/prompt_builder.py -> parents[3]
_DEFAULT_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


class PromptBuilder:
    """Render system and user prompts from templates (architecture §4.4)."""

    def __init__(
        self,
        settings: Settings | None = None,
        prompts_dir: Path | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._prompts_dir = Path(prompts_dir or _DEFAULT_PROMPTS_DIR)
        self._env = Environment(
            loader=FileSystemLoader(str(self._prompts_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def build(
        self,
        preferences: UserPreferences,
        candidates: CandidateList,
        top_n: int | None = None,
        *,
        prompt_version: str | None = None,
    ) -> PromptPayload:
        """Render prompts for Groq `chat.completions` (system + user messages)."""
        version = prompt_version or self._settings.prompt_version
        limit = top_n if top_n is not None else self._settings.top_n

        system_template = self._load_template(f"recommend_{version}.system.txt")
        user_template = self._load_template(f"recommend_{version}.user.jinja2")

        candidates_json = json.dumps(
            [candidate.model_dump() for candidate in candidates.items],
            indent=2,
            ensure_ascii=False,
        )

        system_prompt = system_template.render(top_n=limit)
        user_prompt = user_template.render(
            preferences=preferences,
            candidates_json=candidates_json,
            top_n=limit,
        )

        return PromptPayload(
            system_prompt=system_prompt.strip(),
            user_prompt=user_prompt.strip(),
            prompt_version=version,
        )

    def _load_template(self, filename: str) -> object:
        try:
            return self._env.get_template(filename)
        except TemplateNotFound as exc:
            raise FileNotFoundError(
                f"Prompt template not found: {self._prompts_dir / filename}"
            ) from exc
