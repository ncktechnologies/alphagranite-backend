from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from src.app.utils.helpers import app_now


class PerformanceStaticData(SQLModel, table=True):
    """Yearly figures entered on the Performance page.

    Overhead, breakeven and the derived values (see service/performance_data.py)
    are calculated from these; they feed the labor cost reports and the dashboard.
    """

    __tablename__ = "performance_static_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True, unique=True)
    total_expenses: Optional[float] = Field(default=None, ge=0)
    total_wages: Optional[float] = Field(default=None, ge=0)
    breakeven_gross_revenue: Optional[float] = Field(default=None, ge=0)
    created_at: datetime = Field(default_factory=app_now)
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")


class SubcontractorWeeklyLabor(SQLModel, table=True):
    """Subcontractor installer labor entered per report week (week_ending matches the report's weeks)."""

    __tablename__ = "subcontractor_weekly_labor"

    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True)
    week_ending: date = Field(index=True, unique=True)
    total_labor_cost: Optional[float] = Field(default=None, ge=0)
    head_count: Optional[float] = Field(default=None, ge=0)
    created_at: datetime = Field(default_factory=app_now)
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
