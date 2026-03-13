from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import List, Optional
from datetime import datetime


class FabPlanResponse(BaseModel):
    id: int
    fab_id: int
    fab_type: Optional[str] = None
    workstation_id: Optional[int] = None
    workstation_name: Optional[str] = None
    planning_section_id: Optional[int] = None
    plan_name: Optional[str] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    estimated_hours: Optional[float] = None
    scheduled_start_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    work_percentage: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Job Schemas
class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Job name")
    job_number: str = Field(..., min_length=1, max_length=100, description="Unique job number")
    account_id: int = Field(..., gt=0, description="Account ID")
    project_value: Optional[float] = Field(None, ge=0, description="Project value/amount")
    sales_person_id: Optional[int] = Field(None, gt=0, description="Sales person ID")
    need_to_invoice: bool = False
    priority: Optional[str] = Field(None, description="Job priority (e.g., 'Low', 'Medium', 'High')")
    invoice_note: Optional[str] = Field(None, description="Note regarding invoicing")
    sq_ft: Optional[float] = Field(None, description="Square footage")
    description: Optional[str] = Field(None, description="Job description")
    due_date: Optional[datetime] = Field(None, description="Job due date")



class JobUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    job_number: Optional[str] = Field(None, min_length=1, max_length=100)
    project_value: Optional[float] = Field(None, ge=0)
    account_id: Optional[int] = None
    status_id: Optional[int] = None
    sales_person_id: Optional[int] = None
    need_to_invoice: Optional[bool] = None
    priority: Optional[str] = Field(None, description="Job priority (e.g., 'Low', 'Medium', 'High')")
    invoice_note: Optional[str] = Field(None, description="Note regarding invoicing")
    sq_ft: Optional[float] = None
    description: Optional[str] = Field(None, description="Job description")
    due_date: Optional[datetime] = Field(None, description="Job due date")
    
