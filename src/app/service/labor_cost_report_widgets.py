"""Widgets at the top of the weekly labor cost reports.

Each widget compares the selected month's totals with the monthly breakeven
from Performance static data (see service/performance_data.py), or shows an
overhead figure. The backend builds the list so every report shows only the
widgets that apply to it:

  revenue  - Gross Revenue, Gross Profit and Average Revenue per Day deltas
             (actual - breakeven; positive is good)
  wages    - Wages Regular, Wages Overtime and Overtime/Regular % deltas
             (actual - breakeven; positive is good)
  overhead - Overhead / Week, per Employee / Week and per Employee / Day

Wages breakevens come from Total Wages / 12 (the monthly wages budget):
  Wages Regular breakeven   = Total Wages / 12
  Wages Overtime breakeven  = Total Wages / 12 - actual regular wages
                              (the budget left for overtime this month)
  Overtime/Regular breakeven = Wages Overtime breakeven / actual regular wages
"""
from typing import Optional

from src.app.service.labor_cost_report_rows import (
    INSTALLER_VARIANT_AG,
    INSTALLER_VARIANT_COMBINED,
    INSTALLER_VARIANT_SUBS,
)
from src.app.service.performance_data import WORK_DAYS_PER_WEEK

REVENUE, WAGES, OVERHEAD = "revenue", "wages", "overhead"
GOOD_WHEN_POSITIVE, GOOD_WHEN_NEGATIVE = "positive", "negative"

# Why a delta widget has no breakeven (shown under the blank value).
NO_STATIC_DATA_NOTE = "Break even not set - enter it on Static Data"
NO_REGULAR_WAGES_NOTE = "No regular wages this month"

# Widget groups per report, in display order.
FABRICATION_WIDGET_GROUPS = (REVENUE, WAGES, OVERHEAD)
INSTALLER_WIDGET_GROUPS = {
    INSTALLER_VARIANT_AG: (REVENUE, WAGES, OVERHEAD),
    INSTALLER_VARIANT_SUBS: (),
    INSTALLER_VARIANT_COMBINED: (REVENUE, OVERHEAD),
}


def _round(value: Optional[float]) -> Optional[float]:
    return round(value, 2) if value is not None else None


def _delta(actual: Optional[float], breakeven: Optional[float]) -> Optional[float]:
    if actual is None or breakeven is None:
        return None
    return round(actual - breakeven, 2)


def _widget(key: str, group: str, label: str, value: Optional[float], fmt: str = "currency",
            breakeven: Optional[float] = None, good_when: Optional[str] = None,
            missing_note: str = NO_STATIC_DATA_NOTE) -> dict:
    return {
        "key": key,
        "group": group,
        "label": label,
        "value": value,
        "format": fmt,
        "breakeven": breakeven,
        "good_when": good_when,
        # Only for delta widgets without a breakeven.
        "note": missing_note if good_when is not None and breakeven is None else None,
    }


def build_labor_cost_widgets(
    *,
    groups: tuple[str, ...],
    totals: dict,
    static_data: dict,
    overhead_per_week: Optional[float],
    total_employees: Optional[float],
    wages_regular_key: str,
    wages_overtime_key: str,
) -> list[dict]:
    """Widgets for one report from the month's `totals` (the TOTAL column) and the year's static data."""
    widgets: list[dict] = []

    if REVENUE in groups:
        gross_revenue_be = static_data.get("breakeven_gross_revenue")
        gross_profit_be = static_data.get("breakeven_gross_profit")
        revenue_per_day_be = static_data.get("breakeven_avg_revenue_per_day")
        widgets += [
            _widget("gross_revenue_delta", REVENUE, "Gross Revenue Delta",
                    _delta(totals.get("gross_revenue"), gross_revenue_be), breakeven=gross_revenue_be,
                    good_when=GOOD_WHEN_POSITIVE),
            _widget("gross_profit_delta", REVENUE, "Gross Profit Delta",
                    _delta(totals.get("gross_profit"), gross_profit_be), breakeven=gross_profit_be,
                    good_when=GOOD_WHEN_POSITIVE),
            _widget("average_revenue_per_day_delta", REVENUE, "Average Revenue per Day Delta",
                    _delta(totals.get("average_revenue_per_day"), revenue_per_day_be), breakeven=revenue_per_day_be,
                    good_when=GOOD_WHEN_POSITIVE),
        ]

    if WAGES in groups:
        total_wages = static_data.get("total_wages")
        wages_budget = total_wages / 12 if total_wages is not None else None
        regular = totals.get(wages_regular_key)
        overtime = totals.get(wages_overtime_key)
        overtime_be = wages_budget - regular if wages_budget is not None and regular is not None else None
        has_regular = bool(regular)
        overtime_pct = overtime / regular * 100 if has_regular and overtime is not None else None
        overtime_pct_be = overtime_be / regular * 100 if has_regular and overtime_be is not None else None
        widgets += [
            _widget("wages_regular_delta", WAGES, "Wages Regular Delta",
                    _delta(regular, wages_budget), breakeven=_round(wages_budget), good_when=GOOD_WHEN_POSITIVE),
            _widget("wages_overtime_delta", WAGES, "Wages Overtime Delta",
                    _delta(overtime, overtime_be), breakeven=_round(overtime_be), good_when=GOOD_WHEN_POSITIVE),
            _widget("overtime_regular_pct_delta", WAGES, "Overtime/Regular Delta",
                    _delta(overtime_pct, overtime_pct_be), fmt="percent", breakeven=_round(overtime_pct_be),
                    good_when=GOOD_WHEN_POSITIVE,
                    missing_note=NO_STATIC_DATA_NOTE if wages_budget is None else NO_REGULAR_WAGES_NOTE),
        ]

    if OVERHEAD in groups:
        per_employee_week = (
            overhead_per_week / total_employees if overhead_per_week is not None and total_employees else None
        )
        widgets += [
            _widget("overhead_per_week", OVERHEAD, "Overhead / Week", _round(overhead_per_week)),
            _widget("overhead_per_employee_week", OVERHEAD, "Overhead per Employee / Week", _round(per_employee_week)),
            _widget("overhead_per_employee_day", OVERHEAD, "Overhead per Employee / Day",
                    _round(per_employee_week / WORK_DAYS_PER_WEEK if per_employee_week is not None else None)),
        ]

    return widgets
