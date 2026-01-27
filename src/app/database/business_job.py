"""
Business Job model for work orders and project tracking.
This is separate from recruitment jobs in job.py
"""
from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field, Column, Integer, String, Text, DateTime, Date, Numeric, func
from decimal import Decimal
from sqlalchemy.orm import relationship


class BusinessJobBase(SQLModel):
    """Base model for business jobs (work orders)"""
    name: str = Field(max_length=255, index=True)
    job_number: str = Field(max_length=100, unique=True, index=True)
    account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    description: Optional[str] = Field(default=None, sa_type=Text)
    priority: Optional[str] = Field(default="Medium", max_length=50)
    start_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    due_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    project_value: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(15, 2)))
    status_id: int = Field(foreign_key="status.value_id")
    created_by: int = Field(foreign_key="users.id")
    sq_ft: Optional[float] = Field(  # NEW
        default=None
    )
    sales_person_id: Optional[int] = Field(  # NEW
        default=None,
        foreign_key="users.id"
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=False), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=False), onupdate=func.now()),
    )
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
    need_to_invoice: bool = Field(default=False)
    invoice_note: Optional[str] = Field(default=None, description="Note about invoice status")
    invoiced_at: Optional[datetime] = Field(default=None, description="Date the job was invoiced")  # NEW


class BusinessJob(BusinessJobBase, table=True):
    """Business job table model"""
    __tablename__ = "business_jobs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Add relationship to notes
    notes = relationship("JobNote", back_populates="job", cascade="all, delete-orphan")
