from typing import Optional, List, Any
from datetime import datetime
from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field

class AuditTrail(SQLModel, table=True):
    __tablename__ = "audit_trails"

    id: Optional[int] = Field(default=None, primary_key=True)
    activity_message: str
    operation: Optional[str] = Field(default=None, max_length=50)
    user_id: int = Field(foreign_key="users.id")
    resource_type: Optional[str] = Field(default=None, max_length=100)
    activity_table_name: Optional[str] = Field(default=None, max_length=255)
    record_id: Optional[int] = Field(default=None)
    changed_fields: Optional[List[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    old_values: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    new_values: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    request_path: Optional[str] = Field(default=None, max_length=500)
    request_method: Optional[str] = Field(default=None, max_length=10)
    response_status_code: Optional[int] = Field(default=None)
    device_id: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    browser: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
