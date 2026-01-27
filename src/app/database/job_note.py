from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime
from src.app.utils.helpers import utc_now


class JobNote(SQLModel, table=True):
    __tablename__ = "job_notes"
    
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    job_id: int = Field(foreign_key="business_jobs.id", index=True)
    note: str = Field(index=False)
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=False))
    )
