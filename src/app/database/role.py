from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user_role import UserRole  # imported only for type checkers / IDEs

class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=255)
    status: int = Field(foreign_key="status.value_id")
    created_at: datetime = Field(default_factory=datetime.now)
    update_at: datetime = Field(default_factory=datetime.now)
    # Relationships
    users: List["UserRole"] = Relationship(back_populates="roles")
