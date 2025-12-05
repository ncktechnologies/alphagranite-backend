from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Path, Query, BackgroundTasks, HTTPException

from src.app.database.user import User
from src.app.utils.config import get_db
from src.app.service.role import RoleService
from src.app.routers.auth import get_current_user
from src.app.utils.permissions import PermissionChecker 
from src.app.utils.helpers import call_service, success_response 
from src.app.interface.role_schemas import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithStats,
    RoleWithMembers,
    RoleStatusUpdate,
    UserStatusUpdate,
    RoleListResponse,
    RoleWithPermissions,
    RoleMembersResponse,
    ActionMenuPermission,
)
from sqlalchemy import select, func
from src.app.database.user_role import UserRole

role_router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    responses={404: {"description": "Not found"}},
)

@role_router.post("")
async def create_role(
    data: RoleCreate,
    current_user: User = Depends(PermissionChecker("roles", "create")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new role with action menu permissions and assign users
    
    This endpoint creates a new role with permissions for multiple action menus.
    The role name must be unique.
    
    The request body should include:
    - name: Role name (must be unique)
    - description: Optional role description
    - action_menu_permissions: List of action menus with CRUD permissions
      - Each item contains: action_menu_id, can_create, can_read, can_update, can_delete
    - user_ids: List of user IDs to assign to this role
    - status: Role status (1=Active, 2=Inactive)
    
    The backend will:
    1. Create permission records for each action menu
    2. Create the role
    3. Create role_permission records linking role + permission + action_menu
    4. Assign users to the role via user_role records
    """
    # Convert Pydantic models to dicts for service layer
    action_menu_permissions_dicts = [amp.dict() for amp in data.action_menu_permissions]
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.create_role,
        db=db,
        name=data.name,
        description=data.description,
        action_menu_permissions=action_menu_permissions_dicts,
        user_ids=data.user_ids,
        status=data.status,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=result,
        message="Role created successfully"
    )

@role_router.get("/{role_id}")
async def get_role(
    role_id: int = Path(..., ge=1),
    with_permissions: bool = Query(True, description="Include permissions in response"),
    with_members: bool = Query(True, description="Include members in response"),
    skip: int = Query(0, ge=0, description="Number of members to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Number of members to return"),
    search: str = Query(None, description="Search members by name or email"),
    status_id: int = Query(None, description="Filter members by status"),
    sort_by: str = Query("first_name", description="Field to sort members by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    current_user: User = Depends(PermissionChecker("roles", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get role details by ID with permissions and members
    
    This endpoint retrieves a role by its ID with:
    - Basic role information (name, description, status, dates)
    - Permissions list (if with_permissions=True)
    - Member statistics (total, active, inactive, pending)
    - Paginated members list (if with_members=True)
    
    Query Parameters:
    - with_permissions: Include role permissions (default: True)
    - with_members: Include members list (default: True)
    - skip: Pagination offset for members
    - limit: Number of members per page
    - search: Search members by name or email
    - status_id: Filter members by status
    - sort_by: Sort field (first_name, last_name, email, status, invited_at, last_login)
    - sort_order: Sort direction (asc/desc)
    """
    
    # Get role with members and stats
    if with_members:
        result = await call_service(
            RoleService.get_role_with_members,
            db=db,
            role_id=role_id,
            skip=skip,
            limit=limit,
            search=search,
            status_id=status_id,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Add permissions if requested
        if with_permissions:
            permissions_result = await call_service(
                RoleService.get_role_with_permissions,
                db=db,
                role_id=role_id
            )
            result["permissions"] = permissions_result.get("permissions", [])
    
    elif with_permissions:
        result = await call_service(
            RoleService.get_role_with_permissions,
            db=db,
            role_id=role_id
        )
    else:
        result = await call_service(
            RoleService.get_role,
            db=db,
            role_id=role_id
        )
    
    return success_response(
        data=result,
        message="Role retrieved successfully"
    )

def permission_denied(message: str, status_code: int = 403):
    """Helper to raise permission denied errors with consistent format"""
    raise HTTPException(status_code=status_code, detail=message)


@role_router.put("/{role_id}")
async def update_role(
    data: RoleUpdate,
    role_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update role details
    
    This endpoint updates a role's details including its permissions and members.
    You can update any combination of fields:
    - name: New role name (must be unique)
    - description: New role description
    - action_menu_permissions: New list of action menus with CRUD permissions
    - user_ids: New list of user IDs to assign to this role
    - permission_ids: New list of permission IDs (alternative to action_menu_permissions)
    - status: New role status (1=Active, 2=Inactive)
    
    Permission Requirements:
    - User must have can_update=True for "roles" action menu
    - If updating action_menu_permissions, user must have can_create=True for "roles" action menu
    - If updating user_ids (assigning/removing members), user must have can_create=True for "roles" action menu
    """
    from src.app.utils.permissions import has_permission
    
    # Check if user has update permission for roles
    has_update = await has_permission(
        db=db,
        user_id=current_user.id,
        action_menu_name="roles",
        permission_type="update"
    )
    
    if not has_update:
        permission_denied("You don't have permission to update roles")
    
    # Check if user is trying to update permissions or members
    is_updating_permissions = data.action_menu_permissions is not None or data.permission_ids is not None
    is_updating_members = data.user_ids is not None
    
    # If updating permissions or members, check for create permission
    if is_updating_permissions or is_updating_members:
        has_create = await has_permission(
            db=db,
            user_id=current_user.id,
            action_menu_name="roles",
            permission_type="create"
        )
        
        if not has_create:
            error_parts = []
            if is_updating_permissions:
                error_parts.append("modify role permissions")
            if is_updating_members:
                error_parts.append("assign/remove role members")
            
            error_message = f"You don't have permission to {' and '.join(error_parts)}. You need 'can_create' permission for roles."
            permission_denied(error_message)
    
    # Convert action_menu_permissions to dicts if provided
    action_menu_permissions_dicts = None
    if data.action_menu_permissions:
        action_menu_permissions_dicts = [amp.dict() for amp in data.action_menu_permissions]
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.update_role,
        db=db,
        role_id=role_id,
        name=data.name,
        description=data.description,
        action_menu_permissions=action_menu_permissions_dicts,
        user_ids=data.user_ids,
        permission_ids=data.permission_ids,
        status=data.status,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=result,
        message="Role updated successfully"
    )

@role_router.patch("/{role_id}/status")
async def update_role_status(
    data: RoleStatusUpdate,
    role_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("roles", "update")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update role status
    
    This endpoint updates a role's status.
    Status codes:
    - 1: Active
    - 2: Inactive
    """
    # current_user is provided by Depends(get_current_user)
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.change_role_status,
        db=db,
        role_id=role_id,
        status_id=data.status,
        current_user_id=current_user.id
    )
    
    # Get status name for message
    status_names = {1: "Active", 2: "Inactive"}
    status_name = status_names.get(data.status, "Updated")
    
    return success_response(
        data=result,
        message=f"Role status changed to {status_name} successfully"
    )

@role_router.get("")
async def get_roles(
    current_user: User = Depends(PermissionChecker("roles", "read")),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for role name or description"),
    status_id: Optional[int] = Query(None, description="Filter by status ID (1=Active, 2=Inactive)"),
    sort_by: Optional[str] = Query("id", description="Field to sort by (id, name, created_at, updated_at, status)"),
    sort_order: Optional[str] = Query("asc", description="Sort order (asc, desc)"),
    with_stats: bool = Query(False, description="Include member statistics and top members in the response"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of roles with pagination and filtering
    
    This endpoint returns a paginated list of roles with various filtering options.
    You can adjust the number of items per page using the limit parameter.
    
    Filter options include:
    - Search by name/description
    - Filter by status
    - Sort by various fields in ascending or descending order
    - Include member statistics and top members
    """
    # current_user is provided by Depends(get_current_user)
    
    # Call service using helper for error handling
    if with_stats:
        result = await call_service(
            RoleService.get_roles_with_member_stats,
            db=db,
            skip=skip,
            limit=limit,
            search=search,
            status_id=status_id,
            sort_by=sort_by,
            sort_order=sort_order
        )
    else:
        result = await call_service(
            RoleService.get_roles,
            db=db,
            skip=skip,
            limit=limit,
            search=search,
            status_id=status_id,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    return success_response(
        data=result,
        message="Roles retrieved successfully"
    )

@role_router.get("/check-name/{name}")
async def check_role_name_unique(
    name: str,
    current_user: User = Depends(PermissionChecker("roles", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if role name is unique
    
    Returns {"unique": true/false}
    """
    # current_user is provided by Depends(get_current_user)
    
    # Call service to check if name is unique
    is_unique = await call_service(
        RoleService.is_role_name_unique,
        db=db,
        name=name
    )
    
    return success_response(
        data={"unique": is_unique},
        message="Role name uniqueness check completed"
    )

@role_router.delete("/{role_id}")
async def delete_role(
    current_user: User = Depends(PermissionChecker("roles", "delete")),
    role_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a role
    
    This endpoint deletes a role by setting its status to deleted (3).
    The role will no longer be visible in normal role listings.
    """
    # current_user is provided by Depends(get_current_user)
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.delete_role,
        db=db,
        role_id=role_id,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=None,
        message=f"Role deleted successfully"
    )

@role_router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    current_user: User = Depends(PermissionChecker("roles", "update")),
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user
    
    This endpoint deactivates a user by setting their status to inactive (2).
    The user will no longer be able to log in.
    """
    # current_user is provided by Depends(get_current_user)
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.deactivate_user,
        db=db,
        user_id=user_id,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=result,
        message=f"User deactivated successfully"
    )

@role_router.get("/{role_id}/members")
async def get_role_with_members(
    current_user: User = Depends(PermissionChecker("roles", "read")),
    role_id: int = Path(..., ge=1),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search term for member name or email"),
    status_id: Optional[int] = Query(None, description="Filter members by status ID (1=Active, 2=Inactive)"),
    sort_by: Optional[str] = Query("first_name", description="Field to sort by (id, first_name, last_name, email, status, invited_at, last_login)"),
    sort_order: Optional[str] = Query("asc", description="Sort order (asc, desc)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get role details with member information
    
    This endpoint returns detailed information about a role including:
    - Role details (name, description, status, creation date)
    - Member statistics (total, active, pending, inactive)
    - Paginated list of members with their details
    
    Filter options for members include:
    - Search by name or email
    - Filter by status
    - Sort by various fields in ascending or descending order
    """
    # current_user is provided by Depends(get_current_user)
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.get_role_with_members,
        db=db,
        role_id=role_id,
        skip=skip,
        limit=limit,
        search=search,
        status_id=status_id,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return success_response(
        data=result,
        message="Role with members retrieved successfully"
    )


@role_router.get("/{role_id}/debug-members")
async def debug_role_members(
    role_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("roles", "read")),
    db: AsyncSession = Depends(get_db)
):
    """
    Debug endpoint: return raw UserRole rows and joined user info for a role.
    Use this to confirm which users are assigned to a role in the database.
    """
  

    # Get raw user_role rows for this role
    query = select(UserRole, User).join(User, User.id == UserRole.user_id).where(UserRole.role_id == role_id)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for ur, u in rows:
        items.append({
            "user_role_id": ur.id,
            "user_id": ur.user_id,
            "role_id": ur.role_id,
            "assigned_at": getattr(ur, "created_at", None),
            "user": {
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "status": u.status,
            }
        })

    count_res = await db.execute(select(func.count()).select_from(UserRole).where(UserRole.role_id == role_id))
    total = count_res.scalar_one()

    return success_response(data={"total": total, "rows": items}, message="Debug user_role rows for role returned")
