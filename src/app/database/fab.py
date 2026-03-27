from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import DateTime


class Fab(SQLModel, table=True):
    """FAB table model"""
    __tablename__ = "fabs"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="business_jobs.id")
    fab_type: str = Field(max_length=255)
    sales_person_id: int = Field(foreign_key="users.id")
    stone_type_id: int = Field(foreign_key="stone_types.id")
    stone_color_id: int = Field(foreign_key="stone_colors.id")
    stone_thickness_id: int = Field(foreign_key="stone_thickness.id")
    edge_id: int = Field(foreign_key="edges.id")
    input_area: Optional[str] = Field(default=None)
    total_sqft: float
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    
    # Cost of stone - dollar amount
    cost_of_stone: Optional[float] = Field(default=None)
    
    # Process steps flags
    template_needed: bool = Field(default=True)
    drafting_needed: bool = Field(default=True)
    slab_smith_cust_needed: bool = Field(default=True)
    slab_smith_ag_needed: bool = Field(default=True)
    sct_needed: bool = Field(default=True)
    final_programming_needed: bool = Field(default=True)
    slabsmith_time_minutes: Optional[int] = Field(default=None)

    # Drafter assignment
    drafter_id: Optional[int] = Field(default=None, foreign_key="users.id")
    drafter_assigned_by: Optional[int] = Field(default=None, foreign_key="users.id")
    drafter_assigned_at: Optional[datetime] = None
    
    # Templating/Template tracking
    template_received: bool = Field(default=False)
    template_review_complete: bool = Field(default=False)
    
    # Drafting tracking
    draft_completed: bool = Field(default=False)
    cad_review_complete: bool = Field(default=False)
    no_of_pieces: Optional[int] = Field(default=None)
    
    # Financial tracking
    revenue: Optional[float] = Field(default=None)
    gp: Optional[float] = Field(default=None)  # Gross Profit
    
    # SalesCT tracking
    sct_completed: bool = Field(default=False)
    revised: bool = Field(default=False)  # Indicates if FAB has been sent back for revisions
    
    # Cut List tracking
    shop_date_schedule: Optional[datetime] = None
    final_programming_complete: bool = Field(default=False)
    cutlist_complete: Optional[bool] = Field(default=False, description="Whether cut list has been marked complete, triggering move to shop stage")
    final_programming_completed_date: Optional[datetime] = Field(default=None, description="When final programming was completed")
    slab_smith_used: bool = Field(default=False)
    fp_not_needed: bool = Field(default=False)
    
    # Final Programming tracking
    confirmed_date: Optional[datetime] = None  # When final programming confirmed
    wj_time_minutes: Optional[int] = Field(default=None)  # Waterjet time in minutes
    wj_linft: Optional[float] = Field(default=None)  # Waterjet linear feet
    edging_linft: Optional[float] = Field(default=None)  # Edging linear feet
    cnc_linft: Optional[float] = Field(default=None)  # CNC linear feet
    miter_linft: Optional[float] = Field(default=None)  # Miter linear feet
    installation_date: Optional[datetime] = None
    saw_cut_lnft: Optional[float] = Field(default=None, description="Saw cut linear feet from cutlist")
    
    current_stage: Optional[str] = Field(max_length=255, default=None)
    next_stage: Optional[str] = Field(max_length=255, default=None)
    status_id: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
    cost_of_stone_id: Optional[int] = Field(default=None, foreign_key="cost_of_stones.id")
    slabsmith_completed_date: Optional[datetime] = Field(default=None, description="Date when slabsmith was completed")
    sales_ct_completed_date: Optional[datetime] = Field(default=None, description="Date when sales CT was completed")
    template_completed_date: Optional[datetime] = Field(default=None, description="When templating was completed")
    predraft_completed_date: Optional[datetime] = Field(default=None, description="When pre-draft review was completed")
    draft_completed_date: Optional[datetime] = Field(default=None, description="When drafting was completed")
    revision_completed_date: Optional[datetime] = Field(default=None, description="When revision was completed")
    sct_completed_date: Optional[datetime] = Field(default=None, description="When sales CT was completed (legacy)")
    slab_smith_approved: Optional[bool] = Field(default=None, description="SlabSmith approval status")
    block_drawing_approved: Optional[bool] = Field(default=None, description="Block drawing approval status")

    shop_est_completion_date: Optional[datetime] = Field(default=None, description="Estimated completion date for shop")
