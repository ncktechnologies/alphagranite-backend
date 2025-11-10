from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True, index=True)
    account_number: Optional[str] = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = None
    contact_person: Optional[str] = Field(max_length=255)
    email: Optional[str] = Field(max_length=255)
    phone: Optional[str] = Field(max_length=50)
    address: Optional[str] = None
    status_id: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")