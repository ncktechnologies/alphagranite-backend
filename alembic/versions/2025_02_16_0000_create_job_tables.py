"""create job tables

Revision ID: 2025_02_16_0000
Revises: 
Create Date: 2025-02-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision = '2025_02_16_0000'
down_revision = None
branch_labels = None
depends_on = None




def table_exists(table_name):
    """Check if a table exists in the database."""
    conn = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def enum_exists(enum_name):
    """Check if a PostgreSQL ENUM type exists."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :type_name)"),
        {"type_name": enum_name}
    )
    return result.scalar()


def create_enum_if_not_exists(enum_obj):
    """Create an ENUM type only if it doesn't exist."""
    if not enum_exists(enum_obj.name):
        enum_obj.create(op.get_bind(), checkfirst=False)
        print(f"Created ENUM type: {enum_obj.name}")
    else:
        print(f"Skipped ENUM (already exists): {enum_obj.name}")


def create_table_if_not_exists(table_name, *args, **kwargs):
    """Create a table only if it doesn't already exist."""
    if not table_exists(table_name):
        op.create_table(table_name, *args, **kwargs)
        print(f"Created table: {table_name}")
    else:
        print(f"Skipped table (already exists): {table_name}")


def index_exists(index_name):
    """Check if an index exists in the database."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = :index_name)"),
        {"index_name": index_name}
    )
    return result.scalar()


def create_index_if_not_exists(index_name, table_name, columns, **kwargs):
    """Create an index only if it doesn't exist."""
    if not index_exists(index_name):
        op.create_index(index_name, table_name, columns, **kwargs)
        print(f"Created index: {index_name}")
    else:
        print(f"Skipped index (already exists): {index_name}")

def upgrade():
    # Create enum types
    job_status = sa.Enum('draft', 'published', 'closed', 'archived', name='jobstatus')
    job_type = sa.Enum('full_time', 'part_time', 'contract', 'internship', 'temporary', name='jobtype')
    experience_level = sa.Enum('entry', 'mid', 'senior', 'executive', name='experiencelevel')
    application_status = sa.Enum(
        'applied', 'under_review', 'interview', 'offered', 'hired', 'rejected', 'withdrawn',
        name='applicationstatus'
    )
    
    # Create the enum types only if they don't exist
    create_enum_if_not_exists(job_status)
    create_enum_if_not_exists(job_type)
    create_enum_if_not_exists(experience_level)
    create_enum_if_not_exists(application_status)
    
    # Create jobs table
    create_table_if_not_exists(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=False),
        sa.Column('responsibilities', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('job_type', job_type, nullable=False, index=True),
        sa.Column('experience_level', experience_level, nullable=False, index=True),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('salary_currency', sa.String(length=3), server_default='USD', nullable=False),
        sa.Column('is_remote', sa.Boolean(), server_default='f', nullable=False, index=True),
        sa.Column('status', job_status, server_default='draft', nullable=False, index=True),
        sa.Column('application_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('skills_required', postgresql.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('benefits', sa.Text(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False, index=True),
        sa.Column('created_by', sa.Integer(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create job_applications table
    create_table_if_not_exists(
        'job_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False, index=True),
        sa.Column('applicant_id', sa.Integer(), nullable=False, index=True),
        sa.Column('cover_letter', sa.Text(), nullable=False),
        sa.Column('resume_url', sa.String(length=512), nullable=False),
        sa.Column('status', application_status, server_default='applied', nullable=False, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=func.now(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applicant_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'applicant_id', name='_job_applicant_uc')
    )
    
    # Create indexes (only if tables were created)
    if not table_exists('jobs'):
        create_index_if_not_exists('idx_job_status', 'jobs', ['status'])
        create_index_if_not_exists('idx_job_company', 'jobs', ['company_id'])
        create_index_if_not_exists('idx_job_type', 'jobs', ['job_type'])
        create_index_if_not_exists('idx_job_experience', 'jobs', ['experience_level'])
        create_index_if_not_exists('idx_job_remote', 'jobs', ['is_remote'])
        create_index_if_not_exists('idx_job_skills', 'jobs', ['skills_required'], postgresql_using='gin')
    
    if not table_exists('job_applications'):
        create_index_if_not_exists('idx_application_job', 'job_applications', ['job_id'])
        create_index_if_not_exists('idx_application_applicant', 'job_applications', ['applicant_id'])
        create_index_if_not_exists('idx_application_status', 'job_applications', ['status'])


def downgrade():
    # Drop tables first (in reverse order of creation due to foreign key constraints)
    op.drop_table('job_applications')
    op.drop_table('jobs')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS applicationstatus")
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS jobtype")
    op.execute("DROP TYPE IF EXISTS experiencelevel")
