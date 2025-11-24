import re
import random
import string
import bcrypt
import logging
from uuid import uuid4
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from src.app.database.user import User
from src.app.database.status import Status
from src.app.database.user_role import UserRole
from src.app.database.department import Department
from src.app.utils.constants import (
    MSG_EMAIL_EXISTS,
    MSG_EMPLOYEE_EXISTS,
    MSG_EMPLOYEE_NOT_FOUND,
)
from src.app.service.background import save_audit_trail, send_notification

logger = logging.getLogger("employee_service")


class EmployeeService:
    
    @staticmethod
    async def generate_username(first_name: str, last_name: str, db: AsyncSession) -> str:
        base_username = f"{first_name[0].lower()}{last_name.lower()}"
        username = re.sub(r'[^a-z0-9]', '', base_username)
        
        counter = 0
        unique_username = username
        result = await db.execute(select(User).where(User.username == unique_username))
        while result.scalars().first():
            counter += 1
            unique_username = f"{username}{counter}"
            result = await db.execute(select(User).where(User.username == unique_username))
        
        return unique_username
    
    @staticmethod
    def generate_random_password() -> str:
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*"

        password = [
            random.choice(uppercase),
            random.choice(lowercase),
            random.choice(digits),
            random.choice(special),
        ]

        all_chars = uppercase + lowercase + digits + special
        password.extend(random.choice(all_chars) for _ in range(8))
        random.shuffle(password)

        return "".join(password)
    
    @staticmethod
    async def create_employee(db: AsyncSession, data, current_user_id: int, background_tasks, profile_image_id: Optional[int] = None):
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MSG_EMAIL_EXISTS)

        # Validate department exists
        dept_result = await db.execute(select(Department).where(Department.id == data.department))
        if not dept_result.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")

        # Use profile_image_id from data object if present, otherwise use parameter
        final_profile_image_id = data.profile_image_id if hasattr(data, 'profile_image_id') and data.profile_image_id is not None else profile_image_id
        
        username = await EmployeeService.generate_username(data.first_name, data.last_name, db)
        logger.info(f"[CREATE] Creating employee: email={data.email} username={username} profile_image_id={final_profile_image_id}")
        password = EmployeeService.generate_random_password()

        password_bytes = password.encode('utf-8')[:72]
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

        try:
            new_employee = User(
                username=username,
                email=data.email,
                password=hashed_password,
                employee_id=uuid4(),
                first_name=data.first_name,
                last_name=data.last_name,
                phone=data.phone,
                department=data.department,
                gender=data.gender,
                home_address=data.home_address,
                profile_image_id=final_profile_image_id,
                role_id=data.role_id,
                status=1,
                is_super_admin=False,
                is_first_login=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            db.add(new_employee)
            await db.commit()
            await db.refresh(new_employee)
            logger.info(f"[CREATE] Created employee object: id={getattr(new_employee, 'id', None)} username={getattr(new_employee, 'username', None)} repr={new_employee!r}")

            # Create UserRole entry if role_id is provided
            if data.role_id:
                try:
                    user_role = UserRole(
                        user_id=new_employee.id,
                        role_id=data.role_id,
                        created_at=datetime.now()
                    )
                    db.add(user_role)
                    await db.commit()
                    logger.info(f"[CREATE] Created UserRole for user {new_employee.id} with role {data.role_id}")
                except Exception as e:
                    logger.exception(f"[CREATE] Failed to create UserRole: {e}")
                    # Don't fail the employee creation if UserRole fails

            await save_audit_trail(
                db=db,
                activity="employee_created",
                user_id=current_user_id,
                message=f"Created employee {new_employee.username} (ID: {new_employee.id})",
                activity_trace_id=new_employee.id
            )

            if data.email:
                email_body = f"""
                Welcome to Alpha Granite!

                Your account has been created. Here are your login credentials:

                Username: {username}
                Password: {password}

                Please login and change your password immediately.

                Best regards,
                The Alpha Granite Team
                """

                await send_notification(
                    db=db,
                    email=data.email,
                    title="Your Alpha Granite Account",
                    body=email_body,
                    user_id=current_user_id
                )

            # Return employee with generated password
            return {
                "employee": new_employee,
                "password": password
            }

        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def update_employee(db: AsyncSession, employee_id: int, data, current_user_id: int, profile_image_id=None):
        # use module-level logger
        logger = logging.getLogger("employee_update")
        
        # Use profile_image_id from data object if present, otherwise use parameter
        final_profile_image_id = data.profile_image_id if hasattr(data, 'profile_image_id') and data.profile_image_id is not None else profile_image_id
        
        result = await db.execute(select(User).where(User.id == employee_id))
        employee = result.scalars().first()
        logger.info(f"[UPDATE] Fetched employee: {employee}")
        if not employee:
            logger.error(f"[UPDATE] Employee not found: {employee_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_EMPLOYEE_NOT_FOUND)
        
        # Validate department exists if being updated
        if data.department_id is not None:
            dept_result = await db.execute(select(Department).where(Department.id == data.department_id))
            if not dept_result.scalars().first():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")
        
        if data.first_name is not None:
            employee.first_name = data.first_name
        if data.last_name is not None:
            employee.last_name = data.last_name
        if data.email is not None:
            employee.email = data.email
        if data.phone_number is not None:
            employee.phone = data.phone_number
        if data.department_id is not None:
            employee.department = data.department_id
        if data.role_id is not None:
            employee.role_id = data.role_id
            # Update the role assignment in user_roles table
            try:
                # Check if UserRole already exists for this role
                ur_result = await db.execute(
                    select(UserRole).where(
                        UserRole.user_id == employee.id,
                        UserRole.role_id == data.role_id,
                    )
                )
                existing_ur = ur_result.scalars().first()
                if not existing_ur:
                    # Remove old role assignments (if you want single role per user)
                    # If you want multiple roles, comment out the delete section
                    delete_result = await db.execute(
                        select(UserRole).where(UserRole.user_id == employee.id)
                    )
                    old_roles = delete_result.scalars().all()
                    for old_role in old_roles:
                        await db.delete(old_role)
                    
                    # Add new role
                    new_user_role = UserRole(
                        user_id=employee.id,
                        role_id=data.role_id,
                        created_at=datetime.now(),
                    )
                    db.add(new_user_role)
                    logger.info(f"[UPDATE] Updated UserRole for user {employee.id} to role {data.role_id}")
            except Exception:
                # don't block the update if user_role insertion fails; log and continue
                logger.exception(f"Failed to update UserRole for user {employee.id} role {data.role_id}")
        
        # Update profile_image_id if provided (use final_profile_image_id which prioritizes data object)
        if final_profile_image_id is not None:
            employee.profile_image_id = final_profile_image_id
            logger.info(f"[UPDATE] Setting profile_image_id to {final_profile_image_id}")
        
        employee.updated_at = datetime.now()
        
        try:
            db.add(employee)
            await db.commit()
            await db.refresh(employee)
            logger.info(f"[UPDATE] Employee after update: {employee}")
            
            await save_audit_trail(
                db=db,
                activity="employee_updated",
                user_id=current_user_id,
                message=f"Updated employee {employee.username} (ID: {employee.id})",
                activity_trace_id=employee.id
            )
            
            return employee
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"[UPDATE] IntegrityError: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def update_employee_status(db: AsyncSession, employee_id: int, status_id: int, current_user_id: int, background_tasks):
        # save_audit_trail and send_notification imported at module top
        
        result = await db.execute(select(User).where(User.id == employee_id))
        employee = result.scalars().first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_EMPLOYEE_NOT_FOUND)
        
        old_status = employee.status
        employee.status = status_id
        employee.updated_at = datetime.now()
        
        try:
            db.add(employee)
            await db.commit()
            await db.refresh(employee)
            
            status_names = {1: "active", 2: "inactive", 3: "deleted"}
            old_status_name = status_names.get(old_status, "unknown")
            new_status_name = status_names.get(status_id, "unknown")
            
            await save_audit_trail(
                db=db,
                activity="employee_status_changed",
                user_id=current_user_id,
                message=f"Changed status of employee {employee.username} (ID: {employee.id}) from {old_status_name} to {new_status_name}",
                activity_trace_id=employee.id
            )
            
            admin_email_body = f"""
            Employee status changed:
            
            Employee: {employee.first_name} {employee.last_name} ({employee.username})
            Status changed from {old_status_name} to {new_status_name}
            """
            
            result = await db.execute(select(User).where(User.is_super_admin == True))
            super_admins = result.scalars().all()
            
            for admin in super_admins:
                await send_notification(
                    db=db,
                    email=admin.email,
                    title="Employee Status Change",
                    body=admin_email_body,
                    user_id=current_user_id
                )
            
            return employee
            
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
            
    @staticmethod
    async def toggle_employee_active_status(db: AsyncSession, employee_id: int, active: bool, current_user_id: int, background_tasks):
        status_id = 1 if active else 2
        return await EmployeeService.update_employee_status(
            db=db, 
            employee_id=employee_id,
            status_id=status_id,
            current_user_id=current_user_id,
            background_tasks=background_tasks
        )
        
    @staticmethod
    async def bulk_toggle_employee_active_status(db: AsyncSession, employee_ids: list[int], active: bool, current_user_id: int, background_tasks):
        # save_audit_trail imported at module top
        
        status_id = 1 if active else 2
        status_name = "active" if active else "inactive"
        
        success_ids = []
        failed_ids = []
        
        for emp_id in employee_ids:
            try:
                result = await db.execute(select(User).where(User.id == emp_id))
                employee = result.scalars().first()
                if not employee:
                    failed_ids.append(emp_id)
                    continue
                
                old_status = employee.status
                employee.status = status_id
                employee.updated_at = datetime.now()
                
                db.add(employee)
                success_ids.append(emp_id)
                
                await save_audit_trail(
                    db=db,
                    activity="employee_status_changed",
                    user_id=current_user_id,
                    message=f"Changed status of employee {employee.username} (ID: {employee.id}) to {status_name}",
                    activity_trace_id=employee.id
                )
                
            except Exception:
                failed_ids.append(emp_id)
        
        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database error: {str(e)}"
            )
        
        total = len(employee_ids)
        success_count = len(success_ids)
        message = f"Updated {success_count} of {total} employees to {status_name}"
        
        return {
            "success": success_ids,
            "failed": failed_ids,
            "message": message
        }
    
    @staticmethod
    async def get_employee(db: AsyncSession, employee_id: int):
        result = await db.execute(
            select(User, Department.name, Status.name)
            .join(Department, User.department == Department.id)
            .join(Status, User.status == Status.value_id)
            .where(User.id == employee_id)
        )
        row = result.first()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_EMPLOYEE_NOT_FOUND)
        employee, department_name, status_name = row
        employee_dict = employee.__dict__.copy()
        # Remove sensitive/internal fields
        for key in ["is_locked", "failed_login_attempts", "password"]:
            employee_dict.pop(key, None)
        employee_dict["department_name"] = department_name
        employee_dict["status_name"] = status_name
        return employee_dict
    
    @staticmethod
    async def get_employees(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100, 
        search: str = None, 
        department_id: int = None, 
        status_id: int = None,
        role_id: int = None,
        email: str = None,
        phone: str = None,
        sort_by: str = "id",
        sort_order: str = "asc"
    ):
       
        query = select(User, Department.name, Status.name)
        query = query.join(Department, User.department == Department.id)
        query = query.join(Status, User.status == Status.value_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
        
        if department_id:
            query = query.where(User.department == department_id)
        
        if status_id:
            query = query.where(User.status == status_id)
        
        if role_id:
            query = query.where(User.role_id == role_id)
        
        if email:
            query = query.where(User.email == email)
        
        if phone:
            query = query.where(User.phone.ilike(f"%{phone}%"))
        
        valid_sort_fields = {
            "id": User.id,
            "first_name": User.first_name,
            "last_name": User.last_name,
            "email": User.email,
            "created_at": User.created_at,
            "updated_at": User.updated_at,
            "username": User.username,
            "department": User.department,
            "status": User.status
        }
        
        sort_field = valid_sort_fields.get(sort_by, User.id)
        
        if sort_order.lower() == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        count_query = select(func.count()).select_from(User)
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
        if department_id:
            count_query = count_query.where(User.department == department_id)
        if status_id:
            count_query = count_query.where(User.status == status_id)
        if role_id:
            count_query = count_query.where(User.role_id == role_id)
        if email:
            count_query = count_query.where(User.email == email)
        if phone:
            count_query = count_query.where(User.phone.ilike(f"%{phone}%"))
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()
        employees = []
        for row in rows:
            employee, department_name, status_name = row
            employee_dict = employee.__dict__.copy()
            for key in ["is_locked", "failed_login_attempts", "password"]:
                employee_dict.pop(key, None)
            employee_dict["department_name"] = department_name
            employee_dict["status_name"] = status_name
            employees.append(employee_dict)
        
        return {
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "per_page": limit,
            "data": employees
        }

    @staticmethod
    async def is_email_unique(db: AsyncSession, email: str) -> bool:
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()
        return existing_user is None
