from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Any

# Base Department Schema
class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)

# Create Department Request
class DepartmentCreate(DepartmentBase):
    pass

# Update Department Request
class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)

# Change Department Status Request
class DepartmentStatusChange(BaseModel):
    status: int = Field(...)

# Department User Summary (for listing department members)
class DepartmentUserSummary(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    profile_image_id: Optional[int] = None

# Department Response with Users
class DepartmentWithUsers(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: int
    created_at: datetime
    updated_at: datetime
    users: List[DepartmentUserSummary]
    total_members: int

# Department Summary (for listing departments)
class DepartmentSummary(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: int
    total_members: int
    sample_members: List[DepartmentUserSummary]

# Department List Response
class DepartmentListResponse(BaseModel):
    items: List[DepartmentSummary]
    total: int
    page: int
    size: int
    pages: int

# User Details (for listing users in a department)
class UserDetails(BaseModel):
    id: int
    employee_id: UUID
    first_name: str
    last_name: str
    email: str
    home_address: Optional[str] = None
    gender: Optional[str] = None
    profile_image_id: Optional[int] = None
    created_at: datetime
    phone: Optional[str] = None

# Department Users Response
class DepartmentUsersResponse(BaseModel):
    department_id: int
    department_name: str
    department_description: Optional[str] = None
    users: List[UserDetails]
    total: int
    page: int
    size: int
    pages: int