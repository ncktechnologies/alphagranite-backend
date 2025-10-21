import re
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validatorld, validator

# These schemas are used for employee operations
# Note: Employees are stored in the User table, these schemas
# provide a specialized interface for working with user records as employees

class EmployeeCreate(BaseModel):
    """Schema for creating a new employee (creates a record in the users table)"""
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr = Field(...)
    phone: Optional[str] = Field(None)
    department: int = Field(...)
    gender: Optional[str] = Field(None)
    home_address: Optional[str] = Field(None)
    profile_image_id: Optional[int] = Field(None)
    role_id: Optional[int] = Field(None)

class EmployeeResponse(BaseModel):
    """Schema for employee response (represents a user record from the users table)"""
    id: int
    employee_id: UUID
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    department: int
    gender: Optional[str] = None
    home_address: Optional[str] = None
    profile_image_id: Optional[int] = None
    status: int
    created_at: datetime
    updated_at: datetime
    role_id: Optional[int] = None

    class Config:
        from_attributes = True

class EmployeeUpdate(BaseModel):
    """Schema for updating an employee"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = Field(None)
    phone_number: Optional[str] = Field(None)
    department_id: Optional[int] = Field(None)
    gender: Optional[str] = Field(None)
    home_address: Optional[str] = Field(None)
    profile_image_id: Optional[int] = Field(None)
    role_id: Optional[int] = Field(None)

class EmployeeStatusUpdate(BaseModel):
    """Schema for updating employee status"""
    status: int = Field(...)

class EmployeeListResponse(BaseModel):
    """Schema for paginated list of employees"""
    total: int
    page: int
    per_page: int
    data: list[EmployeeResponse]