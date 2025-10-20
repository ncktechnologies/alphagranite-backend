from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Permission(SQLModel, table=True):
    __tablename__ = "permissions"
    id: Optional[int] = Field(default=None, primary_key=True)
    can_create: bool = Field(default=False)
    can_update: bool = Field(default=False)
    can_delete: bool = Field(default=False)
    can_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