class JobNoteResponse(BaseModel):
    id: int
    note: str
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    
class JobResponse(BaseModel):
    id: int
    name: str
    job_number: str
    account_id: Optional[int] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    account_contact_person: Optional[str] = None
    account_email: Optional[str] = None
    account_phone: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    project_value: Optional[float] = None
    sales_person_id: Optional[int] = None
    sq_ft: Optional[float] = None
    sales_person_name: Optional[str] = None
    status_id: int
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    need_to_invoice: Optional[bool] = None
    notes: List[JobNoteResponse] = []
    plans: List[FabPlanResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Account Schemas
class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    account_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    status_id: Optional[int] = None


class AccountResponse(BaseModel):
    id: int
    name: str
    account_number: Optional[str]
    description: Optional[str]
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    status_id: int
    total_jobs: Optional[int] = 0
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Stone Thickness Schemas
class StoneThicknessCreate(BaseModel):
    thickness: str = Field(..., min_length=1, max_length=100)
    thickness_mm: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None


class StoneThicknessUpdate(BaseModel):
    thickness: Optional[str] = Field(None, min_length=1, max_length=100)
    thickness_mm: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    status_id: Optional[int] = None


class StoneThicknessResponse(BaseModel):
    id: int
    thickness: str
    thickness_mm: Optional[float]
    description: Optional[str]
    status_id: int
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Stone Color Schemas
class StoneColorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class StoneColorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    status_id: Optional[int] = None


class StoneColorResponse(BaseModel):
    id: int
    name: str
    color_code: Optional[str]
    description: Optional[str]
    status_id: int
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Edge Schemas
class EdgeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    edge_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class EdgeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    edge_type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status_id: Optional[int] = None


class EdgeResponse(BaseModel):
    id: int
    name: str
    edge_type: str
    description: Optional[str]
    status_id: int
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Stone Type Schemas
class StoneTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class StoneTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status_id: Optional[int] = None


class StoneTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status_id: int
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Fab Type Schemas (simple string list for now)
class FabPlanItem(BaseModel):
    id: int
    workstation_id: int
    workstation_name: Optional[str] = None
    planning_section_id: int
    plan_name: Optional[str] = None
    operator_id: int
    operator_name: Optional[str] = None
    estimated_hours: float
    scheduled_start_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    work_percentage: int
    notes: Optional[str] = None


# Fab Schemas
class FabCreate(BaseModel):
    job_id: int = Field(..., gt=0)
    fab_type: str = Field(..., min_length=1, max_length=255)
    sales_person_id: int = Field(..., gt=0)
    stone_type_id: int = Field(..., gt=0)
    stone_color_id: int = Field(..., gt=0)
    stone_thickness_id: int = Field(..., gt=0)
    edge_id: int = Field(..., gt=0)
    revenue: Optional[float] = Field(None, description="Revenue amount")
    input_area: Optional[str] = Field(None, description="Description of input area (e.g., 'Kitchen countertop and island')")
    total_sqft: Optional[float] = Field(default=1.0, gt=0)  # Default to 1 if unknown (client requirement)
    notes: Optional[str] = None
    template_needed: bool = True
    drafting_needed: bool = True
    slab_smith_cust_needed: bool = True
    slab_smith_ag_needed: bool = True
    sct_needed: bool = True
    final_programming_needed: bool = True
    cost_of_stone_id: Optional[int] = Field(None, description="Cost of stone record ID")
    cost_of_stone: Optional[Decimal] = Field(None, description="Cost of stone amount")


class FabUpdate(BaseModel):
    fab_type: Optional[str] = Field(None, min_length=1, max_length=255)
    sales_person_id: Optional[int] = Field(None, gt=0)
    stone_type_id: Optional[int] = Field(None, gt=0)
    stone_color_id: Optional[int] = Field(None, gt=0)
    stone_thickness_id: Optional[int] = Field(None, gt=0)
    edge_id: Optional[int] = Field(None, gt=0)
    input_area: Optional[str] = Field(None, description="Description of input area (e.g., 'Kitchen countertop and island')")
    total_sqft: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = Field(None, description="Note to add to FAB (will be saved to fab_notes)")
    stage: Optional[str] = Field(None, description="Stage for the note (defaults to current_stage)")
    template_needed: Optional[bool] = None
    drafting_needed: Optional[bool] = None
    slab_smith_cust_needed: Optional[bool] = None
    slab_smith_ag_needed: Optional[bool] = None
    sct_needed: Optional[bool] = None
    final_programming_needed: Optional[bool] = None
    drafter_id: Optional[int] = Field(None, gt=0, description="Drafter user ID")
    # Templating/Template tracking
    template_received: Optional[bool] = Field(None, description="Mark if template is received")
    template_review_complete: Optional[bool] = Field(None, description="Mark template review as complete")
    # Drafting tracking
    draft_completed: Optional[bool] = Field(None, description="Mark draft as completed")
    cad_review_complete: Optional[bool] = Field(None, description="Mark CAD review as complete")
    no_of_pieces: Optional[int] = Field(None, gt=0, description="Number of pieces")
    # Financial tracking
    revenue: Optional[float] = Field(None, description="Revenue amount")
    gp: Optional[float] = Field(None, description="Gross Profit amount")
    # SalesCT tracking
    sct_completed: Optional[bool] = Field(None, description="Mark SCT review as complete")
    revised: Optional[bool] = Field(None, description="Mark if FAB has been revised")
    # Cut List tracking
    shop_date_schedule: Optional[datetime] = Field(None, description="Scheduled shop date")
    final_programming_complete: Optional[bool] = Field(None, description="Mark final programming as complete")
    slab_smith_used: Optional[bool] = Field(None, description="Mark if slab smith was used")
    fp_not_needed: Optional[bool] = Field(None, description="Mark if final programming is not needed")
    # Final Programming tracking
    confirmed_date: Optional[datetime] = Field(None, description="Final programming confirmed date")
    wj_time_minutes: Optional[int] = Field(None, gt=0, description="Waterjet time in minutes")
    wj_linft: Optional[float] = Field(None, gt=0, description="Waterjet linear feet")
    edging_linft: Optional[float] = Field(None, gt=0, description="Edging linear feet")
    cnc_linft: Optional[float] = Field(None, gt=0, description="CNC linear feet")
    miter_linft: Optional[float] = Field(None, gt=0, description="Miter linear feet")
    installation_date: Optional[datetime] = Field(None, description="Installation date")
    current_stage: Optional[str] = None
    next_stage: Optional[str] = None
    status_id: Optional[int] = None
    cost_of_stone_id: Optional[int] = Field(None, description="Cost of stone record ID")
    cost_of_stone: Optional[Decimal] = Field(None, description="Cost of stone amount")
    saw_cut_lnft: Optional[float] = None
    shop_est_completion_date: Optional[datetime] = Field(None, description="Estimated completion date for shop")


class FabStageUpdate(BaseModel):
    current_stage: str
    
class FabResponse(BaseModel):
    id: int
    job_id: int
    job_details: Optional[dict] = None  # Complete job information
    account_id: Optional[int] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    account_contact_person: Optional[str] = None
    account_email: Optional[str] = None
    account_phone: Optional[str] = None
    fab_type: str
    sales_person_id: int
    sales_person_name: Optional[str] = None
    stone_type_id: int
    stone_type_name: Optional[str] = None
    stone_color_id: int
    stone_color_name: Optional[str] = None
    stone_thickness_id: int
    stone_thickness_value: Optional[str] = None
    edge_id: int
    edge_name: Optional[str] = None
    input_area: Optional[str] = None
    total_sqft: float
    notes: Optional[List[str]] = None
    template_needed: bool
    drafting_needed: bool
    slab_smith_cust_needed: bool
    slab_smith_ag_needed: bool
    sct_needed: bool
    final_programming_needed: bool
    drafter_id: Optional[int] = None
    drafter_name: Optional[str] = None
    drafter_assigned_by: Optional[int] = None
    drafter_assigned_by_name: Optional[str] = None
    drafter_assigned_at: Optional[datetime] = None
    # Templating/Template tracking
    template_received: Optional[bool] = False
    template_review_complete: Optional[bool] = False
    # Drafting tracking
    draft_completed: Optional[bool] = False
    cad_review_complete: Optional[bool] = False
    no_of_pieces: Optional[int] = None
    # Financial tracking
    revenue: Optional[float] = None
    gp: Optional[float] = None  # Gross Profit
    # SalesCT tracking
    sct_completed: Optional[bool] = False
    revised: Optional[bool] = False  # Indicates if FAB has been sent back for revisions
    # Cut List tracking
    shop_date_schedule: Optional[datetime] = None
    final_programming_complete: Optional[bool] = False
    final_programming_completed_date: Optional[datetime] = None
    slab_smith_used: Optional[bool] = False
    fp_not_needed: Optional[bool] = False
    # Final Programming tracking
    confirmed_date: Optional[datetime] = None  # When final programming confirmed
    wj_time_minutes: Optional[int] = None  # Waterjet time in minutes
    wj_linft: Optional[float] = None  # Waterjet linear feet
    edging_linft: Optional[float] = None  # Edging linear feet
    cnc_linft: Optional[float] = None  # CNC linear feet
    miter_linft: Optional[float] = None  # Miter linear feet
    saw_cut_lnft: Optional[float] = None  # Saw cut linear feet

    installation_date: Optional[datetime] = None
    current_stage: Optional[str] = "templating"
    next_stage: Optional[str] = "pre_draft_review"
    is_complete: Optional[bool] = False  # Whether current stage is completed
    stage_data: Optional[dict] = None  # Stage-specific data for current stage
    status_id: int
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime]
    updated_by: Optional[int]
    # Templating-related fields
    templating_schedule_start_date: Optional[datetime] = None
    templating_schedule_due_date: Optional[datetime] = None
    templating_notes: Optional[List[str]] = None
    technician_name: Optional[str] = None
    # FAB Notes (last 10)
    fab_notes: Optional[List[dict]] = None
    cost_of_stone_id: Optional[int] = Field(None, description="Cost of stone record ID")
    cost_of_stone: Optional[Decimal] = Field(None, description="Cost of stone amount")

    predraft_completed_date: Optional[datetime] = None
    template_review_complete: Optional[bool] = None
    template_completed_date: Optional[datetime] = None
    shop_est_completion_date: Optional[datetime] = None

    plans: List[FabPlanResponse] = []


    class Config:
        from_attributes = True


