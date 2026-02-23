from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ShopCutPlan(SQLModel, table=True):
    __tablename__ = "shop_cut_plans"

    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(foreign_key="fabs.id")
    workstation_id: int = Field(foreign_key="work_stations.id")
    planning_section_id: int = Field(foreign_key="planning_sections.id")
    user_id: int = Field(foreign_key="users.id")
    estimated_hours: float = Field(gt=0, description="Estimated hours to complete")
    scheduled_start_date: Optional[datetime] = Field(
        default=None,
        description="Scheduled start date"
    )
    actual_start_date: Optional[datetime] = Field(default=None, description="Actual start date")
    actual_end_date: Optional[datetime] = Field(default=None, description="Actual end date")
    work_percentage: int = Field(default=0, ge=0, le=100, description="Work completion percentage")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")