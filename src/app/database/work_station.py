from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB

class WorkStation(SQLModel, table=True, extend_existing=True):
    __tablename__ = "work_stations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True, index=True)
    is_active: bool = Field(default=True)
    attendance_required: bool = Field(default=False)
    status_id: int = Field(foreign_key="status.value_id")
    planning_section_id: Optional[int] = Field(default=None, foreign_key="planning_sections.id")
    operator_ids: Optional[List[int]] = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
