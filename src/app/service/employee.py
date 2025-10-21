import re
import bcrypt
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from src.app.database.user import User  # User and Employee are in the same tablemployee are in the same table
from src.app.utils.constants import (
    MSG_EMAIL_EXISTS,
    MSG_EMPLOYEE_EXISTS,
    MSG_EMPLOYEE_NOT_FOUND,
)

# This service handles employee operations using the shared User table
# Both users and employees are stored in the same database table


class EmployeeService:
    """
    Service for managing employees in the system
    
    All operations are performed on the User table since employees and users
    share the same underlying data structure. The difference is primarily in how
    they are created, managed, and what roles/permissions they have in the system.
    """
    
    @staticmethod
    def generate_username(first_name: str, last_name: str, db: Session) -> str:
        """
        Generate a unique username based on first and last name
        Format: first letter of first name + last name + number if necessary
        Example: John Doe -> jdoe, Jane Doe -> jdoe1
        """
        base_username = f"{first_name[0].lower()}{last_name.lower()}"
        # Replace spaces and special characters
        username = re.sub(r'[^a-z0-9]', '', base_username)
        
        # Check if username exists
        counter = 0
        unique_username = username
        while db.query(User).filter(User.username == unique_username).first():
            counter += 1
            unique_username = f"{username}{counter}"
        
        return unique_username
    
    @staticmethod
    def generate_random_password() -> str:
        """
        Generate a random secure password with:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        - Minimum length of 8
        """
        import random
        import string     
        
        # Define character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*"
        
        # Ensure at least one of each type
        password = [
            random.choice(uppercase),
            random.choice(lowercase),
            random.choice(digits),
            random.choice(special)
        ]
        
        # Fill up to desired length (12 characters)
        all_chars = uppercase + lowercase + digits + special
        password.extend(random.choice(all_chars) for _ in range(8))
        
        # Shuffle for randomness
        random.shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    async def create_employee(db: Session, data, current_user_id: int, background_tasks):
        """
        Create a new employee with generated username and password
        
        Note: Employees are stored in the same 'users' table as regular users,
        they are differentiated by roles and permissions.
        
        Steps:
        1. Check if email is unique
        2. Generate username
        3. Generate random password
        4. Create user record in the users table
        5. Send welcome email with credentials
        6. Create audit log
        """
        from src.app.service.background import save_audit_trail, send_notification

        # Check if email exists
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=MSG_EMAIL_EXISTS)
        
        # Generate username and password
        username = EmployeeService.generate_username(data.first_name, data.last_name, db)
        password = EmployeeService.generate_random_password()
        
        # Hash password
        password_bytes = password.encode('utf-8')[:72]  # Ensure max 72 bytes for bcrypt
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
        
        # Create new user
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
                profile_image_id=data.profile_image_id,
                role_id=data.role_id,
                status=1,  # Active
                is_super_admin=False,
                is_first_login=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(new_employee)
            db.commit()
            db.refresh(new_employee)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="employee_created",
                user_id=current_user_id,
                message=f"Created employee {new_employee.username} (ID: {new_employee.id})",
                activity_trace_id=new_employee.id
            )
            
            # Send welcome email with credentials
            email_body = f"""
            Welcome to Alpha Granite!
            
            Your account has been created. Here are your login credentials:
            
            Username: {username}
            Password: {password}
            
            Please login and change your password immediately.
            
            Best regards,
            The Alpha Granite Team
            """
            
            # Send notification
            await send_notification(
                db=db,
                email=data.email,
                title="Your Alpha Granite Account",
                body=email_body,
                user_id=current_user_id
            )
            
            # Return employee without password
            return new_employee
            
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def update_employee(db: Session, employee_id: int, data, current_user_id: int, profile_image_id=None):
        """
        Update employee details
        
        Args:
            db: Database session
            employee_id: ID of employee to update
            data: EmployeeUpdate data object
            current_user_id: ID of user making the update
            profile_image_id: Optional ID of uploaded profile image
        """
        from src.app.service.background import save_audit_trail
        
        # Find employee
        employee = db.query(User).filter(User.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_EMPLOYEE_NOT_FOUND)
        
        # Update fields if provided
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
        if data.gender is not None:
            employee.gender = data.gender
        if data.home_address is not None:
            employee.home_address = data.home_address
        if profile_image_id is not None:
            employee.profile_image_id = profile_image_id
        if data.role_id is not None:
            employee.role_id = data.role_id
        
        employee.updated_at = datetime.now()
        
        try:
            db.add(employee)
            db.commit()
            db.refresh(employee)
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="employee_updated",
                user_id=current_user_id,
                message=f"Updated employee {employee.username} (ID: {employee.id})",
                activity_trace_id=employee.id
            )
            
            return employee
            
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def update_employee_status(db: Session, employee_id: int, status_id: int, current_user_id: int, background_tasks):
        """
        Update employee status (active, inactive, deleted)
        Status codes:
        1 - Active
        2 - Inactive
        3 - Deleted
        """
        from src.app.service.background import save_audit_trail, send_notification
        
        # Find employee
        employee = db.query(User).filter(User.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_EMPLOYEE_NOT_FOUND)
        
        # Update status
        old_status = employee.status
        employee.status = status_id
        employee.updated_at = datetime.now()
        
        try:
            db.add(employee)
            db.commit()
            db.refresh(employee)
            
            # Status name mapping
            status_names = {1: "active", 2: "inactive", 3: "deleted"}
            old_status_name = status_names.get(old_status, "unknown")
            new_status_name = status_names.get(status_id, "unknown")
            
            # Save audit trail
            await save_audit_trail(
                db=db,
                activity="employee_status_changed",
                user_id=current_user_id,
                message=f"Changed status of employee {employee.username} (ID: {employee.id}) from {old_status_name} to {new_status_name}",
                activity_trace_id=employee.id
            )
            
            # Send notification to admin
            admin_email_body = f"""
            Employee status changed:
            
            Employee: {employee.first_name} {employee.last_name} ({employee.username})
            Status changed from {old_status_name} to {new_status_name}
            """
            
            # Get super admin emails
            super_admins = db.query(User).filter(User.is_super_admin == True).all()
            
            # Send notifications to super admins
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
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Database error: {str(e)}"
            )
    
    @staticmethod
    async def get_employee(db: Session, employee_id: int):
        """Get employee by ID"""
        employee = db.query(User).filter(User.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_EMPLOYEE_NOT_FOUND)
        return employee
    
    @staticmethod
    async def get_employees(
        db: Session, 
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
        """
        Get employees with filtering options
        - skip: pagination offset
        - limit: pagination limit
        - search: search term for first name, last name, email, or username
        - department_id: filter by department
        - status_id: filter by status
        - role_id: filter by role
        - email: filter by exact email
        - phone: filter by phone number
        - sort_by: field to sort by
        - sort_order: asc or desc
        """
        query = db.query(User)
        
        # Apply filters if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.username.ilike(search_term))
            )
        
        if department_id:
            query = query.filter(User.department == department_id)
        
        if status_id:
            query = query.filter(User.status == status_id)
            
        if role_id:
            query = query.filter(User.role_id == role_id)
            
        if email:
            query = query.filter(User.email == email)
            
        if phone:
            query = query.filter(User.phone.ilike(f"%{phone}%"))
        
        # Apply sorting
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
        
        # Default to id if invalid sort field
        sort_field = valid_sort_fields.get(sort_by, User.id)
        
        # Apply sort order
        if sort_order.lower() == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Get paginated results
        employees = query.offset(skip).limit(limit).all()
        
        return {
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "per_page": limit,
            "data": employees
        }

    @staticmethod
    def is_email_unique(db: Session, email: str) -> bool:
        """
        Check if email is unique in the system
        Returns True if email is unique (doesn't exist), False otherwise
        """
        existing_user = db.query(User).filter(User.email == email).first()
        return existing_user is None