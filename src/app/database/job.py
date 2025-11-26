from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from enum import Enum as PyEnum
from sqlmodel import (
    SQLModel,
    Field,
    Column,
    JSON,
    Enum,
    Integer,
    ForeignKey,
    DateTime,
    func,
    String,
    Text,
    Boolean,
    Relationship,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import event, text

# --- Enums ---
class JobStatus(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class JobType(str, PyEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"


class ExperienceLevel(str, PyEnum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    EXECUTIVE = "executive"


class ApplicationStatus(str, PyEnum):
    APPLIED = "applied"
    REVIEW = "under_review"
    INTERVIEW = "interview"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# --- Job Models ---
class JobBase(SQLModel):
    name: str = Field(max_length=255, index=True)
    job_number: str = Field(max_length=100, unique=True, index=True)
    account_id: int = Field(foreign_key="accounts.id")
    description: str = Field(sa_type=Text)
    requirements: str = Field(sa_type=Text)
    responsibilities: str = Field(sa_type=Text)
    location: str = Field(max_length=255)
    job_type: JobType = Field(sa_column=Column(Enum(JobType)))
    experience_level: ExperienceLevel = Field(sa_column=Column(Enum(ExperienceLevel)))
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = Field(default="USD", max_length=3)
    is_remote: bool = Field(default=False)
    status: JobStatus = Field(sa_column=Column(Enum(JobStatus)), default=JobStatus.DRAFT)
    priority: Optional[str] = Field(max_length=50, default="Medium")

    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None

    skills_required: Optional[List[str]] = Field(
        default_factory=list, sa_type=ARRAY(String())
    )

    benefits: Optional[str] = Field(default=None, sa_type=Text)

    company_id: Optional[int] = Field(default=None, foreign_key="companies.id")
    created_by: int = Field(foreign_key="users.id")

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )


class Job(JobBase, table=True):
    __tablename__ = "jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    applications: List["JobApplication"] = Relationship(back_populates="job")


class JobCreate(JobBase):
    pass


class JobRead(JobBase):
    id: int
    applications_count: int = 0


class JobUpdate(SQLModel):
    name: Optional[str] = None
    job_number: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    is_remote: Optional[bool] = None
    status: Optional[JobStatus] = None
    priority: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    skills_required: Optional[List[str]] = None
    benefits: Optional[str] = None


# --- Job Application Models ---
class JobApplicationBase(SQLModel):
    job_id: int = Field(foreign_key="jobs.id")
    applicant_id: int = Field(foreign_key="users.id")

    cover_letter: str = Field(sa_type=Text)
    resume_url: str = Field(max_length=512)

    status: ApplicationStatus = Field(
        sa_column=Column(Enum(ApplicationStatus)),
        default=ApplicationStatus.APPLIED,
    )

    notes: Optional[str] = Field(default=None, sa_type=Text)

    application_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, name="metadata"),
    )

    applied_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )


class JobApplication(JobApplicationBase, table=True):
    __tablename__ = "job_applications"

    id: Optional[int] = Field(default=None, primary_key=True)

    job: "Job" = Relationship(back_populates="applications")
    applicant: "User" = Relationship(back_populates="job_applications")


class JobApplicationCreate(JobApplicationBase):
    pass


class JobApplicationRead(JobApplicationBase):
    id: int
    job: JobRead
    applicant: "UserRead"


class JobApplicationUpdate(SQLModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None
    application_metadata: Optional[Dict[str, Any]] = None


# --- Type Checking ---
if TYPE_CHECKING:
    from .user import User, UserRead

    Job.model_rebuild()
    JobApplication.model_rebuild()


# --- DB Indexes ---
@event.listens_for(Job.__table__, "after_create")
def create_job_indexes(target, connection, **kw):
    connection.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_job_status ON jobs (status);
        CREATE INDEX IF NOT EXISTS idx_job_company ON jobs (company_id);
        CREATE INDEX IF NOT EXISTS idx_job_type ON jobs (job_type);
        CREATE INDEX IF NOT EXISTS idx_job_experience ON jobs (experience_level);
        CREATE INDEX IF NOT EXISTS idx_job_remote ON jobs (is_remote);
        CREATE INDEX IF NOT EXISTS idx_job_skills ON jobs USING GIN (skills_required);
        CREATE INDEX IF NOT EXISTS idx_job_priority ON jobs (priority);
        CREATE INDEX IF NOT EXISTS idx_job_dates ON jobs (start_date, due_date);
        """)
    )


@event.listens_for(JobApplication.__table__, "after_create")
def create_application_indexes(target, connection, **kw):
    connection.execute(
        text("""
        CREATE INDEX IF NOT EXISTS idx_application_job ON job_applications (job_id);
        CREATE INDEX IF NOT EXISTS idx_application_applicant ON job_applications (applicant_id);
        CREATE INDEX IF NOT EXISTS idx_application_status ON job_applications (status);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_application_unique ON job_applications (job_id, applicant_id);
        """)
    )