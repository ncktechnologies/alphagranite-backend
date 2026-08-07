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
    review_checklist: Optional[dict] = Field(default=None, sa_column=Column(JSONB), description="FAB review checklist with checkbox states")
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
    # created_at: datetime = Field()
    # updated_at: Optional[datetime] = Field(default=None)
    # curremt_stage: str = Field(description="equivalent to the table name of the process e.g templatings")

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

class PlanningSection(SQLModel, table=True):
    __tablename__ = "planning_sections"

    id: Optional[int] = Field(default=None, primary_key=True)
    plan_name: str = Field(max_length=255, unique=True, index=True)
    plan_description: Optional[str] = None
    is_active: bool = Field(default=True)
    status_id: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")


class HcpPayrollSourceConfig(SQLModel, table=True):
    __tablename__ = "hcp_payroll_source_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True, index=True)
    base_url: str = Field(default="https://secure.saashr.com", max_length=255)
    company_id: str = Field(default="83943830", max_length=100, index=True)
    grant_type: str = Field(default="client_credentials", max_length=100)
    client_id: Optional[str] = Field(default=None, max_length=255)
    client_secret: Optional[str] = Field(default=None, max_length=255)
    report_settings_id: str = Field(default="89798180", max_length=100, index=True)
    schedule_type: str = Field(default="weekly", max_length=50)
    schedule_interval: int = Field(default=1)
    schedule_weekday: int = Field(default=0)
    schedule_hour: int = Field(default=1)
    schedule_minute: int = Field(default=0)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")


class HcpPayrollIngestionRun(SQLModel, table=True):
    __tablename__ = "hcp_payroll_ingestion_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_config_id: int = Field(foreign_key="hcp_payroll_source_configs.id", index=True)
    status: str = Field(default="running", max_length=50, index=True)
    token_request_url: Optional[str] = Field(default=None, max_length=500)
    token_response_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    token_acquired_at: Optional[datetime] = Field(default=None)
    token_expires_in: Optional[int] = Field(default=None)
    report_request_url: Optional[str] = Field(default=None, max_length=500)
    report_http_status: Optional[int] = Field(default=None)
    report_content_type: Optional[str] = Field(default=None, max_length=255)
    error_message: Optional[str] = Field(default=None)
    row_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime] = Field(default=None)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")


class HcpPayrollReportSnapshot(SQLModel, table=True):
    __tablename__ = "hcp_payroll_report_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_config_id: int = Field(foreign_key="hcp_payroll_source_configs.id", index=True)
    ingestion_run_id: int = Field(foreign_key="hcp_payroll_ingestion_runs.id", index=True)
    report_settings_id: str = Field(max_length=100, index=True)
    report_title: Optional[str] = Field(default=None, max_length=255)
    payload_format: str = Field(default="text", max_length=50)
    raw_payload_text: str = Field()
    row_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)


class HcpPayrollReportRow(SQLModel, table=True):
    __tablename__ = "hcp_payroll_report_rows"

    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_id: int = Field(foreign_key="hcp_payroll_report_snapshots.id", index=True)
    source_config_id: int = Field(foreign_key="hcp_payroll_source_configs.id", index=True)
    ingestion_run_id: int = Field(foreign_key="hcp_payroll_ingestion_runs.id", index=True)
    row_kind: str = Field(max_length=50, index=True)
    row_index: int = Field(index=True)
    cost_center_name: Optional[str] = Field(default=None, max_length=255, index=True)
    employee_first_name: Optional[str] = Field(default=None, max_length=255, index=True)
    employee_last_name: Optional[str] = Field(default=None, max_length=255, index=True)
    hourly_pay: Optional[float] = Field(default=None)
    regular_hours: Optional[float] = Field(default=None)
    holiday_hours: Optional[float] = Field(default=None)
    pto_hours: Optional[float] = Field(default=None)
    total_reg_pto_hol_wages: Optional[float] = Field(default=None)
    overtime_hours: Optional[float] = Field(default=None)
    total_ot_wages: Optional[float] = Field(default=None)
    raw_line_text: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)

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
    fab_id: int = Field(foreign_key="fabs.id", index=True)
    revision_type: str = Field(description="Type of revision needed")
    requested_by: int = Field()
    assigned_to: Optional[int] = Field(default=None)
    scheduled_start_date: Optional[datetime] = Field(default=None)
    scheduled_end_date: Optional[datetime] = Field(default=None)
    actual_start_date: Optional[datetime] = Field(default=None)
    actual_end_date: Optional[datetime] = Field(default=None)
    revision_reason: Optional[str] = Field(default=None)
    revision_notes: Optional[str] = Field(default=None)
    department: Optional[str] = Field(default=None, max_length=255)
    person_name: Optional[str] = Field(default=None, max_length=255)
    is_completed: bool = Field(default=False)
    status_id: int = Field()
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)
    file_ids: Optional[str] = Field(default=None)


