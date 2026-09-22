"""create business jobs table

Revision ID: 2026092001
Revises: 2025010901
Create Date: 2026-09-20
"""

from alembic import op
import sqlalchemy as sa


revision = "2026092001"
down_revision = "2025010901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("job_number", sa.String(length=100), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(length=50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("project_value", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("status_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("sq_ft", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("need_to_invoice", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("invoice_note", sa.String(), nullable=True),
        sa.Column("invoiced_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["status_id"], ["status.value_id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_number"),
    )
    op.create_index("ix_business_jobs_name", "business_jobs", ["name"])
    op.create_index("ix_business_jobs_job_number", "business_jobs", ["job_number"])


def downgrade() -> None:
    op.drop_index("ix_business_jobs_job_number", table_name="business_jobs")
    op.drop_index("ix_business_jobs_name", table_name="business_jobs")
    op.drop_table("business_jobs")