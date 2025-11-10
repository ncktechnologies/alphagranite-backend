from sqlalchemy import select
from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends

if TYPE_CHECKING:
    from src.app.database.user import User


def PermissionChecker(resource: str, action: str):
    from src.app.utils.config import get_db
    from src.app.routers.auth import get_current_user
    
    async def dependency(
        db: AsyncSession = Depends(get_db),
        current_user: "User" = Depends(get_current_user)
    ) -> "User":
        from src.app.database.permission import Permission
        from src.app.database.action_menu import ActionMenu
        from src.app.database.role_permission import RolePermission
        
        if current_user.is_super_admin:
            return current_user

        if not current_user.role_id:
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

        result = await db.execute(
            select(RolePermission, Permission)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(
                RolePermission.role_id == current_user.role_id,
                RolePermission.action_menu_id == action_menu.id
            )
        )
        role_permission = result.first()

        if not role_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to resource '{resource}'"
            )

        _, permission = role_permission
        action_map = {
            "create": permission.can_create,
            "read": permission.can_read,
            "update": permission.can_update,
            "delete": permission.can_delete,
        }

        if action not in action_map or not action_map[action]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: cannot {action} {resource}"
            )

        return current_user
    
    return dependency
