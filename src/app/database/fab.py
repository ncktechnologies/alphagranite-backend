from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Fab(SQLModel, table=True):
    __tablename__ = "fabs"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="business_jobs.id")
    fab_type: str = Field(max_length=255)
    sales_person_id: int = Field(foreign_key="users.id")
    stone_type_id: int = Field(foreign_key="stone_types.id")
    stone_color_id: int = Field(foreign_key="stone_colors.id")
    stone_thickness_id: int = Field(foreign_key="stone_thickness.id")
    edge_id: int = Field(foreign_key="edges.id")
    input_area: str = Field(max_length=255)
    total_sqft: float
    notes: Optional[str] = None
    
    # Process steps flags
    template_needed: bool = Field(default=True)
    drafting_needed: bool = Field(default=True)
    slab_smith_cust_needed: bool = Field(default=True)
    slab_smith_ag_needed: bool = Field(default=True)
    sct_needed: bool = Field(default=True)
    final_programming_needed: bool = Field(default=True)
    
    current_stage: Optional[str] = Field(max_length=255, default=None)
    next_stage: Optional[str] = Field(max_length=255, default=None)
    status_id: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
