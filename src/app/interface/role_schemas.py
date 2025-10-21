from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

class PermissionBase(BaseModel):
    """Base schema for permission"""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    """Schema for creating a new role"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    permission_ids: List[int] = Field(..., description="List of permission IDs to associate with the role")
    status: int = Field(1, description="Role status (1=Active, 2=Inactive)")

class RoleUpdate(BaseModel):
    """Schema for updating an existing role"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    permission_ids: Optional[List[int]] = Field(None, description="List of permission IDs to associate with the role")
    status: Optional[int] = Field(None, description="Role status (1=Active, 2=Inactive)")

class RoleStatusUpdate(BaseModel):
    """Schema for updating role status"""
    status: int = Field(..., description="Role status (1=Active, 2=Inactive, 3=Deleted)")

class UserStatusUpdate(BaseModel):
    """Schema for updating user status"""
    status: int = Field(..., description="User status (1=Active, 2=Inactive)")

class UserBasicInfo(BaseModel):
    """Basic user information for role member listing"""
    id: int
    first_name: str
    last_name: str
    profile_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class RoleUserInfo(UserBasicInfo):
    """User information for detailed role member listing"""
    email: str
    status: int
    invited_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    """Schema for role response"""
    id: int
    name: str
    description: Optional[str] = None
    status: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RoleWithStats(RoleResponse):
    """Schema for role with member statistics"""
    total_members: int
    active_members: int
    pending_members: int
    inactive_members: int
    
    class Config:
        from_attributes = True

class RoleWithMemberPreview(RoleResponse):
    """Schema for role with preview of members"""
    member_count: int
    top_members: List[UserBasicInfo] = []
    
    class Config:
        from_attributes = True

class RoleWithPermissions(RoleResponse):
    """Schema for role with permissions"""
    permissions: List[PermissionBase] = []
    
    class Config:
        from_attributes = True

class RoleWithMembers(RoleWithStats):
    """Schema for role with detailed member information"""
    members: List[RoleUserInfo] = []
    
    class Config:
        from_attributes = True

class RoleListResponse(BaseModel):
    """Schema for paginated list of roles"""
    total: int
    page: int
    per_page: int
    data: List[RoleWithMemberPreview]

class RoleMembersResponse(BaseModel):
    """Schema for paginated list of role members"""
    total: int
    page: int
    per_page: int
    data: RoleWithMembers