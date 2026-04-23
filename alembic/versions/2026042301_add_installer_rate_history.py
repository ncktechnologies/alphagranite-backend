"""add installer rate history table

Revision ID: 2026042301
Revises: 2026033101
Create Date: 2026-04-23
"""

from alembic import op
import sqlalchemy as sa


revision = "2026042301"
down_revision = "2026033101"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists("installer_rate_history"):
        op.create_table(
            "installer_rate_history",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("installer_id", sa.Integer(), nullable=False),
            sa.Column("hourly_rate", sa.Float(), nullable=False),
            sa.Column("effective_from", sa.DateTime(), nullable=False),
            sa.Column("effective_to", sa.DateTime(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["installer_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_installer_rate_history_installer_id", "installer_rate_history", ["installer_id"])
        op.create_index("ix_installer_rate_history_effective_from", "installer_rate_history", ["effective_from"])
        op.create_index("ix_installer_rate_history_effective_to", "installer_rate_history", ["effective_to"])
        op.create_index("ix_installer_rate_history_is_active", "installer_rate_history", ["is_active"])


def downgrade() -> None:
    if table_exists("installer_rate_history"):
        op.drop_index("ix_installer_rate_history_is_active", table_name="installer_rate_history")
        op.drop_index("ix_installer_rate_history_effective_to", table_name="installer_rate_history")
        op.drop_index("ix_installer_rate_history_effective_from", table_name="installer_rate_history")
        op.drop_index("ix_installer_rate_history_installer_id", table_name="installer_rate_history")
        op.drop_table("installer_rate_history")