# Templating Schemas
class TemplatingScheduleCreate(BaseModel):
    fab_id: int = Field(..., gt=0, description="FAB ID")
    technician_id: int = Field(..., gt=0, description="Technician ID")
    schedule_start_date: datetime = Field(..., description="Scheduled start date")
    schedule_due_date: datetime = Field(..., description="Scheduled due date")
    total_sqft: Optional[str] = Field(None, description="Total square feet")
    notes: Optional[List[str]] = Field(None, description="Additional notes as array")
    revenue: Optional[float] = Field(None, ge=0, description="Revenue amount for the fab")
    


class TemplatingScheduleUpdate(BaseModel):
    """Schema for updating templating schedule"""
    technician_id: Optional[int] = None
    schedule_start_date: Optional[date] = None
    schedule_due_date: Optional[date] = None
    total_sqft: Optional[float] = None  # Make sure this field exists
    notes: Optional[List[str]] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    duration: Optional[float] = None
    is_templating_schedule: Optional[bool] = None
    status_id: Optional[int] = None
    is_completed: Optional[bool] = None

    class Config:
        from_attributes = True


class TemplatingCompleteRequest(BaseModel):
    actual_sqft: Optional[str] = Field(None, description="Actual square footage measured")
    actual_start_date: Optional[datetime] = Field(None, description="Actual start date of work")
    actual_end_date: Optional[datetime] = Field(None, description="Actual end date of work")
    duration: Optional[int] = Field(None, description="Duration in hours")
    notes: Optional[List[str]] = Field(None, description="Notes to append to existing notes")


class TemplatingResponse(BaseModel):
    """Schema for templating response"""
    id: int
    fab_id: int
    technician_id: Optional[int] = None
    technician_name: Optional[str] = None
    schedule_start_date: Optional[date] = None
    schedule_due_date: Optional[date] = None
    total_sqft: Optional[str] = None  # Changed from float to str to match database
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    duration: Optional[float] = None
    notes: Optional[List[str]] = None
    is_templating_schedule: Optional[bool] = None
    rescheduled: bool = False  # NEW
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None
    status_name: Optional[str] = None
    current_stage: Optional[str] = None
    next_stage: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


