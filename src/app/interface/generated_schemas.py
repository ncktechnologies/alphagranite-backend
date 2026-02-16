from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB

# --- Jobs ---
# Note: Job model removed to avoid conflict with src.app.database.job
# Import Job from src.app.database.job if needed

# --- Templatings ---
class Templating(SQLModel, table=True):
    __tablename__ = "templatings"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    technician_id: Optional[int] = Field(default=None)
    schedule_start_date: Optional[datetime] = Field(default=None)
    schedule_due_date: Optional[datetime] = Field(default=None)
    total_sqft: Optional[str] = Field(default=None)
    actual_start_date: Optional[datetime] = Field(default=None)
    actual_end_date: Optional[datetime] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    is_templating_schedule: bool = Field(default=False, description="Is templating scheduled")
    rescheduled: bool = Field(default=False, description="Was this templating rescheduled after unscheduling")
    is_completed: Optional[bool] = Field(default=None)  
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)

# --- Slab Smiths ---
class SlabSmith(SQLModel, table=True):
    __tablename__ = "slab_smiths"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    slab_smith_type: str = Field()
    drafter_id: int = Field()
    status_id: int = Field()
    start_date: datetime = Field()
    end_date: Optional[datetime] = Field(default=None)
    total_sqft_completed: Optional[str] = Field(default=None)
    is_completed: bool = Field(default=False)
    slabsmith_completed_date: Optional[datetime] = Field(default=None)
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    file_ids: Optional[str] = Field(default=None)

# --- Shop Planning ---
class ShopPlanning(SQLModel, table=True):
    __tablename__ = "shop_planning"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    description: Optional[str] = Field(default=None)
    status_id: int = Field()
    created_by: int = Field()
    updated_by: Optional[int] = Field(default=None)
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)

class PlanningSection(SQLModel, table=True):
    __tablename__ = "planning_sections"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    description: Optional[str] = Field(default=None)
    status_id: int = Field()
    created_by: int = Field()
    updated_by: Optional[int] = Field(default=None)
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)


# # --- WorkStations ---
# class WorkStation(SQLModel, table=True):
#     __tablename__ = "work_stations"
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field()
#     description: Optional[str] = Field(default=None)
#     status_id: int = Field()
#     created_by: int = Field()
#     updated_by: Optional[int] = Field(default=None)
#     created_at: datetime = Field()
#     updated_at: Optional[datetime] = Field(default=None)



# --- Fabs ---
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    curremt_stage: str = Field(description="equivalent to the table name of the process e.g templatings")

# --- Stone Types ---

# --- Accounts ---

# --- Draftings ---
class Drafting(SQLModel, table=True):
    __tablename__ = "draftings"
    id: Optional[int] = Field(default=None, primary_key=True)
    drafter_id: int = Field()
    fab_id: int = Field(foreign_key="fabs.id", unique=True)  # ← Add unique=True
    scheduled_start_date: datetime = Field()
    scheduled_end_date: datetime = Field()
    drafter_start_date: Optional[datetime] = Field(default=None)
    drafter_end_date: Optional[datetime] = Field(default=None)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    file_ids: Optional[str] = Field(default=None, description="stores a list of differrent file id that belongs to this drafting, each pointing to a file on the files table")
    no_of_piece_drafted: Optional[int] = Field(default=None)
    total_sqft_required_to_draft: str = Field()
    total_sqft_drafted: Optional[float] = Field(default=None)
    draft_note: Optional[str] = Field(default=None)
    mentions: Optional[str] = Field(default=None, description="List of user_ids of user to be notified of the draft submission")
    total_hours_drafted: Optional[float] = Field(default=None, description="Total number of hours spent on drafting")
    is_redrafting: bool = Field(default=False)
    is_completed: bool = Field(default=False)

# --- Pre Draft Reviews ---
class PreDraftReview(SQLModel, table=True):
    __tablename__ = "pre_draft_reviews"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    draft_notes: str = Field()
    is_redrafting_needed: int = Field()
    is_completed: bool = Field(default=False)
    created_at: datetime = Field()
    updated_by: int = Field()
    updated_at: datetime = Field()
    status_id: Optional[int] = Field(default=None)

