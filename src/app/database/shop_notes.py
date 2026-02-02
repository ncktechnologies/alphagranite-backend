from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ShopNotes(SQLModel, table=True):
    __tablename__ = "shop_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(foreign_key="fabs.id")
    note: str = Field(description="Shop note content")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")