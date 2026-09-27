from typing import Optional
from datetime import datetime
from src.app.utils.helpers import utc_now
from sqlmodel import SQLModel, Field

class Status(SQLModel, table=True):
    __tablename__ = "status"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    value_id: int = Field(unique=True)