# --- Shop Revisions ---
class ShopRevision(SQLModel, table=True):
    __tablename__ = "shop_revisions"
    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(foreign_key="fabs.id", index=True)
    revision_note: str = Field(description="Shop revision note")
    requested_by: int = Field(foreign_key="users.id")
    assigned_to: Optional[int] = Field(default=None, foreign_key="users.id")
    revision_feedback: Optional[str] = Field(default=None)
    revision_completed: bool = Field(default=False, index=True)
    completed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
    file_ids: Optional[str] = Field(default=None, description="Comma-separated file IDs")

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
    extra_crew_1_id: Optional[int] = Field(default=None)
    extra_crew_2_id: Optional[int] = Field(default=None)
    extra_crew_3_id: Optional[int] = Field(default=None)
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


# --- SlabSmith Sessions ---
class SlabSmithSession(SQLModel, table=True):
    __tablename__ = "slab_smith_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(index=True)
    user_id: int = Field()
    status: str = Field(default="active")  # active, paused, completed

    session_start_time: datetime = Field()
    session_end_time: Optional[datetime] = Field(default=None)
    current_pause_start_time: Optional[datetime] = Field(default=None)
    total_pause_duration: int = Field(default=0)  # in seconds
    total_time_spent: int = Field(default=0)  # in seconds

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)


class SlabSmithSessionNote(SQLModel, table=True):
    __tablename__ = "slab_smith_session_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True)
    fab_id: int = Field(index=True)
    user_id: int = Field()
    action: str = Field()  # start, pause, resume, end
    timestamp: datetime = Field()
    note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


# --- Final Programming Sessions ---
class FinalProgrammingSession(SQLModel, table=True):
    __tablename__ = "final_programming_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(index=True)
    user_id: int = Field()
    status: str = Field(default="active")  # active, paused, completed

    session_start_time: datetime = Field()
    session_end_time: Optional[datetime] = Field(default=None)
    current_pause_start_time: Optional[datetime] = Field(default=None)
    total_pause_duration: int = Field(default=0)  # in seconds
    total_time_spent: int = Field(default=0)  # in seconds

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)


class FinalProgrammingSessionNote(SQLModel, table=True):
    __tablename__ = "final_programming_session_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True)
    fab_id: int = Field(index=True)
    user_id: int = Field()
    action: str = Field()  # start, pause, resume, end
    timestamp: datetime = Field()
    note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


# --- CNC Drafting ---
class CNCDrafting(SQLModel, table=True):
    __tablename__ = "cnc_draftings"
    id: Optional[int] = Field(default=None, primary_key=True)
    drafter_id: int = Field()
    fab_id: int = Field(foreign_key="fabs.id", unique=True)
    scheduled_start_date: datetime = Field()
    scheduled_end_date: datetime = Field()
    drafter_start_date: Optional[datetime] = Field(default=None)
    drafter_end_date: Optional[datetime] = Field(default=None)
    status_id: int = Field(default=1)
    total_sqft: Optional[float] = Field(default=None)
    no_of_pieces: Optional[int] = Field(default=None)
    cad_review_complete: Optional[bool] = Field(default=False)
    draft_completed: Optional[bool] = Field(default=False)
    notes: Optional[str] = Field(default=None)
    current_stage: Optional[str] = Field(default=None)
    total_sqft_required_to_draft: str = Field()
    total_sqft_drafted: Optional[float] = Field(default=None)
    no_of_piece_drafted: Optional[int] = Field(default=None)
    draft_note: Optional[str] = Field(default=None)
    mentions: Optional[str] = Field(default=None, description="List of user_ids of user to be notified")
    total_hours_drafted: Optional[float] = Field(default=None)
    is_completed: bool = Field(default=False)
    file_ids: Optional[str] = Field(default=None)
    created_at: datetime = Field()
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None)


# --- CNC Drafting Sessions ---
class CNCDraftingSession(SQLModel, table=True):
    __tablename__ = "cnc_drafting_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(index=True)
    drafter_id: int = Field()
    status: str = Field(default="drafting")  # drafting, paused, on_hold, completed

    session_start_time: datetime = Field()
    session_end_time: Optional[datetime] = Field(default=None)
    current_pause_start_time: Optional[datetime] = Field(default=None)
    total_pause_duration: int = Field(default=0)
    total_time_spent: int = Field(default=0)

    cumulative_sqft_drafted: Optional[str] = Field(default="0")
    work_percentage_done: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)


class CNCDraftingSessionNote(SQLModel, table=True):
    __tablename__ = "cnc_drafting_session_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True)
    fab_id: int = Field(index=True)
    action: str = Field()  # start, pause, resume, on_hold, end
    timestamp: datetime = Field()
    note: Optional[str] = Field(default=None)
    sqft_drafted: Optional[str] = Field(default=None)
    work_percentage_done: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
