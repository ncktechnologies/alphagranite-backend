from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# Job Schemas
class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Job name")
    job_number: str = Field(..., min_length=1, max_length=100, description="Unique job number")
    account_id: int = Field(..., gt=0, description="Account ID")
    description: Optional[str] = None
    priority: Optional[str] = Field(default="Medium", description="Job priority: Low, Medium, High, Urgent")
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class JobUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    job_number: Optional[str] = Field(None, min_length=1, max_length=100)
    account_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status_id: Optional[int] = None


class JobResponse(BaseModel):
    id: int
    name: str
    job_number: str
    account_id: int
    description: Optional[str]
    priority: Optional[str]
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    status_id: int
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime]
    updated_by: Optional[int]


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
class FabTypeResponse(BaseModel):
    name: str
    description: Optional[str] = None


# Fab Schemas
class FabCreate(BaseModel):
    job_id: int = Field(..., gt=0)
    fab_type: str = Field(..., min_length=1, max_length=255)
    sales_person_id: int = Field(..., gt=0)
    stone_type_id: int = Field(..., gt=0)
    stone_color_id: int = Field(..., gt=0)
    stone_thickness_id: int = Field(..., gt=0)
    edge_id: int = Field(..., gt=0)
    input_area: str = Field(..., min_length=1, max_length=255)
    total_sqft: Optional[float] = Field(default=1.0, gt=0)  # Default to 1 if unknown (client requirement)
    notes: Optional[str] = None
    template_needed: bool = True
    drafting_needed: bool = True
    slab_smith_cust_needed: bool = True
    slab_smith_ag_needed: bool = True
    sct_needed: bool = True
    final_programming_needed: bool = True


class FabUpdate(BaseModel):
    fab_type: Optional[str] = Field(None, min_length=1, max_length=255)
    sales_person_id: Optional[int] = Field(None, gt=0)
    stone_type_id: Optional[int] = Field(None, gt=0)
    stone_color_id: Optional[int] = Field(None, gt=0)
    stone_thickness_id: Optional[int] = Field(None, gt=0)
    edge_id: Optional[int] = Field(None, gt=0)
    input_area: Optional[str] = Field(None, min_length=1, max_length=255)
    total_sqft: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None
    template_needed: Optional[bool] = None
    drafting_needed: Optional[bool] = None
    slab_smith_cust_needed: Optional[bool] = None
    slab_smith_ag_needed: Optional[bool] = None
    sct_needed: Optional[bool] = None
    final_programming_needed: Optional[bool] = None
    current_stage: Optional[str] = None
    next_stage: Optional[str] = None
    status_id: Optional[int] = None


class FabResponse(BaseModel):
    id: int
    job_id: int
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
    input_area: str
    total_sqft: float
    notes: Optional[List[str]] = None
    template_needed: bool
    drafting_needed: bool
    slab_smith_cust_needed: bool
    slab_smith_ag_needed: bool
    sct_needed: bool
    final_programming_needed: bool
    current_stage: Optional[str]
    next_stage: Optional[str]
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


class TemplatingScheduleUpdate(BaseModel):
    technician_id: Optional[int] = Field(None, gt=0)
    schedule_start_date: Optional[datetime] = None
    schedule_due_date: Optional[datetime] = None
    total_sqft: Optional[str] = None
    notes: Optional[List[str]] = None
    status_id: Optional[int] = None


class TemplatingCompleteRequest(BaseModel):
    actual_sqft: Optional[str] = Field(None, description="Actual square footage measured")
    actual_start_date: Optional[datetime] = Field(None, description="Actual start date of work")
    duration: Optional[int] = Field(None, description="Duration in hours")
    notes: Optional[List[str]] = Field(None, description="Notes to append to existing notes")


class TemplatingResponse(BaseModel):
    id: int
    fab_id: int
    technician_id: Optional[int]
    technician_name: Optional[str] = None  # Technician full name
    schedule_start_date: Optional[datetime]
    schedule_due_date: Optional[datetime]
    total_sqft: Optional[str]
    actual_start_date: Optional[datetime] = None
    duration: Optional[int] = None
    notes: Optional[List[str]]
    is_templating_schedule: bool
    status_id: int
    status_name: Optional[str] = None  # Status description
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]

    class Config:
        from_attributes = True


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


class DraftingUpdate(BaseModel):
    drafter_start_date: Optional[datetime] = None
    drafter_end_date: Optional[datetime] = None
    total_sqft_drafted: Optional[str] = None
    no_of_piece_drafted: Optional[str] = None
    draft_note: Optional[str] = None
    mentions: Optional[str] = None
    status_id: Optional[int] = None


class DraftingSubmitUpdate(BaseModel):
    total_sqft_drafted: str = Field(..., description="Total square feet completed")
    no_of_piece_drafted: str = Field(..., description="Number of pieces drafted")
    draft_note: Optional[str] = Field(None, description="Draft notes")
    is_drafting_completed: bool = Field(default=False, description="Is drafting completed")
    mentions: Optional[str] = Field(None, description="Comma-separated list of user IDs to notify")


class DraftingResponse(BaseModel):
    id: int
    fab_id: int
    drafter_id: int
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    drafter_start_date: Optional[datetime]
    drafter_end_date: Optional[datetime]
    total_sqft_required_to_draft: str
    total_sqft_drafted: Optional[str]
    no_of_piece_drafted: Optional[str]
    draft_note: Optional[str]
    mentions: Optional[str]
    file_ids: Optional[str]
    is_redrafting: bool
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
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


# Sales CT / Review Schemas
class SalesCTCreate(BaseModel):
    fab_id: int = Field(..., gt=0)
    is_revision_needed: bool = Field(default=False)


class SalesCTUpdate(BaseModel):
    is_revision_needed: Optional[bool] = None
    is_revision_completed: Optional[bool] = None
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
    is_revision_completed: Optional[bool]
    no_of_revisions: Optional[str]
    current_revision_count: Optional[str]
    status_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    updated_by: Optional[int]


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