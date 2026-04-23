from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class InstallerRateHistory(SQLModel, table=True):
    __tablename__ = "installer_rate_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    installer_id: int = Field(foreign_key="users.id", index=True)
    hourly_rate: float = Field(gt=0)
    effective_from: datetime = Field(index=True)
    effective_to: Optional[datetime] = Field(default=None, index=True)
    is_active: bool = Field(default=True, index=True)

    created_at: datetime = Field(default_factory=datetime.now)
    created_by: int = Field(foreign_key="users.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
