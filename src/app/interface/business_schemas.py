from datetime import datetime
from typing import Optional
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
    total_sqft: float = Field(..., gt=0)
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
    status_id: Optional[int] = None


class FabResponse(BaseModel):
    id: int
    job_id: int
    fab_type: str
    sales_person_id: int
    stone_type_id: int
    stone_color_id: int
    stone_thickness_id: int
    edge_id: int
    input_area: str
    total_sqft: float
    notes: Optional[str]
    template_needed: bool
    drafting_needed: bool
    slab_smith_cust_needed: bool
    slab_smith_ag_needed: bool
    sct_needed: bool
    final_programming_needed: bool
    current_stage: Optional[str]
    status_id: int
    created_at: datetime
    created_by: int
    updated_at: Optional[datetime]
    updated_by: Optional[int]