from typing import Optional
from sqlmodel import SQLModel, Field

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    account_id: int
    job_id: str
    status_id: int
    created_by: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
