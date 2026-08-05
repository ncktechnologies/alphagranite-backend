import logging
from datetime import datetime
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.role import Role
from src.app.database.user import User
from src.app.database.file import File
from src.app.database.status import Status
from src.app.utils.config import API_BASE_URL
from src.app.database.user_role import UserRole
from src.app.utils.helpers import error_response, utc_now
from src.app.database.permission import Permission
from src.app.database.action_menu import ActionMenu
from src.app.service.background import save_audit_trail
from src.app.database.role_permission import RolePermission

class RoleService:
    """
    Service for managing roles and their permissions
    
    This service handles:
    - Creating roles with permissions
    - Updating roles and their permissions
    - Changing role status
    - Retrieving roles with or without their permissions
    - Checking if role names are unique
    """
    
    @staticmethod
    async def create_role(
        db: AsyncSession, 
        name: str, 
        description: Optional[str],
        action_menu_permissions: List[Dict[str, Any]],
        user_ids: List[int],
        status: int,
        current_user_id: int
    ):
        """
        Create a new role with action menu permissions and assign users
        
        Args:
            db: Database session
            name: Role name (must be unique)
            description: Optional role description
            action_menu_permissions: List of dicts with action_menu_id and CRUD flags
            user_ids: List of user IDs to assign to this role
            status: Role status (1=Active, 2=Inactive)
            current_user_id: ID of the user creating the role
            
        Returns:
            The created role with its associated permissions
            
        Raises:
            HTTPException: If role name already exists or if there are database errors
        """
     
        
        # Check if role name already exists
        existing_role = await db.execute(select(Role).where(Role.name == name))
        if existing_role.scalar_one_or_none():
            raise error_response(
                message=f"Role with name '{name}' already exists",
                status_code=400
            )
        
        # Verify all action menus exist
        action_menu_ids = [amp["action_menu_id"] for amp in action_menu_permissions]
        action_menus_result = await db.execute(
            select(ActionMenu).where(ActionMenu.id.in_(action_menu_ids))
        )
        action_menus = action_menus_result.scalars().all()
        
        if len(action_menus) != len(action_menu_ids):
            raise error_response(
                message="One or more action menu IDs do not exist",
                status_code=400
            )
        
        try:
            # Create new role
            new_role = Role(
                name=name,
                description=description,
                status=status,
                created_at=utc_now(),
                updated_at=utc_now()
            )
            
            db.add(new_role)
            await db.flush()  # Flush to get the new role ID
            
            # Create permissions and role_permission entries for each action menu
            created_permissions = []
            for amp in action_menu_permissions:
                action_menu_id = amp["action_menu_id"]
                
                # Get action menu name for permission naming
                action_menu = next((am for am in action_menus if am.id == action_menu_id), None)
                if not action_menu:
                    continue
                
                # Create permission name based on role and action menu
                permission_name = f"{name.lower().replace(' ', '_')}_{action_menu.code}_permission"
                
                # Create new permission
                permission = Permission(
                    name=permission_name,
                    description=f"{name} permission for {action_menu.name}",
                    can_create=amp["can_create"],
                    can_read=amp["can_read"],
                    can_update=amp["can_update"],
                    can_delete=amp["can_delete"],
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                db.add(permission)
                await db.flush()  # Get permission ID
                created_permissions.append(permission)
                
                # Create role_permission entry with action_menu_id
                role_permission = RolePermission(
                    role_id=new_role.id,
                    permission_id=permission.id,
                    action_menu_id=action_menu_id,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                db.add(role_permission)
            
            # Assign users to the role
            for user_id in user_ids:
                # Verify user exists
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    raise error_response(
                        message=f"User with ID {user_id} does not exist",
                        status_code=400
                    )
                
                # Check if user already has this role
                existing_user_role = await db.execute(
                    select(UserRole).where(
                        and_(UserRole.user_id == user_id, UserRole.role_id == new_role.id)
                    )
                )
                if not existing_user_role.scalar_one_or_none():
                    user_role = UserRole(
                        user_id=user_id,
                        role_id=new_role.id,
                        created_at=utc_now()
                    )
                    db.add(user_role)
            
            await db.commit()
            await db.refresh(new_role)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="role_created",
                user_id=current_user_id,
                message=f"Created role '{new_role.name}' (ID: {new_role.id})",
                activity_trace_id=new_role.id
            )
            
            # Retrieve role with permissions for response
            role_with_permissions = await RoleService.get_role_with_permissions(db, new_role.id)
            return role_with_permissions
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Database error: {str(e)}",
                status_code=400
            )
    
    @staticmethod
    async def update_role(
        db: AsyncSession,
        role_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        action_menu_permissions: Optional[List[dict]] = None,
        user_ids: Optional[List[int]] = None,
        permission_ids: Optional[List[int]] = None,
        status: Optional[int] = None,
        current_user_id: int = None
    ):
        """
        Update role with permissions and members
        
        This method updates a role's details including:
        - Basic info (name, description, status)
        - Permissions via action_menu_permissions or permission_ids
        - Members via user_ids
        """
        from sqlalchemy import select, delete, and_
        from src.app.database.role import Role
        from src.app.database.permission import Permission
        from src.app.database.role_permission import RolePermission
        from src.app.database.user_role import UserRole
        from src.app.database.action_menu import ActionMenu
        
        # Get existing role
        result = await db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        
        if not role:
            raise ValueError(f"Role with id {role_id} not found")
        
        # Check if new name is unique (if provided)
        if name and name != role.name:
            existing_result = await db.execute(
                select(Role).where(
                    and_(
                        Role.name == name,
                        Role.id != role_id
                    )
                )
            )
            if existing_result.scalar_one_or_none():
                raise ValueError(f"Role name '{name}' already exists")
        
        # Update basic fields
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if status is not None:
            role.status = status
        
        role.updated_at = utc_now()
        # role.updated_by = current_user_id
        
        # Handle permissions update via action_menu_permissions
        if action_menu_permissions is not None:
            # Delete existing role_permissions
            await db.execute(
                delete(RolePermission).where(RolePermission.role_id == role_id)
            )
            
            # Create or reuse permissions for each action menu
            for amp in action_menu_permissions:
                action_menu_id = amp.get("action_menu_id")
                can_create = amp.get("can_create", False)
                can_read = amp.get("can_read", False)
                can_update = amp.get("can_update", False)
                can_delete = amp.get("can_delete", False)
                
                # Get action menu name
                action_menu_result = await db.execute(
                    select(ActionMenu).where(ActionMenu.id == action_menu_id)
                )
                action_menu = action_menu_result.scalar_one_or_none()
                if not action_menu:
                    raise ValueError(f"Action menu with id {action_menu_id} not found")
                
                # Generate permission name
                permission_name = f"{role.name} - {action_menu.name}"
                
                # Check if permission with this name already exists
                existing_perm_result = await db.execute(
                    select(Permission).where(Permission.name == permission_name)
                )
                existing_permission = existing_perm_result.scalar_one_or_none()
                
                if existing_permission:
                    # Update existing permission
                    existing_permission.can_create = can_create
                    existing_permission.can_read = can_read
                    existing_permission.can_update = can_update
                    existing_permission.can_delete = can_delete
                    existing_permission.updated_at = utc_now()
                    permission = existing_permission
                else:
                    # Create new permission
                    permission = Permission(
                        name=permission_name,
                        description=f"Auto-generated permission for role {role.name}",
                        can_create=can_create,
                        can_read=can_read,
                        can_update=can_update,
                        can_delete=can_delete,
                        created_at=utc_now(),
                        updated_at=utc_now()
                    )
                    db.add(permission)
                    await db.flush()  # Flush to get permission.id
            
                # Create role_permission link
                role_permission = RolePermission(
                    role_id=role_id,
                    permission_id=permission.id,
                    action_menu_id=action_menu_id,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                db.add(role_permission)
    
        # Handle permissions update via permission_ids
        elif permission_ids is not None:
            # Delete existing role_permissions
            await db.execute(
                delete(RolePermission).where(RolePermission.role_id == role_id)
            )
            
            # Create new role_permission records
            for permission_id in permission_ids:
                # Verify permission exists
                perm_result = await db.execute(
                    select(Permission).where(Permission.id == permission_id)
                )
                if not perm_result.scalar_one_or_none():
                    raise ValueError(f"Permission with id {permission_id} not found")
                
                role_permission = RolePermission(
                    role_id=role_id,
                    permission_id=permission_id,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                db.add(role_permission)
    
        # Handle members update
        if user_ids is not None:
            new_member_ids = set(user_ids)

            # Enforce one-role-per-user: reject users already assigned to another role.
            conflicting_member_rows = await db.execute(
                select(
                    UserRole.user_id,
                    UserRole.role_id,
                    User.first_name,
                    User.last_name,
                    Role.name,
                )
                .join(User, User.id == UserRole.user_id)
                .join(Role, Role.id == UserRole.role_id)
                .where(
                    UserRole.user_id.in_(new_member_ids),
                    UserRole.role_id != role_id,
                )
            )
            conflicting_members = conflicting_member_rows.all()
            if conflicting_members:
                conflict_details = ", ".join(
                    [
                        (
                            f"{((first_name or '').strip() + ' ' + (last_name or '').strip()).strip() or f'User #{user_id}'} "
                            f"(role: {role_name or f'Role #{assigned_role_id}'})"
                        )
                        for user_id, assigned_role_id, first_name, last_name, role_name in conflicting_members
                    ]
                )
                raise ValueError(
                    "Cannot assign users who already have another role: "
                    f"{conflict_details}."
                )

            existing_member_rows = await db.execute(
                select(UserRole.user_id).where(UserRole.role_id == role_id)
            )
            existing_member_ids = {row[0] for row in existing_member_rows.all()}

            # Delete existing user_role assignments
            await db.execute(
                delete(UserRole).where(UserRole.role_id == role_id)
            )
            
            # Create new user_role records
            for user_id in new_member_ids:
                # Verify user exists
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                if not user_result.scalar_one_or_none():
                    raise ValueError(f"User with id {user_id} not found")
                
                user_role = UserRole(
                    user_id=user_id,
                    role_id=role_id,
                    created_at=utc_now()
                )
                db.add(user_role)

            # Keep users.role_id in sync for employee APIs that read direct role_id.
            if new_member_ids:
                await db.execute(
                    update(User)
                    .where(User.id.in_(new_member_ids))
                    .values(role_id=role_id, updated_at=utc_now())
                )

            removed_member_ids = existing_member_ids - new_member_ids
            for removed_user_id in removed_member_ids:
                fallback_role_result = await db.execute(
                    select(UserRole.role_id)
                    .where(UserRole.user_id == removed_user_id)
                    .order_by(UserRole.id.desc())
                    .limit(1)
                )
                fallback_role_id = fallback_role_result.scalar_one_or_none()

                await db.execute(
                    update(User)
                    .where(User.id == removed_user_id)
                    .values(role_id=fallback_role_id, updated_at=utc_now())
                )
    
        await db.commit()
        await db.refresh(role)
        
        # Return updated role with permissions and members
        return await RoleService.get_role_with_permissions(db, role_id)

    @staticmethod
    async def change_role_status(
        db: AsyncSession, 
        role_id: int, 
        status_id: int,
        current_user_id: int
    ):
        """
        Update role status (active, inactive)
        Status codes:
        1 - Active
        2 - Inactive
        
        Args:
            db: Database session
            role_id: ID of the role to update
            status_id: New status value
            current_user_id: ID of the user changing the status
            
        Returns:
            The updated role
            
        Raises:
            HTTPException: If role doesn't exist or if there are database errors
        """
        from src.app.service.background import save_audit_trail
        
        # Get existing role
        role_query = await db.execute(select(Role).where(Role.id == role_id))
        role = role_query.scalar_one_or_none()
        if not role:
            raise error_response(
                message=f"Role with ID {role_id} not found",
                status_code=404
            )
        
        try:
            # Update status
            old_status = role.status
            role.status = status_id
            role.updated_at = utc_now()
            
            db.add(role)
            await db.commit()
            await db.refresh(role)
            
            # Status name mapping
            status_names = {1: "active", 2: "inactive"}
            old_status_name = status_names.get(old_status, "unknown")
            new_status_name = status_names.get(status_id, "unknown")
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="role_status_changed",
                user_id=current_user_id,
                message=f"Changed status of role '{role.name}' (ID: {role.id}) from {old_status_name} to {new_status_name}",
                activity_trace_id=role.id
            )
            
            return role
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Database error: {str(e)}",
                status_code=400
            )
    
    @staticmethod
    async def get_role(db: AsyncSession, role_id: int):
        """
        Get role by ID
        
        Args:
            db: Database session
            role_id: ID of the role to retrieve
            
        Returns:
            The role with status name
            
        Raises:
            HTTPException: If role doesn't exist
        """
        role_query = await db.execute(
            select(Role, Status)
            .outerjoin(Status, Role.status == Status.value_id)
            .where(Role.id == role_id)
        )
        role_result = role_query.first()
        
        if not role_result:
            raise error_response(
                message=f"Role with ID {role_id} not found",
                status_code=404
            )
        
        role, status_obj = role_result
        
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "status": role.status,
            "status_name": status_obj.name if status_obj else None,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
        }
    
    @staticmethod
    async def get_role_with_permissions(db: AsyncSession, role_id: int):
        """
        Get role by ID with its associated permissions
        
        Args:
            db: Database session
            role_id: ID of the role to retrieve
            
        Returns:
            The role with its permissions
            
        Raises:
            HTTPException: If role doesn't exist
        """
        from src.app.database.action_menu import ActionMenu
        
        # Get the role with status
        role_query = await db.execute(
            select(Role, Status)
            .outerjoin(Status, Role.status == Status.value_id)
            .where(Role.id == role_id)
        )
        role_result = role_query.first()
        
        if not role_result:
            raise error_response(
                message=f"Role with ID {role_id} not found",
                status_code=404
            )
        
        role, status_obj = role_result

        # Load permissions with action menu info via the association table
        perm_stmt = (
            select(Permission, RolePermission, ActionMenu)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .outerjoin(ActionMenu, RolePermission.action_menu_id == ActionMenu.id)
            .where(RolePermission.role_id == role_id)
        )
        perm_result = await db.execute(perm_stmt)
        permission_rows = perm_result.all()

        # Build permissions list
        permissions = [
            {
                "id": p.id,
                "name": getattr(p, 'name', None),
                "description": getattr(p, 'description', None),
                "can_create": getattr(p, 'can_create', False),
                "can_read": getattr(p, 'can_read', False),
                "can_update": getattr(p, 'can_update', False),
                "can_delete": getattr(p, 'can_delete', False),
                "action_menu_id": rp.action_menu_id if rp else None,
                "action_menu_name": am.name if am else None,
            }
            for p, rp, am in permission_rows
        ]

        # Group permissions by action menu for action_permissions
        action_permissions = {}
        for p, rp, am in permission_rows:
            if am:  # Only include permissions with action menus
                menu_id = am.id
                if menu_id not in action_permissions:
                    action_permissions[menu_id] = {
                        "action_menu_id": menu_id,
                        "action_menu_name": am.name,
                        "can_create": False,
                        "can_read": False,
                        "can_update": False,
                        "can_delete": False,
                    }
                # Aggregate permissions for this action menu
                action_permissions[menu_id]["can_create"] = action_permissions[menu_id]["can_create"] or getattr(p, 'can_create', False)
                action_permissions[menu_id]["can_read"] = action_permissions[menu_id]["can_read"] or getattr(p, 'can_read', False)
                action_permissions[menu_id]["can_update"] = action_permissions[menu_id]["can_update"] or getattr(p, 'can_update', False)
                action_permissions[menu_id]["can_delete"] = action_permissions[menu_id]["can_delete"] or getattr(p, 'can_delete', False)

        # Return a serializable representation combining role and permissions
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "status": role.status,
            "status_name": status_obj.name if status_obj else None,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "permissions": permissions,
            "action_permissions": list(action_permissions.values())
        }
    
    @staticmethod
    async def get_roles(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100, 
        search: str = None, 
        status_id: int = None,
        sort_by: str = "id",
        sort_order: str = "asc"
    ):
        """
        Get roles with filtering options
        
        Args:
            db: Database session
            skip: Pagination offset
            limit: Pagination limit
            search: Search term for role name or description
            status_id: Filter by status
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
            
        Returns:
            List of roles with pagination info
        """
        # Build base query
        query = select(Role)
        
        # Apply filters if provided
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Role.name.ilike(search_term)) | 
                (Role.description.ilike(search_term))
            )
        
        if status_id:
            query = query.where(Role.status == status_id)
        
        # Count total roles with filters applied
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()
        
        # Apply sorting
        valid_sort_fields = {
            "id": Role.id,
            "name": Role.name,
            "created_at": Role.created_at,
            "updated_at": Role.updated_at,
            "status": Role.status
        }
        
        # Default to id if invalid sort field
        sort_field = valid_sort_fields.get(sort_by, Role.id)
        
        # Apply sort order
        if sort_order.lower() == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        roles = result.scalars().all()
        
        # Convert roles to dict for JSON serialization
        roles_data = [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "status": role.status,
                "created_at": role.created_at,
                "updated_at": role.updated_at
            }
            for role in roles
        ]
        
        return {
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "per_page": limit,
            "data": roles_data
        }
    
    @staticmethod
    async def is_role_name_unique(db: AsyncSession, name: str) -> bool:
        """
        Check if role name is unique
        
        Args:
            db: Database session
            name: Role name to check
            
        Returns:
            True if name is unique, False otherwise
        """
        result = await db.execute(select(Role).where(Role.name == name))
        existing_role = result.scalar_one_or_none()
        return existing_role is None
    
    @staticmethod
    async def get_roles_with_member_stats(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        status_id: int = None,
        sort_by: str = "id",
        sort_order: str = "asc"
    ):
        """
        Get roles with member statistics and a preview of members
        
        Args:
            db: Database session
            skip: Pagination offset
            limit: Pagination limit
            search: Search term for role name or description
            status_id: Filter by status
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
            
        Returns:
            List of roles with member statistics and preview
        """
        # Build base query for roles
        query = select(Role)
        
        # Apply filters if provided
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Role.name.ilike(search_term)) | 
                (Role.description.ilike(search_term))
            )
        
        if status_id:
            query = query.where(Role.status == status_id)
        
        # Count total roles with filters applied
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()
        
        # Apply sorting
        valid_sort_fields = {
            "id": Role.id,
            "name": Role.name,
            "created_at": Role.created_at,
            "updated_at": Role.updated_at,
            "status": Role.status
        }
        
        # Default to id if invalid sort field
        sort_field = valid_sort_fields.get(sort_by, Role.id)
        
        # Apply sort order
        if sort_order.lower() == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        roles = result.scalars().all()
        
        # For each role, get member count and all members with profile images
        role_data = []
        for role in roles:
            # Get total member count
            member_count_query = select(func.count()).where(UserRole.role_id == role.id)
            member_count_result = await db.execute(member_count_query)
            member_count = member_count_result.scalar_one()
            
            # Get all members with profile images (not just top 3)
            all_members_query = (
                select(User)
                .join(UserRole, User.id == UserRole.user_id)
                .where(UserRole.role_id == role.id)
            )
            all_members_result = await db.execute(all_members_query)
            all_members = all_members_result.scalars().all()
            
            # Create list of all members with profile images
            members_with_images = []
            for member in all_members:
                # Get profile image URL if available
                profile_image_url = None
                if member.profile_image_id:
                    file_query = select(File).where(File.id == member.profile_image_id)
                    file_result = await db.execute(file_query)
                    file = file_result.scalar_one_or_none()
                    if file:
                        profile_image_url = f"{API_BASE_URL}/static/uploads/{file.file_path}"
                
                members_with_images.append({
                    "id": member.id,
                    "username": member.username,
                    "email": member.email,
                    "first_name": member.first_name,
                    "last_name": member.last_name,
                    "department": member.department,
                    "status": member.status,
                    "profile_image_url": profile_image_url
                })
            
            # Combine data
            role_data.append({
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "status": role.status,
                "created_at": role.created_at,
                "updated_at": role.updated_at,
                "member_count": member_count,
                "members": members_with_images  # Changed from top_members to members
            })
        
        return {
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "per_page": limit,
            "data": role_data
        }
    
    @staticmethod
    async def get_role_with_members(
        db: AsyncSession,
        role_id: int,
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        status_id: int = None,
        sort_by: str = "first_name",
        sort_order: str = "asc"
    ):
        """
        Get role details with member information
        
        Args:
            db: Database session
            role_id: ID of the role to retrieve
            skip: Pagination offset for members
            limit: Pagination limit for members
            search: Search term for member name or email
            status_id: Filter members by status
            sort_by: Field to sort members by
            sort_order: Sort order (asc or desc)
            
        Returns:
            Role with detailed statistics and paginated member list
            
        Raises:
            HTTPException: If role doesn't exist
        """
        # Get role with status
        role_query = await db.execute(
            select(Role, Status)
            .outerjoin(Status, Role.status == Status.value_id)
            .where(Role.id == role_id)
        )
        role_result = role_query.first()
        
        if not role_result:
            raise error_response(
                message=f"Role with ID {role_id} not found",
                status_code=404
            )
        
        role, role_status = role_result
        logger = logging.getLogger("role_service")
        logger.info(f"[ROLE] Retrieved role id={role_id}: {role}")
        
        # Get member statistics
        # 1. Total members
        total_members_query = select(func.count()).select_from(
            select(UserRole).where(UserRole.role_id == role_id).subquery()
        )
        total_members_result = await db.execute(total_members_query)
        total_members = total_members_result.scalar_one()
        
        # 2. Active members
        active_members_query = select(func.count()).select_from(
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .where(and_(UserRole.role_id == role_id, User.status == 1))
            .subquery()
        )
        active_members_result = await db.execute(active_members_query)
        active_members = active_members_result.scalar_one()
        
        # 3. Pending members (users who haven't logged in yet)
        pending_members_query = select(func.count()).select_from(
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .where(and_(UserRole.role_id == role_id, User.is_first_login == True))
            .subquery()
        )
        pending_members_result = await db.execute(pending_members_query)
        pending_members = pending_members_result.scalar_one()
        
        # 4. Inactive members
        inactive_members_query = select(func.count()).select_from(
            select(User)
            .join(UserRole, User.id == UserRole.user_id)
            .where(and_(UserRole.role_id == role_id, User.status == 2))
            .subquery()
        )
        inactive_members_result = await db.execute(inactive_members_query)
        inactive_members = inactive_members_result.scalar_one()
        
        # Build query for members with status
        member_query = (
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                User.status,
                Status.name.label('status_name'),
                User.created_at.label('invited_at'),
                User.updated_at.label('last_login'),
                User.profile_image_id,
                File.file_path.label('profile_image_path')
            )
            .join(UserRole, User.id == UserRole.user_id)
            .outerjoin(File, User.profile_image_id == File.id)
            .outerjoin(Status, User.status == Status.value_id)
            .where(UserRole.role_id == role_id)
        )
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            member_query = member_query.where(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        if status_id:
            member_query = member_query.where(User.status == status_id)
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(member_query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()
        logger.info(f"[ROLE] member count SQL: {str(member_query)}; total_count={total_count}")
        
        # Apply sorting
        valid_sort_fields = {
            "id": User.id,
            "first_name": User.first_name,
            "last_name": User.last_name,
            "email": User.email,
            "status": User.status,
            "invited_at": User.created_at,
            "last_login": User.updated_at
        }
        
        # Default to first_name if invalid sort field
        sort_field = valid_sort_fields.get(sort_by, User.first_name)
        
        # Apply sort order
        if sort_order.lower() == "desc":
            member_query = member_query.order_by(sort_field.desc())
        else:
            member_query = member_query.order_by(sort_field.asc())
        
        # Apply pagination
        member_query = member_query.offset(skip).limit(limit)
        
        # Execute query
        members_result = await db.execute(member_query)
        members_raw = members_result.fetchall()
        logger.info(f"[ROLE] fetched {len(members_raw)} raw member rows")
        
        # Format member data
        members = []
        for member in members_raw:
            profile_image_url = None
            if member.profile_image_path:
                profile_image_url = f"{API_BASE_URL}/static/uploads/{member.profile_image_path}"
            
            members.append({
                "id": member.id,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "email": member.email,
                "status": member.status,
                "status_name": member.status_name if hasattr(member, 'status_name') else None,
                "invited_at": member.invited_at,
                "last_login": member.last_login,
                "profile_image_url": profile_image_url
            })
        
        # Get action_permissions for this role
        from src.app.database.action_menu import ActionMenu
        perm_stmt = (
            select(Permission, RolePermission, ActionMenu)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .outerjoin(ActionMenu, RolePermission.action_menu_id == ActionMenu.id)
            .where(RolePermission.role_id == role_id)
        )
        perm_result = await db.execute(perm_stmt)
        permission_rows = perm_result.all()
        
        # Group permissions by action menu for action_permissions
        action_permissions = {}
        for p, rp, am in permission_rows:
            if am:  # Only include permissions with action menus
                menu_id = am.id
                if menu_id not in action_permissions:
                    action_permissions[menu_id] = {
                        "action_menu_id": menu_id,
                        "action_menu_name": am.name,
                        "can_create": False,
                        "can_read": False,
                        "can_update": False,
                        "can_delete": False,
                    }
                # Aggregate permissions for this action menu
                action_permissions[menu_id]["can_create"] = action_permissions[menu_id]["can_create"] or getattr(p, 'can_create', False)
                action_permissions[menu_id]["can_read"] = action_permissions[menu_id]["can_read"] or getattr(p, 'can_read', False)
                action_permissions[menu_id]["can_update"] = action_permissions[menu_id]["can_update"] or getattr(p, 'can_update', False)
                action_permissions[menu_id]["can_delete"] = action_permissions[menu_id]["can_delete"] or getattr(p, 'can_delete', False)
        
        # Construct response
        response = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "status": role.status,
            "status_name": role_status.name if role_status else None,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "total_members": total_members,
            "active_members": active_members,
            "pending_members": pending_members,
            "inactive_members": inactive_members,
            "action_permissions": list(action_permissions.values()),
            "members": {
                "total": total_count,
                "page": skip // limit + 1 if limit > 0 else 1,
                "per_page": limit,
                "data": members
            }
        }
        
        return response
    
    @staticmethod
    async def delete_role(
        db: AsyncSession,
        role_id: int,
        current_user_id: int
    ):
        """
        Delete a role (hard delete)
        
        Args:
            db: Database session
            role_id: ID of the role to delete
            current_user_id: ID of the user deleting the role
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If role doesn't exist or if there are database errors
        """
        from src.app.service.background import save_audit_trail
        
        # Get existing role
        role_query = await db.execute(select(Role).where(Role.id == role_id))
        role = role_query.scalar_one_or_none()
        if not role:
            raise error_response(
                message=f"Role with ID {role_id} not found",
                status_code=404
            )

        # Guard: block deletion only when ACTIVE employees are still assigned.
        active_assigned_count_result = await db.execute(
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(UserRole, User.id == UserRole.user_id)
            .where(
                UserRole.role_id == role_id,
                User.status == 1,
            )
        )
        active_assigned_count = int(active_assigned_count_result.scalar() or 0)
        if active_assigned_count > 0:
            raise error_response(
                message=(
                    "Cannot delete role while active employees are still assigned. "
                    "Please unassign all employees from this role first."
                ),
                status_code=400,
            )
        
        try:
            # Cleanup any stale member links before deleting the role row.
            await db.execute(
                delete(UserRole).where(UserRole.role_id == role_id)
            )

            # Clear legacy direct role pointers on users.
            await db.execute(
                update(User)
                .where(User.role_id == role_id)
                .values(role_id=None)
            )

            # Cleanup role permissions and remove orphaned permissions that are
            # no longer linked to any role.
            role_permission_ids_result = await db.execute(
                select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
            )
            permission_ids = [pid for pid in role_permission_ids_result.scalars().all() if pid is not None]

            await db.execute(
                delete(RolePermission).where(RolePermission.role_id == role_id)
            )

            if permission_ids:
                referenced_permission_ids_result = await db.execute(
                    select(func.distinct(RolePermission.permission_id)).where(
                        RolePermission.permission_id.in_(permission_ids)
                    )
                )
                still_referenced = set(
                    pid for pid in referenced_permission_ids_result.scalars().all() if pid is not None
                )
                orphan_permission_ids = [pid for pid in permission_ids if pid not in still_referenced]
                if orphan_permission_ids:
                    await db.execute(
                        delete(Permission).where(Permission.id.in_(orphan_permission_ids))
                    )

            # Hard-delete the role row.
            await db.delete(role)
            await db.commit()
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="role_deleted",
                user_id=current_user_id,
                message=f"Deleted role '{role.name}' (ID: {role.id})",
                activity_trace_id=role.id
            )
            
            return {"message": f"Role '{role.name}' deleted successfully"}
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Database error: {str(e)}",
                status_code=400
            )
            
    @staticmethod
    async def deactivate_user(
        db: AsyncSession,
        user_id: int,
        current_user_id: int
    ):
        """
        Deactivate a user (set status to inactive)
        
        Args:
            db: Database session
            user_id: ID of the user to deactivate
            current_user_id: ID of the user performing the action
            
        Returns:
            The deactivated user
            
        Raises:
            HTTPException: If user doesn't exist or if there are database errors
        """
        from src.app.service.background import save_audit_trail
        
        # Get existing user
        user_query = await db.execute(select(User).where(User.id == user_id))
        user = user_query.scalar_one_or_none()
        if not user:
            raise error_response(
                message=f"User with ID {user_id} not found",
                status_code=404
            )
        
        try:
            # Update status to inactive (2)
            old_status = user.status
            user.status = 2  # 2 = Inactive
            user.updated_at = utc_now()
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="user_deactivated",
                user_id=current_user_id,
                message=f"Deactivated user {user.first_name} {user.last_name} (ID: {user.id})",
                activity_trace_id=user.id
            )
            
            return user
            
        except IntegrityError as e:
            await db.rollback()
            raise error_response(
                message=f"Database error: {str(e)}",
                status_code=400
            )