# Templating Coordinator specific schemas
class TemplatingReviewUpdate(BaseModel):
    """Schema for templating coordinator to update template review"""
    template_received: bool = Field(..., description="Mark if template is received")
    total_sqft: Optional[float] = Field(None, gt=0, description="Updated total square feet")
    notes: Optional[str] = Field(None, description="Review notes")


class TemplateReviewCompleteUpdate(BaseModel):
    """Schema for marking template review as complete"""
    template_review_complete: bool = Field(..., description="Mark template review as complete/incomplete")
    total_sqft: Optional[float] = Field(None, gt=0, description="Updated total square feet")


# Templating Technician specific schemas
class TemplatingTechnicianUpdate(BaseModel):
    """Schema for templating technician to update their work"""
    is_completed: bool = Field(..., description="Mark templating as completed/not completed")
    actual_start_date: Optional[datetime] = Field(None, description="Actual start date of templating work")
    duration: Optional[int] = Field(None, gt=0, description="Duration in minutes")
    total_sqft: Optional[str] = Field(None, description="Measured square footage")
    notes: Optional[List[str]] = Field(None, description="Templating notes")


# Pre-Draft schemas
class PreDraftUpdate(BaseModel):
    """Schema for pre-draft review actions"""
    template_review_complete: Optional[bool] = Field(None, description="Mark template review complete")
    total_sqft: Optional[float] = Field(None, gt=0, description="Updated square feet")
    drafter_id: Optional[int] = Field(None, gt=0, description="Assign drafter")
    notes: Optional[str] = Field(None, description="Pre-draft notes")
    current_stage: Optional[str] = Field(None, description="Move to different stage")


# Drafting schemas
class DraftingSessionUpdate(BaseModel):
    """Schema for drafting session actions (start, pause, end)"""
    action: str = Field(..., description="Action: 'start', 'pause', or 'end'")
    notes: Optional[str] = Field(None, description="Session notes")


class DraftingUpdate(BaseModel):
    """Schema for updating drafting information"""
    # Original frontend fields
    total_sqft: Optional[float] = Field(None, gt=0, description="Updated square feet")
    no_of_pieces: Optional[int] = Field(None, gt=0, description="Number of pieces")
    cad_review_complete: Optional[bool] = Field(None, description="Mark CAD review complete")
    draft_completed: Optional[bool] = Field(None, description="Mark draft as completed")
    notes: Optional[str] = Field(None, description="Drafting notes")
    current_stage: Optional[str] = Field(None, description="Move to different stage")
    # Database model fields
    drafter_start_date: Optional[datetime] = None
    drafter_end_date: Optional[datetime] = None
    total_sqft_drafted: Optional[float] = None
    no_of_piece_drafted: Optional[int] = None
    draft_note: Optional[str] = None
    total_hours_drafted: Optional[float] = None
    mentions: Optional[str] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None
    
    @field_validator('drafter_start_date', 'drafter_end_date', mode='before')
    @classmethod
    def remove_timezone(cls, v):
        """Convert timezone-aware datetime to naive datetime"""
        if v is None:
            return v
        if isinstance(v, str):
            # Parse ISO format string and remove timezone
            # Replace Z with +00:00 for fromisoformat
            if v.endswith('Z'):
                v = v[:-1] + '+00:00'
            dt = datetime.fromisoformat(v)
            return dt.replace(tzinfo=None)
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


# Clockwork Schemas
class ClockworkCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    technician_id: int = Field(..., gt=0)
    table_name: str = Field(..., min_length=1, description="e.g., 'templatings' or 'draftings'")
    table_id: int = Field(..., gt=0, description="ID of the related record in table_name")
    started_at: datetime
    completed_at: datetime
    total_sqft_done: str
    notes: Optional[str] = None
    pause_reason: Optional[str] = None


class ClockworkUpdate(BaseModel):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_sqft_done: Optional[str] = None
    notes: Optional[str] = None
    pause_reason: Optional[str] = None


class ClockworkResponse(BaseModel):
    id: int
    fab_id: int
    technician_id: int
    table_name: str
    table_id: int
    started_at: datetime
    completed_at: datetime
    total_sqft_done: str
    notes: Optional[str]
    pause_reason: Optional[str]
    created_at: datetime
    created_by: int


# Drafting Schemas
class DraftingCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    drafter_id: int = Field(..., gt=0)
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    total_sqft_required_to_draft: str




class DraftingSubmitUpdate(BaseModel):
    total_sqft_drafted: float = Field(..., description="Total square feet completed")
    no_of_piece_drafted: int = Field(..., description="Number of pieces drafted")
    draft_note: Optional[str] = Field(None, description="Draft notes")
    is_drafting_completed: bool = Field(default=False, description="Is drafting completed")
    mentions: Optional[str] = Field(None, description="Comma-separated list of user IDs to notify")