# --- Sales CTs ---
class SalesCT(SQLModel, table=True):
    __tablename__ = "sales_cts"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(foreign_key="fabs.id", unique=True)  # ← Add unique=True
    revision_type: Optional[str] = Field(default=None)  # <-- add this
    is_revision_needed: bool = Field()
    is_revision_completed: Optional[bool] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    no_of_revisions: Optional[str] = Field(default=None)
    current_revision_count: Optional[str] = Field(default=None)
    revision_reason: Optional[str] = Field(default=None)
    slab_smith_type: str = Field()
    drafter_id: int = Field()
    status_id: int = Field()
    start_date: datetime = Field()
    end_date: datetime = Field()
    total_sqft_completed: Optional[str] = Field(default=None)
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    file_ids: Optional[str] = Field(default=None, description="stores a list of differrent file id that belongs to this drafting, each pointing to a file on the files table")

# --- Cut List ---
class CutList(SQLModel, table=True):
    __tablename__ = "cut_list"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    is_final_progreamming_completed: bool = Field(default=False)
    is_completed: bool = Field(default=False)
    shop_schedule_date: Optional[datetime] = Field(default=None)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    no_of_piece: Optional[str] = Field(default=None)
    total_sqft: Optional[str] = Field(default=None)
    installation_date: Optional[datetime] = Field(default=None)
    Ln_ft_map: Optional[str] = Field(default=None, description="contains the map of key value pair of Lnft e.g water jet Ln ft and so on")

# --- Job Technician Workflows ---
class JobTechnicianWorkflow(SQLModel, table=True):
    __tablename__ = "job_technician_workflows"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    technician_id: int = Field()
    table_name: str = Field(description="templating")
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    pause_reason: Optional[str] = Field(default=None)
    total_sqft_done: str = Field()
    started_at: datetime = Field()
    completed_at: datetime = Field(description="this is is when workflow finished , it may be that the only fabid was puase or the  section was done")
    table_id: int = Field(description="related to the id for the table_name")
    created_at: datetime = Field()
    created_by: int = Field()

# --- Final Programmings ---
class FinalProgramming(SQLModel, table=True):
    __tablename__ = "final_programmings"
    id: Optional[int] = Field(default=None, primary_key=True)
    drafter_id: int = Field()
    fab_id: int = Field()
    scheduled_start_date: datetime = Field()
    scheduled_end_date: datetime = Field()
    drafter_start_date: Optional[datetime] = Field(default=None)
    drafter_end_date: Optional[datetime] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    file_ids: Optional[str] = Field(default=None, description="stores a list of differrent file id that belongs to this drafting, each pointing to a file on the files table")
    no_of_piece_drafted: Optional[str] = Field(default=None)
    total_sqft_required_to_draft: str = Field()
    total_sqft_drafted: Optional[str] = Field(default=None)
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))

# --- Shop Planning Sections ---
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

# --- Operation Workflow ---
class OperationWorkflow(SQLModel, table=True):
    __tablename__ = "operation_workflow"
    id: Optional[int] = Field(default=None, primary_key=True)
    shop_planning_sections: int = Field()
    started_at: datetime = Field()
    finished_at: datetime = Field()
    total_sqft_done: str = Field()
    reason_for_pause: str = Field()
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)

# --- WJ Programming ---
class WJProgramming(SQLModel, table=True):
    __tablename__ = "wj_programmings"
    id: Optional[int] = Field(default=None, primary_key=True)
    drafter_id: int = Field()
    fab_id: int = Field()
    scheduled_start_date: datetime = Field()
    scheduled_end_date: datetime = Field()
    drafter_start_date: Optional[datetime] = Field(default=None)
    drafter_end_date: Optional[datetime] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    file_ids: Optional[str] = Field(default=None, description="stores a list of different file ids that belongs to this programming")
    no_of_pieces: Optional[str] = Field(default=None)
    total_ln_ft: Optional[str] = Field(default=None)
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))

