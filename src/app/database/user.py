from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    employee_id: UUID = Field(index=True)
    phone: Optional[str] = Field(default=None, max_length=255)
    email: str = Field(index=True, unique=True, max_length=255)
    home_address: Optional[str] = Field(default=None, max_length=255)
    gender: Optional[str] = Field(default=None, max_length=255)
    profile_image_id: Optional[int] = Field(default=None, foreign_key="files.id")
    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    department: int = Field(foreign_key="departments.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: int = Field(foreign_key="status.value_id")
    is_super_admin: bool = Field(default=False)
    password: str = Field(max_length=255)
    # Relationships
    roles: List["UserRole"] = Relationship(back_populates="users")
  