class DraftingResponse(BaseModel):
    id: int
    fab_id: int
    drafter_id: int
    drafter_name: Optional[str] = None
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    drafter_start_date: Optional[datetime]
    drafter_end_date: Optional[datetime]
    total_sqft_required_to_draft: str
    total_sqft_drafted: Optional[float]
    no_of_piece_drafted: Optional[int]
    total_hours_drafted: Optional[float]
    draft_note: Optional[str]
    mentions: Optional[str]
    file_ids: Optional[str]
    is_redrafting: bool
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Pre Draft Review Schemas
class PreDraftReviewCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    is_completed: bool = Field(default=False)
    draft_notes: Optional[str] = None


class PreDraftReviewUpdate(BaseModel):
    is_completed: Optional[bool] = None
    draft_notes: Optional[str] = None
    is_redrafting_needed: Optional[bool] = None
    redraft_notes: Optional[str] = None


class PreDraftReviewResponse(BaseModel):
    id: int
    fab_id: int
    draft_notes: Optional[str]
    is_redrafting_needed: Optional[bool]
    is_completed: bool
    status_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    updated_by: int


# SlabSmith Schemas
class SlabSmithCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    slab_smith_type: str = Field(..., min_length=1)
    drafter_id: int = Field(..., gt=0)
    start_date: datetime
    end_date: Optional[datetime] = None
    total_sqft_completed: Optional[str] = None


class SlabSmithUpdate(BaseModel):
    end_date: Optional[datetime] = None
    total_sqft_completed: Optional[str] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None


class SlabSmithResponse(BaseModel):
    id: int
    fab_id: int
    slab_smith_type: str
    drafter_id: int
    start_date: datetime
    end_date: Optional[datetime]
    total_sqft_completed: Optional[str]
    file_ids: Optional[str]
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Sales CT / Review Schemas
class SalesCTCreate(BaseModel):
    fab_id: int = Field(..., description="FAB ID")
    is_revision_needed: bool = Field(..., description="Whether revision is needed")
    revision_reason: Optional[str] = Field(None, description="Reason for revision if needed")  
    revision_type: Optional[str] = Field(None, description="Type of revision")
    class Config:
        from_attributes = True


class SalesCTUpdate(BaseModel):
    is_revision_needed: Optional[bool] = None
    is_revision_completed: Optional[bool] = None
    is_completed: Optional[bool] = None
    revenue: Optional[float] = None
    status_id: Optional[int] = None


class SalesCTRevisionCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    revision_reason: str
    revision_type: Optional[str] = None
    file_ids: Optional[str] = Field(None, description="Comma-separated file IDs")


class SalesCTRevisionUpdate(BaseModel):
    is_revision_completed: bool = Field(default=False)
    draft_note: Optional[str] = None
    revision_type: Optional[str] = None


class SalesCTResponse(BaseModel):
    id: int
    fab_id: int
    is_revision_needed: bool
    revision_reason: Optional[str] = None
    is_revision_completed: Optional[bool] = None
    no_of_revisions: Optional[str] = None
    current_revision_count: Optional[str] = None
    status_id: int
    slab_smith_type: Optional[str] = None
    drafter_id: Optional[int] = None
    start_date: Optional[str] = None  # ISO format string
    end_date: Optional[str] = None  # ISO format string
    total_sqft_completed: Optional[float] = None
    file_ids: Optional[str] = None
    created_at: Optional[str] = None  # ISO format string
    updated_at: Optional[str] = None  # ISO format string
    updated_by: Optional[int] = None
    
    class Config:
        from_attributes = True


# File Management Schemas
class FileAttachCreate(BaseModel):
    entity_type: str = Field(..., description="e.g., 'drafting', 'slabsmith'")
    entity_id: int = Field(..., gt=0)
    file_id: int = Field(..., gt=0)


class FileAttachResponse(BaseModel):
    success: bool
    message: str


# Job with Fabs Response
class FabDetailResponse(FabResponse):
    stone_type_name: Optional[str] = None
    stone_color_name: Optional[str] = None
    stone_thickness_value: Optional[str] = None
    edge_name: Optional[str] = None
    sales_person_name: Optional[str] = None


class JobWithFabsResponse(BaseModel):
    id: int
    name: str
    job_number: str
    account_id: int
    account_name: Optional[str] = None
    priority: Optional[str]
    status_id: int
    created_at: datetime
    fabs: List[FabDetailResponse] = []


# Table Names Response
class TableNamesResponse(BaseModel):
    table_names: List[str]


# FabNotes Schemas
class FabNotesCreate(BaseModel):
    fab_id: int = Field(..., gt=0, description="FAB ID")
    stage: Optional[str] = Field(None, description="Stage for the note (defaults to FAB's current_stage)")
    note: str = Field(..., min_length=1, description="Note content")


