from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class PlanningSection(SQLModel, table=True):
    __tablename__ = "planning_sections"

    id: Optional[int] = Field(default=None, primary_key=True)
    plan_name: str = Field(max_length=255, unique=True, index=True)
    plan_description: Optional[str] = None
    is_active: bool = Field(default=True)
    status_id: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
