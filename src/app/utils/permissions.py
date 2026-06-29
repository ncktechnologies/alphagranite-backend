from sqlalchemy import select
from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends

if TYPE_CHECKING:
    from src.app.database.user import User


# Define dependent resources for FAB creation
# If user has permission for the parent resource, they get READ access to dependent resources
FAB_DEPENDENT_RESOURCES = {
    "accounts", "stone_thickness", "stone_color", "stone_type", 
    "edges", "jobs", "employees"
}


def PermissionChecker(resource: str, action: str):
    from src.app.utils.config import get_db
    from src.app.routers.auth import get_current_user
    from src.app.database.user import User  # ✅ Import inside function
    
    async def dependency(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)  
    ) -> User:
        from src.app.database.permission import Permission
        from src.app.database.action_menu import ActionMenu
        from src.app.database.role_permission import RolePermission
        from src.app.database.user_role import UserRole
        
        if current_user.is_super_admin:
            return current_user

        # Get all role IDs for the user from user_roles table
        ur_result = await db.execute(
            select(UserRole.role_id).filter(UserRole.user_id == current_user.id)
        )
        role_ids = [row[0] for row in ur_result.all()]
        
        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned"
            )

        result = await db.execute(
            select(ActionMenu).where(ActionMenu.code == resource)
        )
        action_menu = result.scalars().first()
        
        if not action_menu:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Resource '{resource}' not found"
            )

        # Default baseline: any role-assigned employee can read Employees.
        if action_menu.code == "employees" and action == "read":
            return current_user

        # Check direct permissions for this resource across all user's roles
        result = await db.execute(
            select(RolePermission, Permission)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id.in_(role_ids),
                RolePermission.action_menu_id == action_menu.id
            )
        )
        role_permission = result.first()

        # If user has direct permission, check it
        if role_permission:
            _, permission = role_permission
            action_map = {
                "create": permission.can_create,
                "read": permission.can_read,
                "update": permission.can_update,
                "delete": permission.can_delete,
            }

            if action in action_map and action_map[action]:
                return current_user
        
        # Check for implicit permissions from FAB IDs
        # If user can create/read FAB IDs and the resource is a dependent resource, grant READ access
        if resource in FAB_DEPENDENT_RESOURCES and action == "read":
            # Check if user has fabids permission
            fabids_menu_result = await db.execute(
                select(ActionMenu).where(ActionMenu.code == "fabids")
            )
            fabids_menu = fabids_menu_result.scalars().first()
            
            if fabids_menu:
                # Check if user has fabids permission (create or read)
                fabids_perm_result = await db.execute(
                    select(RolePermission, Permission)
                    .join(Permission, RolePermission.permission_id == Permission.id)
                    .where(
                        RolePermission.role_id.in_(role_ids),
                        RolePermission.action_menu_id == fabids_menu.id
                    )
                )
                fabids_permission = fabids_perm_result.first()
                
                if fabids_permission:
                    _, perm = fabids_permission
                    # If user can create or read FAB IDs, grant READ access to dependent resources
                    if perm.can_create or perm.can_read:
                        return current_user

        # No permission found
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: cannot {action} {resource}"
        )

    return dependency


async def has_permission(
    db: AsyncSession,
    user_id: int,
    action_menu_name: str,
    permission_type: str  # "create", "read", "update", "delete"
) -> bool:
    """
    Check if a user has a specific permission for an action menu.
    
    Args:
        db: Database session
        user_id: ID of the user
        action_menu_name: Name of the action menu (e.g., "roles", "users")
        permission_type: Type of permission ("create", "read", "update", "delete")
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    from sqlalchemy import select, and_
    from src.app.database.user import User
    from src.app.database.role import Role
    from src.app.database.user_role import UserRole
    from src.app.database.role_permission import RolePermission
    from src.app.database.permission import Permission
    from src.app.database.action_menu import ActionMenu
    
    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        return False
    
    # Super admin has all permissions
    if user.is_super_admin:
        return True

    # Default baseline: any role-assigned employee can read Employees.
    if permission_type == "read" and str(action_menu_name).strip().lower() in {"employees", "employee"}:
        role_result = await db.execute(select(UserRole.role_id).where(UserRole.user_id == user_id))
        return bool(role_result.first())
    
    # Check if user has the permission through their role
    permission_column = f"can_{permission_type}"
    
    query = select(Permission).join(
        RolePermission, RolePermission.permission_id == Permission.id
    ).join(
        UserRole, UserRole.role_id == RolePermission.role_id
    ).join(
        ActionMenu, RolePermission.action_menu_id == ActionMenu.id
    ).where(
        and_(
            UserRole.user_id == user_id,
            ActionMenu.name == action_menu_name,
            getattr(Permission, permission_column) == True
        )
    )
    
    result = await db.execute(query)
    permission = result.scalar_one_or_none()
    
    return permission is not None
