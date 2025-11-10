from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.user import User
from src.app.utils.config import get_db
from src.app.routers.auth import get_current_user
from src.app.utils.permissions import PermissionChecker
from src.app.utils.helpers import call_service, success_response
from src.app.service.action_menu import ActionMenuService, PermissionService
from src.app.interface.action_menu_schemas import (
    ActionMenuCreate,
    ActionMenuUpdate,
    PermissionCreate,
    PermissionUpdate,
    ActionMenuResponse,
    PermissionResponse,
)

action_menu_router = APIRouter(
    prefix="/action-menus",
    tags=["action-menus"],
    responses={404: {"description": "Not found"}},
)

permission_router = APIRouter(
    prefix="/permissions",
    tags=["permissions"],
    responses={404: {"description": "Not found"}},
)


# ============ ACTION MENU ENDPOINTS ============

@action_menu_router.post("")
async def create_action_menu(
    data: ActionMenuCreate,
    current_user: User = Depends(PermissionChecker("action_menus", "create")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new action menu
    
    This endpoint creates a new action menu with a unique code.
    Action menus are used to group permissions for the frontend navigation.
    """
    result = await call_service(
        ActionMenuService.create_action_menu,
        db=db,
        name=data.name,
        code=data.code,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=result,
        message="Action menu created successfully"
    )


@action_menu_router.get("")
async def get_all_action_menus(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all action menus
    
    This endpoint returns all action menus in the system.
    Use this to populate dropdowns when creating/editing roles and permissions.
    """
    result = await call_service(
        ActionMenuService.get_all_action_menus,
        db=db
    )
    
    return success_response(
        data=result,
        message="Action menus retrieved successfully"
    )


@action_menu_router.get("/{action_menu_id}")
async def get_action_menu(
    action_menu_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("action_menus", "read")),
    db: AsyncSession = Depends(get_db)
):
    """Get action menu by ID"""
    result = await call_service(
        ActionMenuService.get_action_menu,
        db=db,
        action_menu_id=action_menu_id
    )
    
    return success_response(
        data=result,
        message="Action menu retrieved successfully"
    )


@action_menu_router.put("/{action_menu_id}")
async def update_action_menu(
    data: ActionMenuUpdate,
    action_menu_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("action_menus", "update")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an action menu
    
    This endpoint updates an action menu's name and/or code.
    """
    result = await call_service(
        ActionMenuService.update_action_menu,
        db=db,
        action_menu_id=action_menu_id,
        name=data.name,
        code=data.code,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=result,
        message="Action menu updated successfully"
    )


@action_menu_router.delete("/{action_menu_id}")
async def delete_action_menu(
    action_menu_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("action_menus", "delete")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an action menu
    
    This endpoint deletes an action menu.
    It will fail if the action menu is in use by any permissions.
    """
    result = await call_service(
        ActionMenuService.delete_action_menu,
        db=db,
        action_menu_id=action_menu_id,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=None,
        message=result["message"]
    )


# ============ PERMISSION ENDPOINTS ============

@permission_router.post("")
async def create_permission(
    data: PermissionCreate,
    current_user: User = Depends(PermissionChecker("permissions", "create")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new permission
    
    This endpoint creates a new permission.
    Permissions define what actions can be performed (create, read, update, delete).
    """
    result = await call_service(
        PermissionService.create_permission,
        db=db,
        name=data.name,
        description=data.description,
        can_create=data.can_create,
        can_read=data.can_read,
        can_update=data.can_update,
        can_delete=data.can_delete,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=result,
        message="Permission created successfully"
    )


@permission_router.get("")
async def get_all_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all permissions
    
    This endpoint returns all permissions in the system.
    Use this to populate dropdowns when creating/editing roles.
    """
    result = await call_service(
        PermissionService.get_all_permissions,
        db=db
    )
    
    return success_response(
        data=result,
        message="Permissions retrieved successfully"
    )


@permission_router.get("/{permission_id}")
async def get_permission(
    permission_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("permissions", "read")),
    db: AsyncSession = Depends(get_db)
):
    """Get permission by ID"""
    result = await call_service(
        PermissionService.get_permission,
        db=db,
        permission_id=permission_id
    )
    
    return success_response(
        data=result,
        message="Permission retrieved successfully"
    )


@permission_router.put("/{permission_id}")
async def update_permission(
    data: PermissionUpdate,
    permission_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("permissions", "update")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a permission
    
    This endpoint updates a permission's details and capabilities.
    """
    result = await call_service(
        PermissionService.update_permission,
        db=db,
        permission_id=permission_id,
        name=data.name,
        description=data.description,
        can_create=data.can_create,
        can_read=data.can_read,
        can_update=data.can_update,
        can_delete=data.can_delete,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=result,
        message="Permission updated successfully"
    )


@permission_router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int = Path(..., ge=1),
    current_user: User = Depends(PermissionChecker("permissions", "delete")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a permission
    
    This endpoint deletes a permission.
    It will fail if the permission is assigned to any roles.
    """
    result = await call_service(
        PermissionService.delete_permission,
        db=db,
        permission_id=permission_id,
        current_user_id=current_user.id
    )
    
    return success_response(
        data=None,
        message=result["message"]
    )
