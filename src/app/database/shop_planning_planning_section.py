from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ShopPlanningPlanningSection(SQLModel, table=True):
    __tablename__ = "shop_planning_planning_sections"

    id: Optional[int] = Field(default=None, primary_key=True)
    shop_planning_id: int = Field(foreign_key="shop_plannings.id")
    planning_section_id: int = Field(foreign_key="planning_sections.id")
    order: int  # Step order for this planning section
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
