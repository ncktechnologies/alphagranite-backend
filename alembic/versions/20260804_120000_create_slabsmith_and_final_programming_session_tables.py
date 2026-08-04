"""create slabsmith and final programming session tables

Revision ID: 20260804_120000
Revises: notes_to_json_array, 2026042301, add_templating_fields, 20260401_120000, 2025_02_16_0000, add_fab_tracking_fields, 561270688422
Create Date: 2026-08-04 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260804_120000"
down_revision = (
    "notes_to_json_array",
    "2026042301",
    "add_templating_fields",
    "20260401_120000",
    "2025_02_16_0000",
    "add_fab_tracking_fields",
    "561270688422",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "slab_smith_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fab_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("session_start_time", sa.DateTime(), nullable=False),
        sa.Column("session_end_time", sa.DateTime(), nullable=True),
        sa.Column("current_pause_start_time", sa.DateTime(), nullable=True),
        sa.Column("total_pause_duration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_time_spent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_slab_smith_sessions_fab_id"), "slab_smith_sessions", ["fab_id"], unique=False)

    op.create_table(
        "slab_smith_session_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("fab_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_slab_smith_session_notes_session_id"), "slab_smith_session_notes", ["session_id"], unique=False)
    op.create_index(op.f("ix_slab_smith_session_notes_fab_id"), "slab_smith_session_notes", ["fab_id"], unique=False)

    op.create_table(
        "final_programming_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fab_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("session_start_time", sa.DateTime(), nullable=False),
        sa.Column("session_end_time", sa.DateTime(), nullable=True),
        sa.Column("current_pause_start_time", sa.DateTime(), nullable=True),
        sa.Column("total_pause_duration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_time_spent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_final_programming_sessions_fab_id"), "final_programming_sessions", ["fab_id"], unique=False)

    op.create_table(
        "final_programming_session_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("fab_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_final_programming_session_notes_session_id"), "final_programming_session_notes", ["session_id"], unique=False)
    op.create_index(op.f("ix_final_programming_session_notes_fab_id"), "final_programming_session_notes", ["fab_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_final_programming_session_notes_fab_id"), table_name="final_programming_session_notes")
    op.drop_index(op.f("ix_final_programming_session_notes_session_id"), table_name="final_programming_session_notes")
    op.drop_table("final_programming_session_notes")

    op.drop_index(op.f("ix_final_programming_sessions_fab_id"), table_name="final_programming_sessions")
    op.drop_table("final_programming_sessions")

    op.drop_index(op.f("ix_slab_smith_session_notes_fab_id"), table_name="slab_smith_session_notes")
    op.drop_index(op.f("ix_slab_smith_session_notes_session_id"), table_name="slab_smith_session_notes")
    op.drop_table("slab_smith_session_notes")

    op.drop_index(op.f("ix_slab_smith_sessions_fab_id"), table_name="slab_smith_sessions")
    op.drop_table("slab_smith_sessions")
