from uuid import UUID
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import relationship as sa_relationship

if TYPE_CHECKING:
    from .user_role import UserRole
    from .department import Department
    from .job import JobApplication
    from .password_reset_otp import PasswordResetOTP

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    employee_id: UUID = Field(index=True)
    phone: Optional[str] = Field(default=None, max_length=255)
    email: str = Field(index=True, unique=True, max_length=255)
    home_address: Optional[str] = Field(default=None, max_length=255)
    gender: Optional[str] = Field(default=None, max_length=255)
    profile_image_id: Optional[int] = Field(default=None)
    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    department: int = Field(default=1, foreign_key="departments.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: int = Field(default=1)
    is_super_admin: bool = Field(default=False)
    password: str = Field(max_length=255)
    failed_login_attempts: int = Field(default=0)
    is_locked: bool = Field(default=False)
    locked_at: Optional[datetime] = Field(default=None)
    is_first_login: bool = Field(default=True)
    role_id: Optional[int] = Field(default=None)
    email_notifications_enabled: bool = Field(default=True)
    
    # Relationship to Department
    department_rel: Optional["Department"] = Relationship(back_populates="users")
    
    # Relationship to user_roles (association table)
    roles: Optional[List["UserRole"]] = Relationship(back_populates="user")
    
    # Relationship to job applications
    job_applications: Optional[List["JobApplication"]] = Relationship(back_populates="applicant")
    
    # Relationship to password reset OTPs using SQLAlchemy relationship
    password_reset_otps: Optional[List["PasswordResetOTP"]] = sa_relationship(
        "PasswordResetOTP",
        back_populates="user",
        cascade="all, delete-orphan"
    )
