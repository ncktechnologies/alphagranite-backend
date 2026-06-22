from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ServiceLevelSetting(SQLModel, table=True):
    __tablename__ = "service_level_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Normalized fab_type string (e.g. "STANDARD", "AG REDO", "BASIC").
    # Use "DEFAULT" as a catch-all when no fab-type-specific row exists.
    fab_type: str = Field(index=True, max_length=100)

    # Stage display name matching the service-level report's _normalize_stage output.
    # Valid values: "Pre-Draft Review", "Drafting", "SCT", "SlabSmith",
    #               "Final Programming", "CNC", "Revisions"
    stage_name: str = Field(index=True, max_length=100)

    # Days at or below which the FAB is considered ON TRACK (green).
    target_days: float = Field(default=1.0, ge=0)

    # Additional days beyond target_days before turning RED (yellow window).
    # 0 means any overage immediately becomes red.
    at_risk_days: float = Field(default=0.0, ge=0)

    # False for fab types where SLA is not applicable (PUNCHOUT, RESURFACE, etc.).
    is_applicable: bool = Field(default=True)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)
    updated_by: Optional[int] = Field(default=None, foreign_key="users.id")
