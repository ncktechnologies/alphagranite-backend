"""create performance_static_data and subcontractor_weekly_labor

Revision ID: 20261006_120000
Revises: 20261002_120000
Create Date: 2026-10-06

"""
from alembic import op
import sqlalchemy as sa


revision = "20261006_120000"
down_revision = "20261002_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "performance_static_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("total_expenses", sa.Float(), nullable=True),
        sa.Column("total_wages", sa.Float(), nullable=True),
        sa.Column("breakeven_gross_revenue", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_performance_static_data_year", "performance_static_data", ["year"], unique=True)

    op.create_table(
        "subcontractor_weekly_labor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("week_ending", sa.Date(), nullable=False),
        sa.Column("total_labor_cost", sa.Float(), nullable=True),
        sa.Column("head_count", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_subcontractor_weekly_labor_year", "subcontractor_weekly_labor", ["year"])
    op.create_index(
        "ix_subcontractor_weekly_labor_week_ending", "subcontractor_weekly_labor", ["week_ending"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_subcontractor_weekly_labor_week_ending", table_name="subcontractor_weekly_labor")
    op.drop_index("ix_subcontractor_weekly_labor_year", table_name="subcontractor_weekly_labor")
    op.drop_table("subcontractor_weekly_labor")
    op.drop_index("ix_performance_static_data_year", table_name="performance_static_data")
    op.drop_table("performance_static_data")
