from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel
from src.app.utils.helpers import app_now


class Notification(SQLModel, table=True):
    """In-app (bell) notification for one user. Reading it removes it from the tray;
    the row is kept so the user's history stays available."""

    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    event: str = Field(max_length=64, index=True)
    title: str = Field(max_length=255)
    message: str = Field(max_length=1000)
    fab_id: Optional[int] = Field(default=None, foreign_key="fabs.id", index=True)
    job_id: Optional[int] = Field(default=None)
    is_read: bool = Field(default=False, index=True)
    read_at: Optional[datetime] = Field(default=None)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=app_now, index=True)
