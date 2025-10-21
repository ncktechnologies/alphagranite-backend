from datetime import datetime
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database.role import Role
from src.app.database.user import User
from src.app.database.file import File
from src.app.utils.config import API_BASE_URL
from src.app.database.user_role import UserRole
from src.app.database.permission import Permission
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
        permission_ids: List[int], 
        status: int,
        current_user_id: int
    ):
        """
        Create a new role with the specified permissions
        
        Args:
            db: Database session
            name: Role name (must be unique)
            description: Optional role description
            permission_ids: List of permission IDs to associate with the role
            status: Role status (1=Active, 2=Inactive)
            current_user_id: ID of the user creating the role
            
        Returns:
            The created role with its associated permissions
            
        Raises:
            HTTPException: If role name already exists or if there are database errors
        """
        from src.app.service.background import save_audit_trail
        
        # Check if role name already exists
        existing_role = await db.execute(select(Role).where(Role.name == name))
        if existing_role.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{name}' already exists"
            )
        
        # Verify all permissions exist
        permissions_count = await db.execute(
            select(func.count(Permission.id)).where(Permission.id.in_(permission_ids))
        )
        if permissions_count.scalar_one() != len(permission_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more permission IDs do not exist"
            )
        
        try:
            # Create new role
            new_role = Role(
                name=name,
                description=description,
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(new_role)
            await db.flush()  # Flush to get the new role ID
            
            # Associate permissions with the role
            for permission_id in permission_ids:
                role_permission = RolePermission(
                    role_id=new_role.id,
                    permission_id=permission_id
                )
                db.add(role_permission)
            
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def update_role(
        db: AsyncSession, 
        role_id: int, 
        name: Optional[str] = None,
        description: Optional[str] = None, 
        permission_ids: Optional[List[int]] = None, 
        status: Optional[int] = None,
        current_user_id: int = None
    ):
        """
        Update an existing role
        
        Args:
            db: Database session
            role_id: ID of the role to update
            name: New role name (optional)
            description: New role description (optional)
            permission_ids: New list of permission IDs (optional)
            status: New role status (optional)
            current_user_id: ID of the user updating the role
            
        Returns:
            The updated role with its associated permissions
            
        Raises:
            HTTPException: If role doesn't exist, name is already taken, or if there are database errors
        """
        from src.app.service.background import save_audit_trail
        
        # Get existing role
        role_query = await db.execute(select(Role).where(Role.id == role_id))
        role = role_query.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        # Check if new name already exists (if name is being updated)
        if name and name != role.name:
            existing_role = await db.execute(select(Role).where(Role.name == name))
            if existing_role.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role with name '{name}' already exists"
                )
        
        try:
            # Update role fields if provided
            if name is not None:
                role.name = name
            if description is not None:
                role.description = description
            if status is not None:
                role.status = status
            
            role.updated_at = datetime.now()
            
            # Update permissions if provided
            if permission_ids is not None:
                # Verify all permissions exist
                permissions_count = await db.execute(
                    select(func.count(Permission.id)).where(Permission.id.in_(permission_ids))
                )
                if permissions_count.scalar_one() != len(permission_ids):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more permission IDs do not exist"
                    )
                
                # Delete existing role_permissions
                await db.execute(
                    select(RolePermission).where(RolePermission.role_id == role_id).delete()
                )
                
                # Create new role_permissions
                for permission_id in permission_ids:
                    role_permission = RolePermission(
                        role_id=role_id,
                        permission_id=permission_id
                    )
                    db.add(role_permission)
            
            await db.commit()
            await db.refresh(role)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="role_updated",
                user_id=current_user_id,
                message=f"Updated role '{role.name}' (ID: {role.id})",
                activity_trace_id=role.id
            )
            
            # Retrieve role with permissions for response
            role_with_permissions = await RoleService.get_role_with_permissions(db, role_id)
            return role_with_permissions
            
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
    
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        try:
            # Update status
            old_status = role.status
            role.status = status_id
            role.updated_at = datetime.now()
            
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def get_role(db: AsyncSession, role_id: int):
        """
        Get role by ID
        
        Args:
            db: Database session
            role_id: ID of the role to retrieve
            
        Returns:
            The role
            
        Raises:
            HTTPException: If role doesn't exist
        """
        role_query = await db.execute(select(Role).where(Role.id == role_id))
        role = role_query.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        return role
    
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
        # Query the role with permissions
        stmt = (
            select(Role)
            .options(joinedload(Role.permissions))
            .where(Role.id == role_id)
        )
        result = await db.execute(stmt)
        role = result.scalar_one_or_none()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        return role
    
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
        
        return {
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "per_page": limit,
            "data": roles
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
        
        # For each role, get member count and top 3 members with profile images
        role_data = []
        for role in roles:
            # Get total member count
            member_count_query = select(func.count()).where(UserRole.role_id == role.id)
            member_count_result = await db.execute(member_count_query)
            member_count = member_count_result.scalar_one()
            
            # Get top 3 members with profile images
            top_members_query = (
                select(User)
                .join(UserRole, User.id == UserRole.user_id)
                .where(UserRole.role_id == role.id)
                .limit(3)
            )
            top_members_result = await db.execute(top_members_query)
            top_members = top_members_result.scalars().all()
            
            # Create list of members with profile images
            members_with_images = []
            for member in top_members:
                # Get profile image URL if available
                profile_image_url = None
                if member.profile_image_id:
                    file_query = select(File).where(File.id == member.profile_image_id)
                    file_result = await db.execute(file_query)
                    file = file_result.scalar_one_or_none()
                    if file:
                        profile_image_url = f"{API_BASE_URL}/static/uploads/{file.path}"
                
                members_with_images.append({
                    "id": member.id,
                    "first_name": member.first_name,
                    "last_name": member.last_name,
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
                "top_members": members_with_images
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
        # Get role
        role_query = await db.execute(select(Role).where(Role.id == role_id))
        role = role_query.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
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
        
        # Build query for members
        member_query = (
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                User.status,
                User.created_at.label('invited_at'),
                User.last_login,
                User.profile_image_id,
                File.path.label('profile_image_path')
            )
            .join(UserRole, User.id == UserRole.user_id)
            .outerjoin(File, User.profile_image_id == File.id)
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
        
        # Apply sorting
        valid_sort_fields = {
            "id": User.id,
            "first_name": User.first_name,
            "last_name": User.last_name,
            "email": User.email,
            "status": User.status,
            "invited_at": User.created_at,
            "last_login": User.last_login
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
                "invited_at": member.invited_at,
                "last_login": member.last_login,
                "profile_image_url": profile_image_url
            })
        
        # Construct response
        response = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "status": role.status,
            "created_at": role.created_at,
            "updated_at": role.updated_at,
            "total_members": total_members,
            "active_members": active_members,
            "pending_members": pending_members,
            "inactive_members": inactive_members,
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
        Delete a role (set status to deleted)
        
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        try:
            # Update status to deleted (3)
            old_status = role.status
            role.status = 3  # 3 = Deleted
            role.updated_at = datetime.now()
            
            db.add(role)
            await db.commit()
            await db.refresh(role)
            
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        try:
            # Update status to inactive (2)
            old_status = user.status
            user.status = 2  # 2 = Inactive
            user.updated_at = datetime.now()
            
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )