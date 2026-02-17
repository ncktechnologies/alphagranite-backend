
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# Copying the class from generated_schemas.py exactly as seen
class ShopPlanningSection(SQLModel, table=True):
    __tablename__ = "shop_planning_sections"
    id: Optional[int] = Field(default=None, primary_key=True)
    work_station_id: int = Field()
    operator_ids: Optional[str] = Field(default=None)
    machine: Optional[str] = Field(default=None)
    scheduled_sqft: Optional[str] = Field(default=None)
    completed_sqft: Optional[str] = Field(default=None)
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)

try:
    print("Attempting to instantiate ShopPlanningSection with mismatched args...")
    section = ShopPlanningSection(
        planning_section_id=1,
        workstation_ids="1,2",
        total_sqft=100.0,
        machine_ids="1,2",
        operator_ids="2",
        note="Some note",
        scheduled_hours="10",
        fab_id=1,
        created_by=1
    )
    print("Instantiation SUCCESS")
    print(section)
except Exception as e:
    print(f"Instantiation FAILED: {e}")