class FabNotesUpdate(BaseModel):
    note: Optional[str] = Field(None, min_length=1, description="Updated note content")
    stage: Optional[str] = Field(None, description="Updated stage")


class FabNotesResponse(BaseModel):
    id: int
    fab_id: int
    stage: str
    note: str
    created_by: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None
    updated_by_name: Optional[str] = None


# WJ Programming Schemas
class WJProgrammingCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    drafter_id: int = Field(..., gt=0)
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    total_ln_ft: Optional[str] = None


class WJProgrammingUpdate(BaseModel):
    drafter_id: Optional[int] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    drafter_start_date: Optional[datetime] = None
    drafter_end_date: Optional[datetime] = None
    no_of_pieces: Optional[str] = None
    total_ln_ft: Optional[str] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None


class WJProgrammingResponse(BaseModel):
    id: int
    fab_id: int
    drafter_id: int
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    drafter_start_date: Optional[datetime]
    drafter_end_date: Optional[datetime]
    no_of_pieces: Optional[str]
    total_ln_ft: Optional[str]
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# WJ Scheduling Schemas
class WJSchedulingCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    total_ln_ft: Optional[str] = None


class WJSchedulingUpdate(BaseModel):
    technician_id: Optional[int] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    total_ln_ft: Optional[str] = None
    completed_ln_ft: Optional[str] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None


class WJSchedulingResponse(BaseModel):
    id: int
    fab_id: int
    technician_id: Optional[int]
    scheduled_start_date: Optional[datetime]
    scheduled_end_date: Optional[datetime]
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    total_ln_ft: Optional[str]
    completed_ln_ft: Optional[str]
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Resurface Scheduling Schemas
class ResurfaceSchedulingCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    total_sqft: Optional[str] = None


class ResurfaceSchedulingUpdate(BaseModel):
    technician_id: Optional[int] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    total_sqft: Optional[str] = None
    completed_sqft: Optional[str] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None


class ResurfaceSchedulingResponse(BaseModel):
    id: int
    fab_id: int
    technician_id: Optional[int]
    scheduled_start_date: Optional[datetime]
    scheduled_end_date: Optional[datetime]
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    total_sqft: Optional[str]
    completed_sqft: Optional[str]
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Revision Schemas
class RevisionCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    revision_type: str = Field(..., min_length=1)
    requested_by: int = Field(..., gt=0)
    assigned_to: Optional[int] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    revision_notes: Optional[str] = None


class RevisionUpdate(BaseModel):
    revision_type: Optional[str] = None
    assigned_to: Optional[int] = None
    scheduled_start_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    revision_notes: Optional[str] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None


class RevisionResponse(BaseModel):
    id: int
    fab_id: int
    revision_type: str
    requested_by: int
    assigned_to: Optional[int]
    scheduled_start_date: Optional[datetime]
    scheduled_end_date: Optional[datetime]
    actual_start_date: Optional[datetime]
    actual_end_date: Optional[datetime]
    revision_notes: Optional[str]
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Cost of Stone Schemas
class CostOfStoneCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    stone_color_id: Optional[int] = None
    stone_type_id: Optional[int] = None
    total_sqft: Optional[str] = None
    cost_per_sqft: Optional[str] = None
    waste_percentage: Optional[str] = None


class CostOfStoneUpdate(BaseModel):
    stone_color_id: Optional[int] = None
    stone_type_id: Optional[int] = None
    total_sqft: Optional[str] = None
    cost_per_sqft: Optional[str] = None
    total_cost: Optional[str] = None
    waste_percentage: Optional[str] = None
    calculated_by: Optional[int] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None


class CostOfStoneResponse(BaseModel):
    id: int
    fab_id: int
    stone_color_id: Optional[int]
    stone_type_id: Optional[int]
    total_sqft: Optional[str]
    cost_per_sqft: Optional[str]
    total_cost: Optional[str]
    waste_percentage: Optional[str]
    calculated_by: Optional[int]
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Install Scheduling Schemas
class InstallSchedulingCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    scheduled_install_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    total_sqft: Optional[str] = None


class InstallSchedulingUpdate(BaseModel):
    installer_id: Optional[int] = None
    scheduled_install_date: Optional[datetime] = None
    scheduled_end_date: Optional[datetime] = None
    actual_install_date: Optional[datetime] = None
    total_sqft: Optional[str] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None


class InstallSchedulingResponse(BaseModel):
    id: int
    fab_id: int
    installer_id: Optional[int]
    scheduled_install_date: Optional[datetime]
    scheduled_end_date: Optional[datetime]
    actual_install_date: Optional[datetime]
    total_sqft: Optional[str]
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Install Completion Schemas
class InstallCompletionCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    installer_id: int = Field(..., gt=0)
    install_date: datetime
    completion_date: datetime
    total_sqft_installed: Optional[str] = None
    customer_signature: Optional[str] = None
    completion_notes: Optional[str] = None


