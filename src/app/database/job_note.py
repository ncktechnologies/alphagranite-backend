from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlmodel.sql.sqltypes import UTCDateTime  # patched in utils/config to store/return America/Chicago
from src.app.utils.helpers import app_now


class JobNote(SQLModel, table=True):
    __tablename__ = "job_notes"
    
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    job_id: int = Field(foreign_key="business_jobs.id", index=True)
    note: str = Field(index=False)
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(
        default_factory=app_now,
        sa_column=Column(UTCDateTime())
    )
