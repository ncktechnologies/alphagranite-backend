"""
Fab Type model for fabrication types.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, func


class FabTypeBase(SQLModel):
    """Base model for fab types"""
    name: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None)


class FabType(FabTypeBase, table=True):
    """Fab type table model"""
    __tablename__ = "fab_type"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=False), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), onupdate=func.now()),
    )


class FabTypeResponse(FabTypeBase):
    """Response model for fab types"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]