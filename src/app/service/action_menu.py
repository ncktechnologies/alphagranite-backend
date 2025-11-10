from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.utils.helpers import error_response
from src.app.database.permission import Permission
from src.app.database.action_menu import ActionMenu


class ActionMenuService:
    """Service for managing action menus"""
    
    @staticmethod
    async def create_action_menu(
        db: AsyncSession,
        name: str,
        code: str,
        current_user_id: int
    ):
        """
        Create a new action menu
        
        Args:
            db: Database session
            name: Action menu name
            code: Action menu code (unique)
            current_user_id: ID of the user creating the action menu
            
        Returns:
            The created action menu
            
        Raises:
            error_response: If code already exists
        """
        from src.app.service.background import save_audit_trail
        
        # Check if code already exists
        existing = await db.execute(select(ActionMenu).where(ActionMenu.code == code))
        if existing.scalar_one_or_none():
            raise error_response(
                message=f"Action menu with code '{code}' already exists",
                status_code=400
            )
        
        try:
            new_action_menu = ActionMenu(
                name=name,
                code=code,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(new_action_menu)
            await db.commit()
            await db.refresh(new_action_menu)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="action_menu_created",
                user_id=current_user_id,
                message=f"Created action menu '{new_action_menu.name}' (ID: {new_action_menu.id})",
                activity_trace_id=new_action_menu.id
            )
            
            return new_action_menu
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Database error: {str(e)}",
                status_code=400
            )
    
    @staticmethod
    async def get_action_menu(db: AsyncSession, action_menu_id: int):
        """Get action menu by ID"""
        result = await db.execute(select(ActionMenu).where(ActionMenu.id == action_menu_id))
        action_menu = result.scalar_one_or_none()
        if not action_menu:
            raise error_response(
                message=f"Action menu with ID {action_menu_id} not found",
                status_code=404
            )
        return action_menu
    
    @staticmethod
    async def get_all_action_menus(db: AsyncSession):
        """Get all action menus"""
        result = await db.execute(select(ActionMenu).order_by(ActionMenu.name))
        action_menus = result.scalars().all()
        return [
            {
                "id": am.id,
                "name": am.name,
                "code": am.code,
                "created_at": am.created_at,
                "updated_at": am.updated_at
            }
            for am in action_menus
        ]
    
    @staticmethod
    async def update_action_menu(
        db: AsyncSession,
        action_menu_id: int,
        name: Optional[str] = None,
        code: Optional[str] = None,
        current_user_id: int = None
    ):
        """Update an existing action menu"""
        from src.app.service.background import save_audit_trail
        
        # Get existing action menu
        result = await db.execute(select(ActionMenu).where(ActionMenu.id == action_menu_id))
        action_menu = result.scalar_one_or_none()
        if not action_menu:
            raise error_response(
                message=f"Action menu with ID {action_menu_id} not found",
                status_code=404
            )
        
        # Check if new code already exists (if code is being updated)
        if code and code != action_menu.code:
            existing = await db.execute(select(ActionMenu).where(ActionMenu.code == code))
            if existing.scalar_one_or_none():
                raise error_response(
                    message=f"Action menu with code '{code}' already exists",
                    status_code=400
                )
        
        try:
            if name is not None:
                action_menu.name = name
            if code is not None:
                action_menu.code = code
            
            action_menu.updated_at = datetime.now()
            
            await db.commit()
            await db.refresh(action_menu)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="action_menu_updated",
                user_id=current_user_id,
                message=f"Updated action menu '{action_menu.name}' (ID: {action_menu.id})",
                activity_trace_id=action_menu.id
            )
            
            return action_menu
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Database error: {str(e)}",
                status_code=400
            )
    
    @staticmethod
    async def delete_action_menu(
        db: AsyncSession,
        action_menu_id: int,
        current_user_id: int
    ):
        """Delete an action menu"""
        from src.app.service.background import save_audit_trail
        
        # Get existing action menu
        result = await db.execute(select(ActionMenu).where(ActionMenu.id == action_menu_id))
        action_menu = result.scalar_one_or_none()
        if not action_menu:
            raise error_response(
                message=f"Action menu with ID {action_menu_id} not found",
                status_code=404
            )
        
        try:
            await db.delete(action_menu)
            await db.commit()
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="action_menu_deleted",
                user_id=current_user_id,
                message=f"Deleted action menu '{action_menu.name}' (ID: {action_menu.id})",
                activity_trace_id=action_menu.id
            )
            
            return {"message": f"Action menu '{action_menu.name}' deleted successfully"}
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Cannot delete action menu. It may be in use by permissions.",
                status_code=400
            )


