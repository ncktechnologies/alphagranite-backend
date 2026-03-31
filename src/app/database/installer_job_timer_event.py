from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class InstallerJobTimerEvent(SQLModel, table=True):
    __tablename__ = "installer_job_timer_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="installer_job_timer_sessions.id", index=True)
    job_id: int = Field(foreign_key="business_jobs.id", index=True)
    fab_id: Optional[int] = Field(default=None, foreign_key="fabs.id", index=True)
    installer_id: int = Field(foreign_key="users.id", index=True)

    action: str = Field(max_length=20)
    event_at: datetime = Field(default_factory=datetime.now)
    note: Optional[str] = None
