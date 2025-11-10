from sqlmodel import update
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any, Tuple

from src.app.database.user import User
from src.app.database.status import Status
from src.app.database.department import Department
from src.app.database.audit_trail import AuditTrail
from src.app.interface.department_schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentStatusChange,
)


class DepartmentService:
    @staticmethod
    async def create_department(
        db: AsyncSession,
        data: DepartmentCreate,
        user_id: int
    ) -> Department:
        """
        Create a new department with status set to active (status=1)
        """
        # Check if department with the same name already exists
        query = select(Department).where(Department.name == data.name)
        result = await db.execute(query)
        existing_department = result.scalar_one_or_none()

        if existing_department:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Department with name '{data.name}' already exists"
            )

        # Create new department (status 1 is typically "active")
        new_department = Department(
            name=data.name,
            description=data.description,
            status=1  # Active status
        )
        db.add(new_department)
        await db.commit()
        await db.refresh(new_department)

        # Add audit trail entry
        audit_entry = AuditTrail(
            activity_message=f"Created department '{data.name}'",
            user_id=user_id,
            activity_table_name="departments",
            record_id=new_department.id
        )
        db.add(audit_entry)
        await db.commit()

        return new_department

    @staticmethod
    async def update_department(
        db: AsyncSession,
        department_id: int,
        data: DepartmentUpdate,
        user_id: int
    ) -> Department:
        """
        Update an existing department
        """
        # Check if department exists
        query = select(Department).where(Department.id == department_id)
        result = await db.execute(query)
        department = result.scalar_one_or_none()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found"
            )

        # Check if updating to a name that already exists (except for this department)
        if data.name:
            name_query = select(Department).where(
                and_(Department.name == data.name, Department.id != department_id)
            )
            name_result = await db.execute(name_query)
            existing_name = name_result.scalar_one_or_none()

            if existing_name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Department with name '{data.name}' already exists"
                )

        # Update department fields
        update_data = {}
        activity_message_parts = []

        if data.name is not None and data.name != department.name:
            update_data["name"] = data.name
            activity_message_parts.append(f"name from '{department.name}' to '{data.name}'")

        if data.description is not None and data.description != department.description:
            update_data["description"] = data.description
            activity_message_parts.append("description")

        if update_data:
            update_data["updated_at"] = func.now()
            query = update(Department).where(Department.id == department_id).values(**update_data)
            await db.execute(query)

            # Refresh department data
            refresh_query = select(Department).where(Department.id == department_id)
            result = await db.execute(refresh_query)
            department = result.scalar_one()

            # Add audit trail entry
            activity_message = f"Updated department {department.id}: {', '.join(activity_message_parts)}"
            audit_entry = AuditTrail(
                activity_message=activity_message,
                user_id=user_id,
                activity_table_name="departments",
                record_id=department_id
            )
            db.add(audit_entry)
            await db.commit()

        return department

    @staticmethod
    async def change_department_status(
        db: AsyncSession,
        department_id: int,
        status_data: DepartmentStatusChange,
        user_id: int
    ) -> Department:
        """
        Change the status of a department
        """
        # Check if department exists
        query = select(Department).where(Department.id == department_id)
        result = await db.execute(query)
        department = result.scalar_one_or_none()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found"
            )

        # Get status information
        status_query = select(Status).where(Status.value_id == status_data.status)
        status_result = await db.execute(status_query)
        status_obj = status_result.scalar_one_or_none()

        if not status_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value: {status_data.status}"
            )

        old_status = department.status
        if old_status == status_data.status:
            return department  # No change needed

        # Check if department has users before deactivating or deleting
        if status_data.status == 2 or status_data.status == 3:  # Assuming 2=inactive, 3=deleted
            user_count_query = select(func.count(User.id)).where(User.department == department_id)
            user_count_result = await db.execute(user_count_query)
            user_count = user_count_result.scalar_one()

            if user_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot change status. Department has {user_count} assigned users. Please reassign users first."
                )

        # Update the status
        query = update(Department).where(Department.id == department_id).values(
            status=status_data.status,
            updated_at=func.now()
        )
        await db.execute(query)

        # Get the updated department
        refresh_query = select(Department).where(Department.id == department_id)
        result = await db.execute(refresh_query)
        department = result.scalar_one()

        # Get status information for audit trail
        old_status_query = select(Status).where(Status.value_id == old_status)
        old_status_result = await db.execute(old_status_query)
        old_status_obj = old_status_result.scalar_one_or_none()

        old_status_name = old_status_obj.name if old_status_obj else f"Unknown ({old_status})"
        new_status_name = status_obj.name

        # Add audit trail entry
        audit_entry = AuditTrail(
            activity_message=f"Changed department '{department.name}' status from {old_status_name} to {new_status_name}",
            user_id=user_id,
            activity_table_name="departments",
            record_id=department_id
        )
        db.add(audit_entry)
        await db.commit()

        return department

    @staticmethod
    async def delete_department(
        db: AsyncSession,
        department_id: int,
        user_id: int
    ) -> Dict[str, str]:
        """
        Delete a department (soft delete by changing status)
        """
        # Check if department exists
        query = select(Department).where(Department.id == department_id)
        result = await db.execute(query)
        department = result.scalar_one_or_none()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found"
            )

        # Check if department has users
        user_count_query = select(func.count(User.id)).where(User.department == department_id)
        user_count_result = await db.execute(user_count_query)
        user_count = user_count_result.scalar_one()

        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete department. {user_count} users are still assigned to this department."
            )

        # Delete the department (set status to deleted, assuming status=3 is 'deleted')
        query = update(Department).where(Department.id == department_id).values(
            status=3,  # Deleted status
            updated_at=func.now()
        )
        await db.execute(query)

        # Add audit trail entry
        audit_entry = AuditTrail(
            activity_message=f"Deleted department '{department.name}'",
            user_id=user_id,
            activity_table_name="departments",
            record_id=department_id
        )
        db.add(audit_entry)
        await db.commit()

        return {"message": f"Department '{department.name}' has been deleted"}

    @staticmethod
    async def get_departments_list(
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        status_filter: Optional[int] = 1
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get a list of departments with user samples and counts
        """
        # Start with base query
        query = select(Department)
        
        # Apply status filter if provided
        if status_filter is not None:
            query = query.filter(Department.status == status_filter)
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)
        
        # Execute query to get departments
        result = await db.execute(query)
        departments = result.scalars().all()

        # Load status lookup once to avoid repeated queries
        statuses_res = await db.execute(select(Status))
        statuses = {s.value_id: s.name for s in statuses_res.scalars().all()}

    # For each department, get member count and sample members
        department_data = []
        for dept in departments:
            # Get user count
            user_count_query = select(func.count(User.id)).where(
                User.department == dept.id
            )
            user_count_result = await db.execute(user_count_query)
            user_count = user_count_result.scalar_one()
            
            # Get sample users (up to 5)
            users_query = select(User).where(
                User.department == dept.id
            ).limit(5)
            users_result = await db.execute(users_query)
            sample_users = users_result.scalars().all()
            
            # Format user data
            sample_members = [
                {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "profile_image_id": user.profile_image_id
                }
                for user in sample_users
            ]
            
            # Resolve status name if available
            status_name = statuses.get(dept.status)

            # Create department summary
            department_data.append({
                "id": dept.id,
                "name": dept.name,
                "description": dept.description,
                "status": dept.status,
                "status_name": status_name,
                "total_members": user_count,
                "sample_members": sample_members
            })
        
        return department_data, total_count

    @staticmethod
    async def get_department_details(
        db: AsyncSession,
        department_id: int
    ) -> Dict[str, Any]:
        """
        Get details of a specific department including all its users
        """
        # Check if department exists
        query = select(Department).where(Department.id == department_id)
        result = await db.execute(query)
        department = result.scalar_one_or_none()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found"
            )

        # Get all users in this department (full user data)
        users_query = select(User).where(User.department == department_id)
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()

        # Load status lookup
        statuses_res = await db.execute(select(Status))
        statuses = {s.value_id: s.name for s in statuses_res.scalars().all()}

        # Format user data with status_name where applicable
        user_data = [
            {
                "id": user.id,
                "employee_id": user.employee_id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "department": user.department,
                "home_address": user.home_address,
                "gender": user.gender,
                "profile_image_id": user.profile_image_id,
                "status": user.status,
                "status_name": statuses.get(user.status),
                "role_id": user.role_id,
                "is_super_admin": user.is_super_admin,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            for user in users
        ]

        # Create department details with status_name
        department_data = {
            "id": department.id,
            "name": department.name,
            "description": department.description,
            "status": department.status,
            "status_name": statuses.get(department.status),
            "created_at": department.created_at,
            "updated_at": department.updated_at,
            "users": user_data,
            "total_members": len(user_data)
        }

        return department_data

    @staticmethod
    async def get_department_users(
        db: AsyncSession,
        department_id: int,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        gender: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], int, int]:
        """
        Get users in a specific department with pagination and filtering
        """
        # Check if department exists
        dept_query = select(Department).where(Department.id == department_id)
        dept_result = await db.execute(dept_query)
        department = dept_result.scalar_one_or_none()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found"
            )

        # Start building the users query
        query = select(User).where(User.department == department_id)

        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        # Apply gender filter if provided
        if gender:
            query = query.filter(User.gender == gender)

        # Apply sorting
        if sort_by:
            if sort_by not in ["first_name", "last_name", "email", "gender", "created_at"]:
                sort_by = "created_at"  # Default sort field
            
            if sort_order and sort_order.lower() == "desc":
                query = query.order_by(getattr(User, sort_by).desc())
            else:
                query = query.order_by(getattr(User, sort_by).asc())
        else:
            # Default sorting
            query = query.order_by(User.first_name.asc())

        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar_one()

        # Calculate total pages
        total_pages = (total_count + size - 1) // size

        # Apply pagination
        query = query.offset((page - 1) * size).limit(size)

        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()

        # Load status lookup (for department and users)
        statuses_res = await db.execute(select(Status))
        statuses = {s.value_id: s.name for s in statuses_res.scalars().all()}

        # Format user data
        user_data = [
            {
                "id": user.id,
                "employee_id": user.employee_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "home_address": user.home_address,
                "gender": user.gender,
                "profile_image_id": user.profile_image_id,
                "created_at": user.created_at,
                "phone": user.phone,
                "status": user.status,
                "status_name": statuses.get(user.status)
            }
            for user in users
        ]

        # Create department info including status_name
        department_info = {
            "department_id": department.id,
            "department_name": department.name,
            "department_description": department.description,
            "status": department.status,
            "status_name": statuses.get(department.status)
        }

        return department_info, user_data, total_count, total_pages

    @staticmethod
    async def get_statuses(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Return all available statuses as a list of {value_id, name, slug}.
        """
        result = await db.execute(select(Status))
        rows = result.scalars().all()
        return [
            {"value_id": r.value_id, "name": r.name, "slug": r.slug}
            for r in rows
        ]