from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ActionMenuCreate(BaseModel):
    """Schema for creating a new action menu"""
    name: str = Field(..., min_length=1, max_length=255, description="Action menu name")
    code: str = Field(..., min_length=1, max_length=255, description="Action menu code (unique identifier)")


class ActionMenuUpdate(BaseModel):
    """Schema for updating an action menu"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Action menu name")
    code: Optional[str] = Field(None, min_length=1, max_length=255, description="Action menu code")


class ActionMenuResponse(BaseModel):
    """Schema for action menu response"""
    id: int
    name: str
    code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    """Schema for creating a new permission"""
    name: str = Field(..., min_length=1, max_length=255, description="Permission name")
    description: Optional[str] = Field(None, max_length=255, description="Permission description")
    can_create: bool = Field(default=False, description="Can create")
    can_read: bool = Field(default=False, description="Can read")
    can_update: bool = Field(default=False, description="Can update")
    can_delete: bool = Field(default=False, description="Can delete")


class PermissionUpdate(BaseModel):
    """Schema for updating a permission"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Permission name")
    description: Optional[str] = Field(None, max_length=255, description="Permission description")
    can_create: Optional[bool] = Field(None, description="Can create")
    can_read: Optional[bool] = Field(None, description="Can read")
    can_update: Optional[bool] = Field(None, description="Can update")
    can_delete: Optional[bool] = Field(None, description="Can delete")


class PermissionResponse(BaseModel):
    """Schema for permission response"""
    id: int
    name: str
    description: Optional[str]
    can_create: bool
    can_read: bool
    can_update: bool
    can_delete: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
