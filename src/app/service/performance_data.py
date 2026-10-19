"""Performance-page inputs (yearly static data, weekly subcontractor labor) and
the values derived from them for the reports and the dashboard."""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.performance_data import PerformanceStaticData, SubcontractorWeeklyLabor

# Working days (Mon-Fri) in a full week.
WORK_DAYS_PER_WEEK = 5


def _easter_sunday(year: int) -> date:
    """Western (Gregorian) Easter Sunday - anonymous Gregorian algorithm."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _observed(day: date) -> date:
    """Saturday holidays are taken on the Friday before, Sunday ones on the Monday after."""
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def _previous_weekday(day: date) -> date:
    day -= timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def company_holidays(year: int) -> set[date]:
    """Observed company holidays falling in the year: New Year's Day, Good Friday, Christmas Eve, Christmas Day.

    Christmas Eve is taken on the working day before (observed) Christmas Day, so
    the two never land on the same day. A Saturday New Year's Day is taken on
    Dec 31 of the year before, so it counts in that year.
    """
    christmas = _observed(date(year, 12, 25))
    candidates = {
        _observed(date(year, 1, 1)),
        _observed(date(year + 1, 1, 1)),
        _easter_sunday(year) - timedelta(days=2),
        christmas,
        _previous_weekday(christmas),
    }
    return {day for day in candidates if day.year == year}


def working_days_in_year(year: int) -> int:
    """Mon-Fri days in the year less the company holidays (e.g. 257 for 2026)."""
    first, last = date(year, 1, 1), date(year, 12, 31)
    weekdays = sum(1 for n in range((last - first).days + 1) if (first + timedelta(days=n)).weekday() < 5)
    return weekdays - len(company_holidays(year))


def derive_static_data(
    total_expenses: Optional[float],
    total_wages: Optional[float],
    breakeven_gross_revenue: Optional[float],
    year: int,
) -> dict:
    """Entered figures plus everything calculated from them (None when an input is missing).

    difference (overhead)         = total_expenses - total_wages
    overhead_monthly              = difference / 12
    overhead_weekly               = difference / 52   (overhead per week used by the reports)
    breakeven_gross_profit        = total_expenses / 12
    breakeven_avg_revenue_per_day = breakeven_gross_revenue (monthly) * 12 / working days in the year
    """
    working_days = working_days_in_year(year)
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
        "working_days_per_year": working_days,
        "breakeven_avg_revenue_per_day": _round(
            breakeven_gross_revenue * 12 / working_days if breakeven_gross_revenue is not None else None
        ),
    }


# Dashboard periods -> how many of them fit in a year (breakeven GP is a monthly figure).
_PERIODS_PER_YEAR = {"this_week": 52, "this_month": 12}


def breakeven_gross_profit_for_period(total_expenses: Optional[float], period: str, year: int) -> Optional[float]:
    """Breakeven gross profit scaled to a dashboard period (yearly expenses / periods per year).

    "today" is one working day: yearly expenses / working days in the year.
    """
    if total_expenses is None:
        return None
    if period == "today":
        return total_expenses / working_days_in_year(year)
    if period not in _PERIODS_PER_YEAR:
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
        year,
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