class InstallCompletionUpdate(BaseModel):
    installer_id: Optional[int] = None
    install_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    total_sqft_installed: Optional[str] = None
    customer_signature: Optional[str] = None
    completion_notes: Optional[str] = None
    is_completed: Optional[bool] = None
    status_id: Optional[int] = None


class InstallCompletionResponse(BaseModel):
    id: int
    fab_id: int
    installer_id: int
    install_date: datetime
    completion_date: datetime
    total_sqft_installed: Optional[str]
    customer_signature: Optional[str]
    completion_notes: Optional[str]
    is_completed: bool
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# SalesCT Schemas
class SalesCTReviewUpdate(BaseModel):
    """Schema for Sales CT review update"""
    sct_completed: bool
    revenue: Optional[Decimal] = None
    slab_smith_used: Optional[bool] = None  # ← Add this
    slab_smith_approved: Optional[bool] = None
    block_drawing_approved: Optional[bool] = None
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sct_completed": True,
                "revenue": 15000.50,
                "slab_smith_used": True,
                "notes": "All measurements verified and approved"
            }
        }


class SalesCTSendToDrafting(BaseModel):
    """Schema for sending FAB back to drafting for revisions"""
    notes: str = Field(..., description="Revision notes - required when sending back")
    

class SalesCTApprove(BaseModel):
    """Schema for approving FAB and sending to SlabSmith"""
    sct_completed: bool = Field(default=True, description="Mark SCT as complete")
    revenue: Optional[Decimal] = None
    slab_smith_used: Optional[bool] = None  # ← Add this
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sct_completed": True,
                "revenue": 15000.50,
                "slab_smith_used": True,
                "notes": "Approved for production"
            }
        }


# Cut List Schemas
class CutListScheduleUpdate(BaseModel):
    """Schema for scheduling cut list shop date"""
    shop_date_schedule: datetime = Field(..., description="Scheduled shop date")
    installation_date: Optional[datetime] = Field(None, description="Optional installation date")
    no_of_pieces: Optional[int] = Field(None, gt=0, description="Number of pieces")
    total_sqft: Optional[float] = Field(None, gt=0, description="Total square feet")
    wj_linft: Optional[float] = Field(None, gt=0, description="Waterjet linear feet")
    edging_linft: Optional[float] = Field(None, gt=0, description="Edging linear feet")
    cnc_linft: Optional[float] = Field(None, gt=0, description="CNC linear feet")
    miter_linft: Optional[float] = Field(None, gt=0, description="Miter linear feet")
    revision_complete: Optional[bool] = Field(None, description="Mark revision as complete")


class CutListUpdate(BaseModel):
    """Schema for updating cut list"""
    slab_smith_used: Optional[bool] = Field(None, description="Whether slab smith was used")
    fp_not_needed: Optional[bool] = Field(None, description="Whether final programming is not needed")
    shop_date_schedule: Optional[datetime] = Field(None, description="Scheduled shop date")
    revision_complete: Optional[bool] = Field(None, description="Whether revision is complete")
    notes: Optional[str] = Field(None, description="Additional notes")


# Final Programming Schemas
class FinalProgrammingSessionUpdate(BaseModel):
    """Schema for final programming session actions (start, pause, resume, end)"""
    action: str = Field(..., description="Action: 'start', 'pause', 'resume', or 'end'")
    notes: Optional[str] = Field(None, description="Session notes")


class FinalProgrammingScheduleShopDate(BaseModel):
    """Schema for scheduling shop date from Final Programming"""
    shop_date_schedule: datetime = Field(..., description="Scheduled shop date")
    installation_date: Optional[datetime] = Field(None, description="Optional installation date")
    no_of_pieces: Optional[int] = Field(None, gt=0, description="Number of pieces")
    total_sqft: Optional[float] = Field(None, gt=0, description="Total square feet")
    wj_linft: Optional[float] = Field(None, gt=0, description="Waterjet linear feet")
    edging_linft: Optional[float] = Field(None, gt=0, description="Edging linear feet")
    cnc_linft: Optional[float] = Field(None, gt=0, description="CNC linear feet")
    miter_linft: Optional[float] = Field(None, gt=0, description="Miter linear feet")
    confirmed: Optional[bool] = Field(None, description="Mark as confirmed")


class FinalProgrammingComplete(BaseModel):
    """Schema for completing final programming"""
    final_programming_complete: bool = Field(..., description="Mark final programming as complete")
    final_programming_completed_date: Optional[datetime] = Field(None, description="Date when final programming was completed")
    notes: Optional[str] = Field(None, description="Final programming notes")
    drafter_id: Optional[int] = Field(None, gt=0, description="Assigned programmer ID")
    wj_time_minutes: Optional[int] = Field(None, gt=0, description="Waterjet time in minutes")


