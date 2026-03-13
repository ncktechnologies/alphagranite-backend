from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class ShopCutPlanTimerEvent(SQLModel, table=True):
    __tablename__ = "shop_cut_plan_timer_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="shop_cut_plan_timer_sessions.id")
    shop_cut_plan_id: int = Field(foreign_key="shop_cut_plans.id")
    operator_id: int = Field(foreign_key="users.id")

    action: str = Field(max_length=20)
    event_at: datetime = Field(default_factory=datetime.now)
    note: Optional[str] = None
