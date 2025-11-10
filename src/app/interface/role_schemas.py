from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

class PermissionBase(BaseModel):
    """Base schema for permission"""
    id: int
    name: str
    description: Optional[str] = None
    can_create: bool = False
    can_read: bool = False
    can_update: bool = False
    can_delete: bool = False
    action_menu_id: Optional[int] = None
    action_menu_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class ActionMenuPermission(BaseModel):
    """Schema for action menu with CRUD permissions"""
    action_menu_id: int = Field(..., description="Action menu ID")
    can_create: bool = Field(False, description="Permission to create")
    can_read: bool = Field(False, description="Permission to read")
    can_update: bool = Field(False, description="Permission to update")
    can_delete: bool = Field(False, description="Permission to delete")

class RoleCreate(BaseModel):
    """Schema for creating a new role"""
    name: str = Field(..., min_length=1, max_length=255, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    action_menu_permissions: List[ActionMenuPermission] = Field(..., description="List of action menus with their CRUD permissions")
    user_ids: List[int] = Field(default_factory=list, description="List of user IDs to assign to this role")
    status: int = Field(1, description="Role status (1=Active, 2=Inactive)")

class RoleUpdate(BaseModel):
    """Schema for updating an existing role"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    action_menu_permissions: Optional[List[ActionMenuPermission]] = Field(None, description="List of action menus with their CRUD permissions")
    user_ids: Optional[List[int]] = Field(None, description="List of user IDs to assign to this role")
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
    status_name: Optional[str] = None
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
    status_name: Optional[str] = None
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