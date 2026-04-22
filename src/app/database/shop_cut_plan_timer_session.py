from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ShopCutPlanTimerSession(SQLModel, table=True):
    __tablename__ = "shop_cut_plan_timer_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    shop_cut_plan_id: int = Field(foreign_key="shop_cut_plans.id")
    operator_id: int = Field(foreign_key="users.id")
    status: str = Field(max_length=20)

    session_start_at: datetime
    current_run_start_at: Optional[datetime] = None
    current_pause_start_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    total_work_seconds: int = Field(default=0)
    total_pause_seconds: int = Field(default=0)
    work_percentage: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
