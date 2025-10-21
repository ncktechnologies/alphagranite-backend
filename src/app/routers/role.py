from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Request, Path, Query, BackgroundTasks

from src.app.utils.config import get_db
from src.app.service.role import RoleService
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
)

role_router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    responses={404: {"description": "Not found"}},
)

@role_router.post("")
async def create_role(
    request: Request,
    data: RoleCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new role with permissions
    
    This endpoint creates a new role with the specified permissions.
    The role name must be unique.
    
    The request body should include:
    - name: Role name (must be unique)
    - description: Optional role description
    - permission_ids: List of permission IDs to associate with the role
    - status: Role status (1=Active, 2=Inactive)
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.create_role,
        db=db,
        name=data.name,
        description=data.description,
        permission_ids=data.permission_ids,
        status=data.status,
        current_user_id=current_user["user_id"]
    )
    
    return success_response(
        data=result,
        message="Role created successfully"
    )

@role_router.get("/{role_id}")
async def get_role(
    request: Request,
    role_id: int = Path(..., ge=1),
    with_permissions: bool = Query(True, description="Include permissions in response"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get role details by ID
    
    This endpoint retrieves a role by its ID.
    If with_permissions is True (default), it will include the role's permissions in the response.
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    if with_permissions:
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

@role_router.put("/{role_id}")
async def update_role(
    request: Request,
    data: RoleUpdate,
    role_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Update role details
    
    This endpoint updates a role's details including its permissions.
    You can update any combination of fields:
    - name: New role name (must be unique)
    - description: New role description
    - permission_ids: New list of permission IDs
    - status: New role status (1=Active, 2=Inactive)
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.update_role,
        db=db,
        role_id=role_id,
        name=data.name,
        description=data.description,
        permission_ids=data.permission_ids,
        status=data.status,
        current_user_id=current_user["user_id"]
    )
    
    return success_response(
        data=result,
        message="Role updated successfully"
    )

@role_router.patch("/{role_id}/status")
async def update_role_status(
    request: Request,
    data: RoleStatusUpdate,
    role_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Update role status
    
    This endpoint updates a role's status.
    Status codes:
    - 1: Active
    - 2: Inactive
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.change_role_status,
        db=db,
        role_id=role_id,
        status_id=data.status,
        current_user_id=current_user["user_id"]
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
    request: Request,
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
    # Get current user from request state
    current_user = request.state.user
    
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
    request: Request,
    name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if role name is unique
    
    Returns {"unique": true/false}
    """
    # Get current user from request state
    current_user = request.state.user
    
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
    request: Request,
    role_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a role
    
    This endpoint deletes a role by setting its status to deleted (3).
    The role will no longer be visible in normal role listings.
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.delete_role,
        db=db,
        role_id=role_id,
        current_user_id=current_user["user_id"]
    )
    
    return success_response(
        data=None,
        message=f"Role deleted successfully"
    )

@role_router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    request: Request,
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user
    
    This endpoint deactivates a user by setting their status to inactive (2).
    The user will no longer be able to log in.
    """
    # Get current user from request state
    current_user = request.state.user
    
    # Call service using helper for error handling
    result = await call_service(
        RoleService.deactivate_user,
        db=db,
        user_id=user_id,
        current_user_id=current_user["user_id"]
    )
    
    return success_response(
        data=result,
        message=f"User deactivated successfully"
    )

@role_router.get("/{role_id}/members")
async def get_role_with_members(
    request: Request,
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
    # Get current user from request state
    current_user = request.state.user
    
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