# --- WJ Scheduling ---
class WJScheduling(SQLModel, table=True):
    __tablename__ = "wj_schedulings"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    technician_id: Optional[int] = Field(default=None)
    scheduled_start_date: Optional[datetime] = Field(default=None)
    scheduled_end_date: Optional[datetime] = Field(default=None)
    actual_start_date: Optional[datetime] = Field(default=None)
    actual_end_date: Optional[datetime] = Field(default=None)
    total_ln_ft: Optional[str] = Field(default=None)
    completed_ln_ft: Optional[str] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))

# --- Resurface Scheduling ---
class ResurfaceScheduling(SQLModel, table=True):
    __tablename__ = "resurface_schedulings"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    technician_id: Optional[int] = Field(default=None)
    scheduled_start_date: Optional[datetime] = Field(default=None)
    scheduled_end_date: Optional[datetime] = Field(default=None)
    actual_start_date: Optional[datetime] = Field(default=None)
    actual_end_date: Optional[datetime] = Field(default=None)
    total_sqft: Optional[str] = Field(default=None)
    completed_sqft: Optional[str] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))

# --- Revisions ---
class Revision(SQLModel, table=True):
    __tablename__ = "revisions"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(foreign_key="fabs.id", unique=True)  # ← Add unique=True
    revision_type: str = Field(description="Type of revision needed")
    requested_by: int = Field()
    assigned_to: Optional[int] = Field(default=None)
    scheduled_start_date: Optional[datetime] = Field(default=None)
    scheduled_end_date: Optional[datetime] = Field(default=None)
    actual_start_date: Optional[datetime] = Field(default=None)
    actual_end_date: Optional[datetime] = Field(default=None)
    revision_notes: Optional[str] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    file_ids: Optional[str] = Field(default=None)

# --- Cost of Stone ---
class CostOfStone(SQLModel, table=True):
    __tablename__ = "cost_of_stones"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    stone_color_id: Optional[int] = Field(default=None)
    stone_type_id: Optional[int] = Field(default=None)
    total_sqft: Optional[str] = Field(default=None)
    cost_per_sqft: Optional[str] = Field(default=None)
    total_cost: Optional[str] = Field(default=None)
    waste_percentage: Optional[str] = Field(default=None)
    calculated_by: Optional[int] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))

# --- Install Scheduling ---
class InstallScheduling(SQLModel, table=True):
    __tablename__ = "install_schedulings"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    installer_id: Optional[int] = Field(default=None)
    scheduled_install_date: Optional[datetime] = Field(default=None)
    scheduled_end_date: Optional[datetime] = Field(default=None)
    actual_install_date: Optional[datetime] = Field(default=None)
    total_sqft: Optional[str] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    notes: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))

# --- Install Completion ---
class InstallCompletion(SQLModel, table=True):
    __tablename__ = "install_completions"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field()
    installer_id: int = Field()
    install_date: datetime = Field()
    completion_date: datetime = Field()
    total_sqft_installed: Optional[str] = Field(default=None)
    customer_signature: Optional[str] = Field(default=None, description="Path to signature file or signature data")
    completion_notes: Optional[str] = Field(default=None)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    file_ids: Optional[str] = Field(default=None, description="Photos or documents from installation")

# --- Drafting Sessions ---
class DraftingSession(SQLModel, table=True):
    __tablename__ = "drafting_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(index=True)
    drafter_id: int = Field()
    status: str = Field(default="drafting")  # drafting, paused, on_hold, completed
    
    # Session timing
    session_start_time: datetime = Field()
    session_end_time: Optional[datetime] = Field(default=None)
    current_pause_start_time: Optional[datetime] = Field(default=None)
    total_pause_duration: int = Field(default=0)  # in seconds
    total_time_spent: int = Field(default=0)  # in seconds (excluding pauses)
    
    # Progress tracking
    cumulative_sqft_drafted: Optional[str] = Field(default="0")
    work_percentage_done: int = Field(default=0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)


class DraftingSessionNote(SQLModel, table=True):
    __tablename__ = "drafting_session_notes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True)
    fab_id: int = Field(index=True)
    action: str = Field()  # start, pause, resume, on_hold, end
    timestamp: datetime = Field()
    note: Optional[str] = Field(default=None)
    sqft_drafted: Optional[str] = Field(default=None)
    work_percentage_done: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
