from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint
from src.app.utils.helpers import utc_now


class StoneColor(SQLModel, table=True):
    __tablename__ = "stone_colors"
    __table_args__ = (
        UniqueConstraint("stone_type_id", "name", name="uq_stone_colors_type_name"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    stone_type_id: Optional[int] = Field(default=None, foreign_key="stone_types.id", index=True)
    name: str = Field(max_length=255, index=True)
    color_code: Optional[str] = Field(max_length=50, default=None)  # Hex color code
    description: Optional[str] = None
    status_id: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=utc_now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")