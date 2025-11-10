from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class OperationWorkflow(SQLModel, table=True):
    __tablename__ = "operation_workflow"

    id: Optional[int] = Field(default=None, primary_key=True)
    shop_planning_sections: int = Field(foreign_key="shop_planning_sections.id")
    started_at: datetime
    finished_at: datetime  # Can be pause or completion
    total_sqft_done: str = Field(max_length=255)
    reason_for_pause: str
    notes: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
