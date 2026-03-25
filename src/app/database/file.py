from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class File(SQLModel, table=True):
    __tablename__ = "files"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    file_path: str = Field(max_length=255)
    file_type: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    file_size: str = Field(max_length=255)
    job_id: Optional[int] = Field(default=None, foreign_key="business_jobs.id", index=True)
    task_id: Optional[int] = Field(default=None, foreign_key="shop_cut_plans.id", index=True)
    uploaded_by: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    stage: Optional[str] = Field(default=None, index=True)  # e.g., "drafting" or "revision")
    file_design: Optional[str] = Field(default=None, max_length=255, index=True)
    stage_name: Optional[str] = Field(default=None, max_length=255, index=True)  # e.g., "drafting" or "revision")
