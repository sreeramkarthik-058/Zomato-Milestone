# Zomato Milestone — Restaurant Recommendation

AI-powered restaurant recommendations using the Hugging Face Zomato dataset and an LLM.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set LLM_API_KEY
```

## Run tests

```bash
pytest
```

## Documentation

See [`docs/`](docs/) for context, architecture, implementation plan, and edge cases.

## Ingest data (Phase 2)

```bash
# Optional: profile cost distribution for budget bands
PYTHONPATH=src python scripts/profile_dataset.py

# First run downloads from Hugging Face and writes ./data/restaurants.parquet
PYTHONPATH=src python -c "
from restaurant_recommender.ingestion import DataIngestionService
print(DataIngestionService().run_if_needed())
"
```

## Status

- **Phase 1** — Models and configuration
- **Phase 2** — Data ingestion and Parquet store (`ingestion/`, `store/`)
- **Phase 3** — Filter service (`filtering/`)
- **Phase 4** — Prompt builder and Groq-oriented response parser (`llm/`, `prompts/`)
- **Phase 5** — Groq provider and recommendation engine (`llm/provider.py`, `llm/engine.py`)
