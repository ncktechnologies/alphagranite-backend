"""create cnc drafting tables

Revision ID: 2026033101
Revises: 2025010901
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = "2026033101"
down_revision = "2025010901"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cnc_draftings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drafter_id", sa.Integer(), nullable=False),
        sa.Column("fab_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_start_date", sa.DateTime(), nullable=False),
        sa.Column("scheduled_end_date", sa.DateTime(), nullable=False),
        sa.Column("drafter_start_date", sa.DateTime(), nullable=True),
        sa.Column("drafter_end_date", sa.DateTime(), nullable=True),
        sa.Column("status_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_sqft", sa.Float(), nullable=True),
        sa.Column("no_of_pieces", sa.Integer(), nullable=True),
        sa.Column("cad_review_complete", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("draft_completed", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("current_stage", sa.String(), nullable=True),
        sa.Column("total_sqft_required_to_draft", sa.String(), nullable=False),
        sa.Column("total_sqft_drafted", sa.Float(), nullable=True),
        sa.Column("no_of_piece_drafted", sa.Integer(), nullable=True),
        sa.Column("draft_note", sa.String(), nullable=True),
        sa.Column("mentions", sa.String(), nullable=True),
        sa.Column("total_hours_drafted", sa.Float(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("file_ids", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["fab_id"], ["fabs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fab_id"),
    )
    op.create_index(op.f("ix_cnc_draftings_id"), "cnc_draftings", ["id"], unique=False)

    op.create_table(
        "cnc_drafting_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fab_id", sa.Integer(), nullable=False),
        sa.Column("drafter_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="drafting"),
        sa.Column("session_start_time", sa.DateTime(), nullable=False),
        sa.Column("session_end_time", sa.DateTime(), nullable=True),
        sa.Column("current_pause_start_time", sa.DateTime(), nullable=True),
        sa.Column("total_pause_duration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_time_spent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cumulative_sqft_drafted", sa.String(), nullable=True, server_default="0"),
        sa.Column("work_percentage_done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cnc_drafting_sessions_fab_id"), "cnc_drafting_sessions", ["fab_id"], unique=False)
    op.create_index(op.f("ix_cnc_drafting_sessions_id"), "cnc_drafting_sessions", ["id"], unique=False)

    op.create_table(
        "cnc_drafting_session_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("fab_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("sqft_drafted", sa.String(), nullable=True),
        sa.Column("work_percentage_done", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cnc_drafting_session_notes_session_id"), "cnc_drafting_session_notes", ["session_id"], unique=False)
    op.create_index(op.f("ix_cnc_drafting_session_notes_fab_id"), "cnc_drafting_session_notes", ["fab_id"], unique=False)
    op.create_index(op.f("ix_cnc_drafting_session_notes_id"), "cnc_drafting_session_notes", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_cnc_drafting_session_notes_id"), table_name="cnc_drafting_session_notes")
    op.drop_index(op.f("ix_cnc_drafting_session_notes_fab_id"), table_name="cnc_drafting_session_notes")
    op.drop_index(op.f("ix_cnc_drafting_session_notes_session_id"), table_name="cnc_drafting_session_notes")
    op.drop_table("cnc_drafting_session_notes")

    op.drop_index(op.f("ix_cnc_drafting_sessions_id"), table_name="cnc_drafting_sessions")
    op.drop_index(op.f("ix_cnc_drafting_sessions_fab_id"), table_name="cnc_drafting_sessions")
    op.drop_table("cnc_drafting_sessions")

    op.drop_index(op.f("ix_cnc_draftings_id"), table_name="cnc_draftings")
    op.drop_table("cnc_draftings")
