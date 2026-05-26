from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class InstallerJobTimerSession(SQLModel, table=True):
    __tablename__ = "installer_job_timer_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="business_jobs.id", index=True)
    fab_id: Optional[int] = Field(default=None, foreign_key="fabs.id", index=True)
    installer_id: int = Field(foreign_key="users.id", index=True)
    installer_role: str = Field(default="lead", max_length=20)
    status: str = Field(max_length=20)

    session_start_at: datetime
    current_run_start_at: Optional[datetime] = None
    current_pause_start_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    total_work_seconds: int = Field(default=0)
    total_pause_seconds: int = Field(default=0)
    sqft_installed: Optional[float] = Field(default=None)
    sqft_not_installed: Optional[float] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
