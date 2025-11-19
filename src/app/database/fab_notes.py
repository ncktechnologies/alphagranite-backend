from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, Text


class FabNotes(SQLModel, table=True):
    """
    Notes for FABs at different workflow stages.
    Tracks all notes added to a FAB with stage context and user attribution.
    """
    __tablename__ = "fab_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    fab_id: int = Field(foreign_key="fabs.id", index=True)
    stage: str = Field(max_length=255, index=True, description="Workflow stage when note was added")
    note: str = Field(sa_column=Column(Text), description="Note content")
    created_by: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
