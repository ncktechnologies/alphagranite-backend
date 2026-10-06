"""Performance-page inputs (yearly static data, weekly subcontractor labor) and
the values derived from them for the reports and the dashboard."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.performance_data import PerformanceStaticData, SubcontractorWeeklyLabor

# Working days per year used for the breakeven revenue-per-day figure.
WORKING_DAYS_PER_YEAR = 253


def derive_static_data(
    total_expenses: Optional[float],
    total_wages: Optional[float],
    breakeven_gross_revenue: Optional[float],
) -> dict:
    """Entered figures plus everything calculated from them (None when an input is missing).

    difference (overhead)         = total_expenses - total_wages
    overhead_monthly              = difference / 12
    overhead_weekly               = difference / 52   (overhead per week used by the reports)
    breakeven_gross_profit        = total_expenses / 12
    breakeven_avg_revenue_per_day = breakeven_gross_revenue / 253 * 12
    """
    difference = (
        total_expenses - total_wages if total_expenses is not None and total_wages is not None else None
    )
    return {
        "total_expenses": total_expenses,
        "total_wages": total_wages,
        "difference_overhead": _round(difference),
        "overhead_monthly": _round(difference / 12 if difference is not None else None),
        "overhead_weekly": _round(difference / 52 if difference is not None else None),
        "breakeven_gross_revenue": breakeven_gross_revenue,
        "breakeven_gross_profit": _round(total_expenses / 12 if total_expenses is not None else None),
        "breakeven_avg_revenue_per_day": _round(
            breakeven_gross_revenue / WORKING_DAYS_PER_YEAR * 12 if breakeven_gross_revenue is not None else None
        ),
    }


# Dashboard periods -> how many of them fit in a year (breakeven GP is a monthly figure).
_PERIODS_PER_YEAR = {"today": WORKING_DAYS_PER_YEAR, "this_week": 52, "this_month": 12}


def breakeven_gross_profit_for_period(total_expenses: Optional[float], period: str) -> Optional[float]:
    """Breakeven gross profit scaled to a dashboard period (yearly expenses / periods per year)."""
    if total_expenses is None or period not in _PERIODS_PER_YEAR:
        return None
    return total_expenses / _PERIODS_PER_YEAR[period]


def gross_profit_delta(gross_profit: Optional[float], breakeven_gross_profit: Optional[float]) -> Optional[float]:
    """Gross profit minus breakeven gross profit: negative = below breakeven. Plain signed number."""
    if gross_profit is None or breakeven_gross_profit is None:
        return None
    return round(gross_profit - breakeven_gross_profit, 2)


async def get_static_data_row(db: AsyncSession, year: int) -> Optional[PerformanceStaticData]:
    return (
        await db.execute(select(PerformanceStaticData).where(PerformanceStaticData.year == year))
    ).scalar_one_or_none()


async def get_static_data(db: AsyncSession, year: int) -> dict:
    row = await get_static_data_row(db, year)
    derived = derive_static_data(
        row.total_expenses if row else None,
        row.total_wages if row else None,
        row.breakeven_gross_revenue if row else None,
    )
    return {
        "year": year,
        **derived,
        "updated_at": row.updated_at.isoformat() if row and row.updated_at else None,
        "updated_by": row.updated_by if row else None,
    }


async def weekly_overhead_for_year(db: AsyncSession, year: int) -> Optional[float]:
    """Overhead (no wages) weekly for the year, or None when it hasn't been entered."""
    return (await get_static_data(db, year))["overhead_weekly"]


async def subcontractor_labor_by_week(db: AsyncSession, year: int) -> dict[str, dict]:
    """Entered subcontractor labor keyed by week-ending date (ISO)."""
    rows = (
        await db.execute(select(SubcontractorWeeklyLabor).where(SubcontractorWeeklyLabor.year == year))
    ).scalars().all()
    return {
        row.week_ending.isoformat(): {
            "total_labor_cost": row.total_labor_cost,
            "head_count": row.head_count,
        }
        for row in rows
    }


def _round(value: Optional[float]) -> Optional[float]:
    return round(value, 2) if value is not None else None

