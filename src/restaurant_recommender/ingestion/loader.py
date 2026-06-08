"""Load raw records from the Hugging Face Zomato dataset."""

from __future__ import annotations

import re
from typing import Any

from datasets import load_dataset

# HF dataset: ManikaSaini/zomato-restaurant-recommendation
# Columns (train split):
#   url, address, name, online_order, book_table, rate, votes, phone,
#   location, rest_type, dish_liked, cuisines, approx_cost(for two people),
#   reviews_list, menu_item, listed_in(type), listed_in(city)

_DATASET_ID_PATTERN = re.compile(
    r"(?:https?://huggingface\.co/datasets/)?"
    r"(?P<id>[\w.-]+/[\w.-]+)/?$"
)


def parse_dataset_id(dataset_url: str) -> str:
    """Extract Hugging Face dataset id from a repo id or full URL."""
    dataset_url = dataset_url.strip()
    match = _DATASET_ID_PATTERN.search(dataset_url)
    if match:
        return match.group("id")
    if "/" in dataset_url and not dataset_url.startswith("http"):
        return dataset_url
    raise ValueError(f"Cannot parse Hugging Face dataset id from: {dataset_url!r}")


def load_raw_dataset(dataset_url: str, *, split: str = "train") -> list[dict[str, Any]]:
    """
    Download and load the Zomato dataset from Hugging Face.

    Returns a list of row dicts (one dict per restaurant).
    """
    dataset_id = parse_dataset_id(dataset_url)
    dataset = load_dataset(dataset_id, split=split)
    return [dict(row) for row in dataset]
