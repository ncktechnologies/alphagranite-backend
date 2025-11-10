from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class WorkStation(SQLModel, table=True):
    __tablename__ = "work_stations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True, index=True)
    planning_sections_id: int = Field(foreign_key="planning_sections.id")
    status_id: int = Field(foreign_key="status.value_id")
    operatives_ids: str  # JSON string of user IDs
    machine_list: str  # JSON string of machines
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
