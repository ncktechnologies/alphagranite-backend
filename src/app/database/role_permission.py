from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id")
    role_id: int = Field(foreign_key="roles.id")
    action_menu_id: int = Field(foreign_key="action_menus.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
