"""Create service_level_settings table with seed data from SLA spec

Revision ID: 20260622_120000
Revises: 20260618_120000
Create Date: 2026-06-22
"""

from typing import Sequence, Union
from datetime import datetime

import sqlalchemy as sa
from alembic import op


revision: str = "20260622_120000"
down_revision: Union[str, Sequence[str], None] = "20260618_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Stages tracked in service-level report
STAGES = [
    "Pre-Draft Review",
    "Drafting",
    "SlabSmith",
    "SCT",
    "Revisions",
    "Final Programming",
    "CNC",
]

# Seed data from SLA spec spreadsheet.
# Format: (fab_type, stage_name, target_days, at_risk_days, is_applicable)
# target_days = green threshold; at_risk_days = yellow window (0 → immediate red on overage)
SEED_ROWS = [
    # AG REDO (total SLA: 5.5 days)
    ("AG REDO", "Pre-Draft Review",  0.5, 0.0, True),
    ("AG REDO", "Drafting",          1.0, 1.0, True),
    ("AG REDO", "SlabSmith",         1.0, 1.0, True),
    ("AG REDO", "SCT",               1.0, 1.0, True),
    ("AG REDO", "Revisions",         0.0, 0.0, True),
    ("AG REDO", "Final Programming", 1.0, 0.0, True),
    ("AG REDO", "CNC",               1.0, 0.0, True),

    # BASIC (total SLA: 5 days)
    ("BASIC", "Pre-Draft Review",  1.0, 0.0, True),
    ("BASIC", "Drafting",          1.0, 1.0, True),
    ("BASIC", "SlabSmith",         0.0, 0.0, False),  # not applicable for BASIC
    ("BASIC", "SCT",               1.0, 1.0, True),
    ("BASIC", "Revisions",         0.0, 0.0, True),
    ("BASIC", "Final Programming", 1.0, 0.0, True),
    ("BASIC", "CNC",               1.0, 0.0, True),

    # CUST REDO (total SLA: 12 days)
    ("CUST REDO", "Pre-Draft Review",  1.0, 1.0, True),
    ("CUST REDO", "Drafting",          4.0, 1.0, True),
    ("CUST REDO", "SlabSmith",         1.0, 1.0, True),
    ("CUST REDO", "SCT",               2.0, 1.0, True),
    ("CUST REDO", "Revisions",         2.0, 1.0, True),
    ("CUST REDO", "Final Programming", 1.0, 0.0, True),
    ("CUST REDO", "CNC",               1.0, 0.0, True),

    # FAB ONLY (total SLA: 10 days)
    ("FAB ONLY", "Pre-Draft Review",  1.0, 0.0, True),
    ("FAB ONLY", "Drafting",          2.0, 1.0, True),
    ("FAB ONLY", "SlabSmith",         1.0, 1.0, True),
    ("FAB ONLY", "SCT",               2.0, 1.0, True),
    ("FAB ONLY", "Revisions",         2.0, 1.0, True),
    ("FAB ONLY", "Final Programming", 1.0, 0.0, True),
    ("FAB ONLY", "CNC",               1.0, 0.0, True),

    # FAST TRACK (total SLA: 5.5 days)
    ("FAST TRACK", "Pre-Draft Review",  0.5, 0.0, True),
    ("FAST TRACK", "Drafting",          1.0, 1.0, True),
    ("FAST TRACK", "SlabSmith",         1.0, 1.0, True),
    ("FAST TRACK", "SCT",               1.0, 1.0, True),
    ("FAST TRACK", "Revisions",         0.0, 0.0, True),
    ("FAST TRACK", "Final Programming", 1.0, 0.0, True),
    ("FAST TRACK", "CNC",               1.0, 0.0, True),

    # STANDARD (total SLA: 12 days)
    ("STANDARD", "Pre-Draft Review",  1.0, 1.0, True),
    ("STANDARD", "Drafting",          4.0, 1.0, True),
    ("STANDARD", "SlabSmith",         1.0, 1.0, True),
    ("STANDARD", "SCT",               2.0, 1.0, True),
    ("STANDARD", "Revisions",         2.0, 1.0, True),
    ("STANDARD", "Final Programming", 1.0, 0.0, True),
    ("STANDARD", "CNC",               1.0, 0.0, True),

    # Fab types with no applicable SLA - one placeholder row each
    ("PUNCHOUT AG",       "Pre-Draft Review", 0.0, 0.0, False),
    ("PUNCHOUT BILLABLE", "Pre-Draft Review", 0.0, 0.0, False),
    ("RESURFACE",         "Pre-Draft Review", 0.0, 0.0, False),

    # DEFAULT – fallback for fab types not explicitly listed
    ("DEFAULT", "Pre-Draft Review",  1.0, 1.0, True),
    ("DEFAULT", "Drafting",          3.0, 1.0, True),
    ("DEFAULT", "SlabSmith",         2.0, 1.0, True),
    ("DEFAULT", "SCT",               3.0, 1.0, True),
    ("DEFAULT", "Revisions",         2.0, 1.0, True),
    ("DEFAULT", "Final Programming", 2.0, 0.0, True),
    ("DEFAULT", "CNC",               1.0, 0.0, True),
]


def table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists("service_level_settings"):
        op.create_table(
            "service_level_settings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("fab_type", sa.String(length=100), nullable=False),
            sa.Column("stage_name", sa.String(length=100), nullable=False),
            sa.Column("target_days", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("at_risk_days", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("is_applicable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_service_level_settings_fab_type", "service_level_settings", ["fab_type"])
        op.create_index("ix_service_level_settings_stage_name", "service_level_settings", ["stage_name"])

    # Seed default data if the table is empty.
    conn = op.get_bind()
    existing = conn.execute(sa.text("SELECT COUNT(*) FROM service_level_settings")).scalar()
    if not existing:
        now = datetime.now()
        conn.execute(
            sa.text(
                "INSERT INTO service_level_settings "
                "(fab_type, stage_name, target_days, at_risk_days, is_applicable, created_at) "
                "VALUES (:fab_type, :stage_name, :target_days, :at_risk_days, :is_applicable, :created_at)"
            ),
            [
                {
                    "fab_type": fab_type,
                    "stage_name": stage_name,
                    "target_days": target_days,
                    "at_risk_days": at_risk_days,
                    "is_applicable": is_applicable,
                    "created_at": now,
                }
                for fab_type, stage_name, target_days, at_risk_days, is_applicable in SEED_ROWS
            ],
        )


def downgrade() -> None:
    if table_exists("service_level_settings"):
        op.drop_index("ix_service_level_settings_stage_name", table_name="service_level_settings")
        op.drop_index("ix_service_level_settings_fab_type", table_name="service_level_settings")
        op.drop_table("service_level_settings")
