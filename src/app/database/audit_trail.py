from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class AuditTrail(SQLModel, table=True):
    __tablename__ = "audit_trails"

    id: Optional[int] = Field(default=None, primary_key=True)
    activity_message: str
    user_id: int = Field(foreign_key="users.id")
    activity_table_name: Optional[str] = Field(default=None, max_length=255)
    record_id: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
