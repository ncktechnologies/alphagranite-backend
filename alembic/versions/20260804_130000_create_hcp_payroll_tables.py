"""create hcp payroll tables

Revision ID: 20260804_130000
Revises: 20260804_120000
Create Date: 2026-08-04 13:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260804_130000"
down_revision: Union[str, Sequence[str], None] = "20260804_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hcp_payroll_source_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=255), nullable=False, server_default="https://secure.saashr.com"),
        sa.Column("company_id", sa.String(length=100), nullable=False, server_default="83943830"),
        sa.Column("grant_type", sa.String(length=100), nullable=False, server_default="client_credentials"),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("client_secret", sa.String(length=255), nullable=True),
        sa.Column("report_settings_id", sa.String(length=100), nullable=False, server_default="89798180"),
        sa.Column("schedule_type", sa.String(length=50), nullable=False, server_default="weekly"),
        sa.Column("schedule_interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("schedule_weekday", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("schedule_hour", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("schedule_minute", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_hcp_payroll_source_configs_base_url"), "hcp_payroll_source_configs", ["base_url"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_source_configs_company_id"), "hcp_payroll_source_configs", ["company_id"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_source_configs_is_active"), "hcp_payroll_source_configs", ["is_active"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_source_configs_name"), "hcp_payroll_source_configs", ["name"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_source_configs_report_settings_id"), "hcp_payroll_source_configs", ["report_settings_id"], unique=False)

    op.create_table(
        "hcp_payroll_ingestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_config_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("token_request_url", sa.String(length=500), nullable=True),
        sa.Column("token_response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("token_acquired_at", sa.DateTime(), nullable=True),
        sa.Column("token_expires_in", sa.Integer(), nullable=True),
        sa.Column("report_request_url", sa.String(length=500), nullable=True),
        sa.Column("report_http_status", sa.Integer(), nullable=True),
        sa.Column("report_content_type", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.String(length=2000), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_config_id"], ["hcp_payroll_source_configs.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index(op.f("ix_hcp_payroll_ingestion_runs_source_config_id"), "hcp_payroll_ingestion_runs", ["source_config_id"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_ingestion_runs_status"), "hcp_payroll_ingestion_runs", ["status"], unique=False)

    op.create_table(
        "hcp_payroll_report_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_config_id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("report_settings_id", sa.String(length=100), nullable=False),
        sa.Column("report_title", sa.String(length=255), nullable=True),
        sa.Column("payload_format", sa.String(length=50), nullable=False),
        sa.Column("raw_payload_text", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_config_id"], ["hcp_payroll_source_configs.id"]),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["hcp_payroll_ingestion_runs.id"]),
    )
    op.create_index(op.f("ix_hcp_payroll_report_snapshots_source_config_id"), "hcp_payroll_report_snapshots", ["source_config_id"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_report_snapshots_ingestion_run_id"), "hcp_payroll_report_snapshots", ["ingestion_run_id"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_report_snapshots_report_settings_id"), "hcp_payroll_report_snapshots", ["report_settings_id"], unique=False)

    op.create_table(
        "hcp_payroll_report_rows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("source_config_id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("row_kind", sa.String(length=50), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("cost_center_name", sa.String(length=255), nullable=True),
        sa.Column("employee_first_name", sa.String(length=255), nullable=True),
        sa.Column("employee_last_name", sa.String(length=255), nullable=True),
        sa.Column("hourly_pay", sa.Float(), nullable=True),
        sa.Column("regular_hours", sa.Float(), nullable=True),
        sa.Column("holiday_hours", sa.Float(), nullable=True),
        sa.Column("pto_hours", sa.Float(), nullable=True),
        sa.Column("total_reg_pto_hol_wages", sa.Float(), nullable=True),
        sa.Column("overtime_hours", sa.Float(), nullable=True),
        sa.Column("total_ot_wages", sa.Float(), nullable=True),
        sa.Column("raw_line_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["hcp_payroll_report_snapshots.id"]),
        sa.ForeignKeyConstraint(["source_config_id"], ["hcp_payroll_source_configs.id"]),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["hcp_payroll_ingestion_runs.id"]),
    )
    op.create_index(op.f("ix_hcp_payroll_report_rows_snapshot_id"), "hcp_payroll_report_rows", ["snapshot_id"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_report_rows_source_config_id"), "hcp_payroll_report_rows", ["source_config_id"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_report_rows_ingestion_run_id"), "hcp_payroll_report_rows", ["ingestion_run_id"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_report_rows_row_kind"), "hcp_payroll_report_rows", ["row_kind"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_report_rows_row_index"), "hcp_payroll_report_rows", ["row_index"], unique=False)
    op.create_index(op.f("ix_hcp_payroll_report_rows_cost_center_name"), "hcp_payroll_report_rows", ["cost_center_name"], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO hcp_payroll_source_configs (
                name, base_url, company_id, grant_type, report_settings_id,
                schedule_type, schedule_interval, schedule_weekday, schedule_hour, schedule_minute,
                is_active, created_at, updated_at, created_by, updated_by
            )
            VALUES (
                'HCP Payroll Default',
                'https://secure.saashr.com',
                '83943830',
                'client_credentials',
                '89798180',
                'weekly',
                1,
                0,
                1,
                0,
                true,
                NOW(),
                NOW(),
                1,
                1
            )
            ON CONFLICT (name) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_hcp_payroll_report_rows_cost_center_name"), table_name="hcp_payroll_report_rows")
    op.drop_index(op.f("ix_hcp_payroll_report_rows_row_index"), table_name="hcp_payroll_report_rows")
    op.drop_index(op.f("ix_hcp_payroll_report_rows_row_kind"), table_name="hcp_payroll_report_rows")
    op.drop_index(op.f("ix_hcp_payroll_report_rows_ingestion_run_id"), table_name="hcp_payroll_report_rows")
    op.drop_index(op.f("ix_hcp_payroll_report_rows_source_config_id"), table_name="hcp_payroll_report_rows")
    op.drop_index(op.f("ix_hcp_payroll_report_rows_snapshot_id"), table_name="hcp_payroll_report_rows")
    op.drop_table("hcp_payroll_report_rows")

    op.drop_index(op.f("ix_hcp_payroll_report_snapshots_report_settings_id"), table_name="hcp_payroll_report_snapshots")
    op.drop_index(op.f("ix_hcp_payroll_report_snapshots_ingestion_run_id"), table_name="hcp_payroll_report_snapshots")
    op.drop_index(op.f("ix_hcp_payroll_report_snapshots_source_config_id"), table_name="hcp_payroll_report_snapshots")
    op.drop_table("hcp_payroll_report_snapshots")

    op.drop_index(op.f("ix_hcp_payroll_ingestion_runs_status"), table_name="hcp_payroll_ingestion_runs")
    op.drop_index(op.f("ix_hcp_payroll_ingestion_runs_source_config_id"), table_name="hcp_payroll_ingestion_runs")
    op.drop_table("hcp_payroll_ingestion_runs")

    op.drop_index(op.f("ix_hcp_payroll_source_configs_report_settings_id"), table_name="hcp_payroll_source_configs")
    op.drop_index(op.f("ix_hcp_payroll_source_configs_name"), table_name="hcp_payroll_source_configs")
    op.drop_index(op.f("ix_hcp_payroll_source_configs_is_active"), table_name="hcp_payroll_source_configs")
    op.drop_index(op.f("ix_hcp_payroll_source_configs_company_id"), table_name="hcp_payroll_source_configs")
    op.drop_index(op.f("ix_hcp_payroll_source_configs_base_url"), table_name="hcp_payroll_source_configs")
    op.drop_table("hcp_payroll_source_configs")