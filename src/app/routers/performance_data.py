"""Performance page inputs: yearly static data and weekly subcontractor labor."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.performance_data import PerformanceStaticData, SubcontractorWeeklyLabor
from src.app.database.user import User
from src.app.interface.response_wrappers import SuccessResponse, success_response
from src.app.middleware.jwt_auth import get_current_user
from src.app.routers.reports import _week_windows_for_month
from src.app.service.performance_data import get_static_data, get_static_data_row, subcontractor_labor_by_week
from src.app.utils.helpers import app_now, error_response

router = APIRouter()

# Report weeks end on Friday (the labor cost reports' default week_ending_weekday).
REPORT_WEEK_ENDING_WEEKDAY = 4


class StaticDataUpdate(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    total_expenses: Optional[float] = Field(None, ge=0)
    total_wages: Optional[float] = Field(None, ge=0)
    breakeven_gross_revenue: Optional[float] = Field(None, ge=0)


class SubcontractorWeek(BaseModel):
    week_ending: date
    total_labor_cost: Optional[float] = Field(None, ge=0)
    head_count: Optional[float] = Field(None, ge=0)


class SubcontractorLaborUpdate(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    weeks: list[SubcontractorWeek]


def report_weeks_for_year(year: int) -> list[dict]:
    """The labor cost reports' weeks for a year (month-end partial weeks included), in order."""
    weeks = []
    for month in range(1, 13):
        for window in _week_windows_for_month(year, month, REPORT_WEEK_ENDING_WEEKDAY):
            weeks.append({
                "week_ending": window["week_end"].isoformat(),
                "week_start": window["overlap_start"].isoformat(),
                "month_number": month,
                "number_of_days": window["number_of_days"],
            })
    return weeks


@router.get("/performance/static-data", response_model=SuccessResponse[dict])
async def get_performance_static_data(
    year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Static data for a year: entered values plus overhead and breakeven figures calculated from them."""
    return success_response(await get_static_data(db, year), "Performance static data retrieved")


@router.put("/performance/static-data", response_model=SuccessResponse[dict])
async def update_performance_static_data(
    payload: StaticDataUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save the entered static data for a year (creates the year's record if needed)."""
    row = await get_static_data_row(db, payload.year)
    if row is None:
        row = PerformanceStaticData(year=payload.year)
        db.add(row)
    row.total_expenses = payload.total_expenses
    row.total_wages = payload.total_wages
    row.breakeven_gross_revenue = payload.breakeven_gross_revenue
    row.updated_at = app_now()
    row.updated_by = current_user.id
    await db.commit()
    return success_response(await get_static_data(db, payload.year), "Performance static data saved")


@router.get("/performance/subcontractor-labor", response_model=SuccessResponse[dict])
async def get_subcontractor_labor(
    year: int = Query(..., ge=2000, le=2100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Every report week of the year with the subcontractor labor entered for it (null when not entered)."""
    entered = await subcontractor_labor_by_week(db, year)
    weeks = [
        {
            **week,
            "total_labor_cost": entered.get(week["week_ending"], {}).get("total_labor_cost"),
            "head_count": entered.get(week["week_ending"], {}).get("head_count"),
        }
        for week in report_weeks_for_year(year)
    ]
    return success_response({"year": year, "weeks": weeks}, "Subcontractor labor retrieved")


@router.put("/performance/subcontractor-labor", response_model=SuccessResponse[dict])
async def update_subcontractor_labor(
    payload: SubcontractorLaborUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save subcontractor labor for the given weeks. A week with both values empty is cleared."""
    valid_weeks = {week["week_ending"] for week in report_weeks_for_year(payload.year)}
    invalid = sorted(w.week_ending.isoformat() for w in payload.weeks if w.week_ending.isoformat() not in valid_weeks)
    if invalid:
        raise error_response(
            f"Not report weeks of {payload.year}: {', '.join(invalid)}. Use the week_ending dates returned by GET.", 422
        )

    existing = {
        row.week_ending: row
        for row in (
            await db.execute(
                select(SubcontractorWeeklyLabor).where(
                    SubcontractorWeeklyLabor.week_ending.in_([w.week_ending for w in payload.weeks])
                )
            )
        ).scalars().all()
    }
    now = app_now()
    for week in payload.weeks:
        row = existing.get(week.week_ending)
        if week.total_labor_cost is None and week.head_count is None:
            if row is not None:
                await db.delete(row)
            continue
        if row is None:
            row = SubcontractorWeeklyLabor(year=payload.year, week_ending=week.week_ending)
            db.add(row)
        row.total_labor_cost = week.total_labor_cost
        row.head_count = week.head_count
        row.updated_at = now
        row.updated_by = current_user.id
    await db.commit()
    return await get_subcontractor_labor(year=payload.year, db=db, current_user=current_user)
