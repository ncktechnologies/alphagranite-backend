from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class StoneThickness(SQLModel, table=True):
    __tablename__ = "stone_thickness"

    id: Optional[int] = Field(default=None, primary_key=True)
    thickness: str = Field(max_length=100, unique=True, index=True)  # e.g., "3/4 inch", "1.25 inch"
    thickness_mm: Optional[float] = None  # Thickness in millimeters for calculations
    description: Optional[str] = None
    status_id: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")