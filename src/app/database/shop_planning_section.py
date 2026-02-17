# from datetime import datetime
# from typing import Optional
# from sqlmodel import SQLModel, Field


# class ShopPlanningSection(SQLModel, table=True):
#     __tablename__ = "shop_planning_sections"

#     id: Optional[int] = Field(default=None, primary_key=True)
#     shop_planning_planning_section_id: int = Field(foreign_key="shop_planning_planning_sections.id")
#     work_station_id: int = Field(foreign_key="work_stations.id")
#     operator_ids: str  # JSON string of operator user IDs
#     order_no: int  # Execution order
#     machine: str = Field(max_length=255)
#     notes: Optional[str] = None
#     scheduled_duration_minutes: int
#     required_sqft: str = Field(max_length=255)
#     completed_sqft: Optional[str] = Field(default=None, max_length=255)
#     no_of_pieces: Optional[str] = Field(default=None, max_length=255)
#     operator_duration: Optional[str] = Field(default=None, max_length=255)
#     start_date: Optional[datetime] = None
#     end_date: Optional[datetime] = None
#     status_id: int = Field(foreign_key="status.value_id")
#     created_at: datetime = Field(default_factory=datetime.now)
#     updated_at: Optional[datetime] = None
#     updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
