from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    job_number: str = Field(max_length=100, unique=True, index=True)
    account_id: int = Field(foreign_key="accounts.id")
    description: Optional[str] = None
    priority: Optional[str] = Field(max_length=50, default="Medium")  # Low, Medium, High, Urgent
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status_id: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
