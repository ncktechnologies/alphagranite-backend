"""create hcp staff roster tables and report kind

Revision ID: 20260922_120000
Revises: 20260904_120000
Create Date: 2026-09-22 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_120000"
down_revision: Union[str, Sequence[str], None] = "20260904_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # One set of credentials per company; a fixed settings_id per saved report.
    op.add_column(
        "hcp_payroll_source_configs",
        sa.Column("payroll_settings_id", sa.String(length=100), nullable=False, server_default="89798180"),
    )
    op.add_column(
        "hcp_payroll_source_configs",
        sa.Column("roster_settings_id", sa.String(length=100), nullable=False, server_default="93428419"),
    )
    op.execute(
        "UPDATE hcp_payroll_source_configs "
        "SET payroll_settings_id = report_settings_id "
        "WHERE report_settings_id IS NOT NULL AND report_settings_id <> ''"
    )
    op.create_index(
        op.f("ix_hcp_payroll_source_configs_payroll_settings_id"),
        "hcp_payroll_source_configs",
        ["payroll_settings_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hcp_payroll_source_configs_roster_settings_id"),
        "hcp_payroll_source_configs",
        ["roster_settings_id"],
        unique=False,
    )
    op.drop_index(op.f("ix_hcp_payroll_source_configs_report_settings_id"), table_name="hcp_payroll_source_configs")
    op.drop_column("hcp_payroll_source_configs", "report_settings_id")

    op.create_table(
        "hcp_staff_roster_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_config_id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("report_settings_id", sa.String(length=100), nullable=False),
        sa.Column("payload_format", sa.String(length=50), nullable=False, server_default="csv"),
        sa.Column("raw_payload_text", sa.Text(), nullable=False),
        sa.Column("pulled_at", sa.DateTime(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_employee_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_config_id"], ["hcp_payroll_source_configs.id"]),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["hcp_payroll_ingestion_runs.id"]),
    )
    op.create_index(op.f("ix_hcp_staff_roster_snapshots_source_config_id"), "hcp_staff_roster_snapshots", ["source_config_id"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_snapshots_ingestion_run_id"), "hcp_staff_roster_snapshots", ["ingestion_run_id"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_snapshots_report_settings_id"), "hcp_staff_roster_snapshots", ["report_settings_id"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_snapshots_pulled_at"), "hcp_staff_roster_snapshots", ["pulled_at"], unique=False)

    op.create_table(
        "hcp_staff_roster_rows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("source_config_id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.String(length=100), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("employee_status", sa.String(length=100), nullable=True),
        sa.Column("employee_type", sa.String(length=100), nullable=True),
        sa.Column("in_payroll", sa.String(length=50), nullable=True),
        sa.Column("locked", sa.String(length=50), nullable=True),
        sa.Column("date_terminated", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("raw_line_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["hcp_staff_roster_snapshots.id"]),
        sa.ForeignKeyConstraint(["source_config_id"], ["hcp_payroll_source_configs.id"]),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["hcp_payroll_ingestion_runs.id"]),
    )
    op.create_index(op.f("ix_hcp_staff_roster_rows_snapshot_id"), "hcp_staff_roster_rows", ["snapshot_id"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_rows_source_config_id"), "hcp_staff_roster_rows", ["source_config_id"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_rows_ingestion_run_id"), "hcp_staff_roster_rows", ["ingestion_run_id"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_rows_row_index"), "hcp_staff_roster_rows", ["row_index"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_rows_employee_id"), "hcp_staff_roster_rows", ["employee_id"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_rows_username"), "hcp_staff_roster_rows", ["username"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_rows_employee_status"), "hcp_staff_roster_rows", ["employee_status"], unique=False)
    op.create_index(op.f("ix_hcp_staff_roster_rows_is_active"), "hcp_staff_roster_rows", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_table("hcp_staff_roster_rows")
    op.drop_table("hcp_staff_roster_snapshots")
    op.add_column(
        "hcp_payroll_source_configs",
        sa.Column("report_settings_id", sa.String(length=100), nullable=False, server_default="89798180"),
    )
    op.execute("UPDATE hcp_payroll_source_configs SET report_settings_id = payroll_settings_id")
    op.create_index(
        op.f("ix_hcp_payroll_source_configs_report_settings_id"),
        "hcp_payroll_source_configs",
        ["report_settings_id"],
        unique=False,
    )
    op.drop_index(op.f("ix_hcp_payroll_source_configs_roster_settings_id"), table_name="hcp_payroll_source_configs")
    op.drop_index(op.f("ix_hcp_payroll_source_configs_payroll_settings_id"), table_name="hcp_payroll_source_configs")
    op.drop_column("hcp_payroll_source_configs", "roster_settings_id")
    op.drop_column("hcp_payroll_source_configs", "payroll_settings_id")
