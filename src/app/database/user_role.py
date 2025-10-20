from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    role_id: int = Field(foreign_key="roles.id")
    created_at: datetime = Field(default_factory=datetime.now)
    update_at: datetime = Field(default_factory=datetime.now)
    # Relationships
    user: "User" = Relationship(back_populates="roles")
    role: "Role" = Relationship(back_populates="users")
