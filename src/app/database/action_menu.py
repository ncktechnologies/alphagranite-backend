from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class ActionMenu(SQLModel, table=True):
    __tablename__ = "action_menus"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    code: str = Field(index=True, max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