# SlabSmith Session Schemas
class SlabSmithSessionUpdate(BaseModel):
    """Schema for SlabSmith session actions (start, pause, resume, end)"""
    action: str = Field(..., description="Action: 'start', 'pause', 'resume', or 'end'")
    notes: Optional[str] = Field(None, description="Session notes")

# Drafting Session Schemas
class DraftingSessionAction(BaseModel):
    """Schema for drafting session actions"""
    drafter_id: int
    action: str  # start, pause, resume, on_hold, end
    session_start_time: Optional[datetime] = None
    session_end_time: Optional[datetime] = None
    timestamp: Optional[datetime] = None
    sqft_drafted: Optional[str] = None
    work_percentage_done: Optional[float] = None
    note: Optional[str] = None
    is_revision: Optional[bool] = False
    
    @field_validator('timestamp', 'session_start_time', 'session_end_time', mode='before')
    @classmethod
    def clean_iso_timestamp(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            # Remove spaces before fractional seconds: "2026-01-23T07:30:22. 723Z" -> "2026-01-23T07:30:22.723Z"
            v = v.replace('. ', '.')
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class DraftingSessionNoteResponse(BaseModel):
    timestamp: datetime
    action: str
    note: Optional[str]
    sqft_drafted: Optional[str]
    work_percentage_done: Optional[int]


class DraftingSessionResponse(BaseModel):
    session_id: int
    fab_id: int
    drafter_id: int
    status: str
    current_session_start_time: datetime
    last_action_time: Optional[datetime]
    total_time_spent: int  # in seconds
    cumulative_sqft_drafted: str
    work_percentage_done: int
    current_pause_start_time: Optional[datetime]
    total_pause_duration: int  # in seconds
    notes: List[DraftingSessionNoteResponse]


class DraftingSessionHistoryResponse(BaseModel):
    fab_id: int
    sessions: List[DraftingSessionResponse]
    total_sessions: int

# Fab Type Schemas
class FabTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Fab type name")
    description: Optional[str] = Field(None, description="Fab type description")


class FabTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Enables SQLModel -> Pydantic conversion



class ShopCutPlanStageCreate(BaseModel):
    """Schema for a stage in shop cut plan creation"""
    sequence: int = Field(ge=1, description="Execution order of this stage (1-based)")
    workstation_id: int
    planning_section_id: int
    operator_ids: List[int]
    estimated_hours: float = Field(gt=0)
    scheduled_start: Optional[datetime] = None
    notes: Optional[str] = None


class ShopCutPlanCreate(BaseModel):
    """Schema for creating shop cut plans"""
    fab_id: int
    estimated_hours: float = Field(gt=0)
    status_id: int = Field(default=1, ge=0, le=1)  # 0=inactive, 1=active
    notes: Optional[str] = None
    stages: List[ShopCutPlanStageCreate]


class ShopCutPlanUpdate(BaseModel):
    """Schema for updating a shop cut plan (matches POST structure)"""
    status_id: int = Field(default=1, ge=0, le=1)
    notes: Optional[str] = None
    stage: ShopCutPlanStageCreate


class ShopPlanSuggestionsRequest(BaseModel):
    plan_data: ShopCutPlanCreate
    window_start: datetime
    window_end: datetime
    slot_minutes: int = Field(default=30, gt=0)
    max_suggestions_per_stage: int = Field(default=10, gt=0)


class ShopCutPlanTimerActionRequest(BaseModel):
    action: str = Field(description="start, pause, resume, stop")
    note: Optional[str] = None
    timestamp: Optional[datetime] = None


class ShopCutPlanTimerEventResponse(BaseModel):
    id: int
    session_id: int
    action: str
    event_at: datetime
    note: Optional[str] = None


class ShopCutPlanTimerSessionResponse(BaseModel):
    id: int
    status: str
    session_start_at: datetime
    current_run_start_at: Optional[datetime] = None
    current_pause_start_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    total_work_seconds: int
    total_pause_seconds: int


class ShopCutPlanTimerStateResponse(BaseModel):
    shop_cut_plan_id: int
    operator_id: int
    session: Optional[ShopCutPlanTimerSessionResponse] = None
    total_actual_seconds: int
    total_actual_hours: float
    estimated_hours: float
    work_percentage: int


class ShopCutPlanTimerHistoryResponse(BaseModel):
    shop_cut_plan_id: int
    operator_id: int
    sessions: List[ShopCutPlanTimerSessionResponse]
    events: List[ShopCutPlanTimerEventResponse]

class EarliestAvailabilityItem(BaseModel):
    planning_section_id: int 
    operator_id: int
    workstation_id: int
    estimated_hours: float


class EarliestAvailabilityRequest(BaseModel):
    requests: List[EarliestAvailabilityItem]
    start_from: Optional[datetime] = None
    slot_minutes: int = 30
    search_horizon_days: int = 30
    max_proposals_per_request: int = 3