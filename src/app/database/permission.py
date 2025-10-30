from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .role import Role

class Permission(SQLModel, table=True):
    __tablename__ = "permissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=255)
    can_create: bool = Field(default=False)
    can_update: bool = Field(default=False)
    can_delete: bool = Field(default=False)
    can_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Roles relationship removed to avoid implicit many-to-many
    # configuration in models. Services should load roles/permissions
    # via explicit queries against the association table when needed.