class PermissionService:
    """Service for managing permissions"""
    
    @staticmethod
    async def create_permission(
        db: AsyncSession,
        name: str,
        description: Optional[str],
        can_create: bool,
        can_read: bool,
        can_update: bool,
        can_delete: bool,
        current_user_id: int
    ):
        """Create a new permission"""
        from src.app.service.background import save_audit_trail
        
        # Check if name already exists
        existing = await db.execute(select(Permission).where(Permission.name == name))
        if existing.scalar_one_or_none():
            raise error_response(
                message=f"Permission with name '{name}' already exists",
                status_code=400
            )
        
        try:
            new_permission = Permission(
                name=name,
                description=description,
                can_create=can_create,
                can_read=can_read,
                can_update=can_update,
                can_delete=can_delete,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(new_permission)
            await db.commit()
            await db.refresh(new_permission)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="permission_created",
                user_id=current_user_id,
                message=f"Created permission '{new_permission.name}' (ID: {new_permission.id})",
                activity_trace_id=new_permission.id
            )
            
            return new_permission
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Database error: {str(e)}",
                status_code=400
            )
    
    @staticmethod
    async def get_permission(db: AsyncSession, permission_id: int):
        """Get permission by ID"""
        result = await db.execute(select(Permission).where(Permission.id == permission_id))
        permission = result.scalar_one_or_none()
        if not permission:
            raise error_response(
                message=f"Permission with ID {permission_id} not found",
                status_code=404
            )
        return permission
    
    @staticmethod
    async def get_all_permissions(db: AsyncSession):
        """Get all permissions"""
        result = await db.execute(select(Permission).order_by(Permission.name))
        permissions = result.scalars().all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "can_create": p.can_create,
                "can_read": p.can_read,
                "can_update": p.can_update,
                "can_delete": p.can_delete,
                "created_at": p.created_at,
                "updated_at": p.updated_at
            }
            for p in permissions
        ]
    
    @staticmethod
    async def update_permission(
        db: AsyncSession,
        permission_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        can_create: Optional[bool] = None,
        can_read: Optional[bool] = None,
        can_update: Optional[bool] = None,
        can_delete: Optional[bool] = None,
        current_user_id: int = None
    ):
        """Update an existing permission"""
        from src.app.service.background import save_audit_trail
        
        # Get existing permission
        result = await db.execute(select(Permission).where(Permission.id == permission_id))
        permission = result.scalar_one_or_none()
        if not permission:
            raise error_response(
                message=f"Permission with ID {permission_id} not found",
                status_code=404
            )
        
        # Check if new name already exists (if name is being updated)
        if name and name != permission.name:
            existing = await db.execute(select(Permission).where(Permission.name == name))
            if existing.scalar_one_or_none():
                raise error_response(
                    message=f"Permission with name '{name}' already exists",
                    status_code=400
                )
        
        try:
            if name is not None:
                permission.name = name
            if description is not None:
                permission.description = description
            if can_create is not None:
                permission.can_create = can_create
            if can_read is not None:
                permission.can_read = can_read
            if can_update is not None:
                permission.can_update = can_update
            if can_delete is not None:
                permission.can_delete = can_delete
            
            permission.updated_at = datetime.now()
            
            await db.commit()
            await db.refresh(permission)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="permission_updated",
                user_id=current_user_id,
                message=f"Updated permission '{permission.name}' (ID: {permission.id})",
                activity_trace_id=permission.id
            )
            
            return permission
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Database error: {str(e)}",
                status_code=400
            )
    
    @staticmethod
    async def delete_permission(
        db: AsyncSession,
        permission_id: int,
        current_user_id: int
    ):
        """Delete a permission"""
        from src.app.service.background import save_audit_trail
        
        # Get existing permission
        result = await db.execute(select(Permission).where(Permission.id == permission_id))
        permission = result.scalar_one_or_none()
        if not permission:
            raise error_response(
                message=f"Permission with ID {permission_id} not found",
                status_code=404
            )
        
        try:
            await db.delete(permission)
            await db.commit()
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="permission_deleted",
                user_id=current_user_id,
                message=f"Deleted permission '{permission.name}' (ID: {permission.id})",
                activity_trace_id=permission.id
            )
            
            return {"message": f"Permission '{permission.name}' deleted successfully"}
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Cannot delete permission. It may be assigned to roles.",
                status_code=400
            )
