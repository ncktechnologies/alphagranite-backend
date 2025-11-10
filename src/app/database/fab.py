from typing import Optional
from sqlmodel import SQLModel, Field

class Fab(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int
    fab_type: str
    stone_type: str
    stone_color: str
    stone_thickness: str
    area: str
    edge: str
    total_sqft: float
    notes: Optional[str] = None
    sales_person_id: int
    steps: str
    status: str
    created_by: int
