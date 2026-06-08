"""Budget tier to cost band mapping (architecture §6.3, INR approx for two)."""

from __future__ import annotations

# Tunable after profiling — see scripts/profile_dataset.py
BUDGET_LOW_MAX = 500.0
BUDGET_MEDIUM_MAX = 1500.0


def cost_band_from_amount(approx_cost: float | None) -> str | None:
    """Map numeric cost to low / medium / high band."""
    if approx_cost is None:
        return None
    if approx_cost <= BUDGET_LOW_MAX:
        return "low"
    if approx_cost <= BUDGET_MEDIUM_MAX:
        return "medium"
    return "high"
