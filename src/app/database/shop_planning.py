from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ShopPlanning(SQLModel, table=True):
    __tablename__ = "shop_plannings"

    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int
    start_date: datetime
    no_of_steps_needed: int
    status_id: int = Field(foreign_key="status.value_id")
    completed_steps: int = Field(default=0)
    current_steps: int
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
