"""AG REDO revenue: a redo is a cost to the business, so its revenue is stored negative."""
from typing import Optional

AG_REDO_FAB_TYPE = "AG REDO"


def is_ag_redo(fab_type: Optional[str]) -> bool:
    return (fab_type or "").strip().upper() == AG_REDO_FAB_TYPE


def ag_redo_revenue(
    cost_per_sqft: Optional[float],
    redo_total_sqft: Optional[float],
    total_sqft: Optional[float] = None,
) -> Optional[float]:
    """-(cost_per_sqft * redo sq ft), e.g. 101.5 * 58 -> -5887.0.

    Falls back to total_sqft when redo_total_sqft is missing or 0 (older rows), matching the
    AG Redo report. Returns None when there is no cost or no square footage to price.
    """
    if cost_per_sqft is None:
        return None
    sqft = float(redo_total_sqft or 0)
    if sqft <= 0:
        sqft = float(total_sqft or 0)
    if sqft <= 0:
        return None
    return -round(float(cost_per_sqft) * sqft, 2)


def apply_ag_redo_revenue(fab) -> None:
    """Set fab.revenue from its cost per sq ft and redo sq ft when both are known."""
    revenue = ag_redo_revenue(fab.cost_per_sqft, fab.redo_total_sqft, fab.total_sqft)
    if revenue is not None:
        fab.revenue = revenue
