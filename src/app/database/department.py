from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Department(SQLModel, table=True):
    __tablename__ = "departments"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: int = Field(foreign_key="status.value_id")
    # Relationships
    users: List["User"] = Relationship(back_populates="department_rel")
