"""restore installer_rate_history table

The original migration (2026042301) was removed in the migration cleanup
(293c855), and the no-op baseline does not create tables, so databases built
after the cleanup never got this table. The owner install-performance report
queries it and fails with UndefinedTableError.

Idempotent: creates the table/indexes only when missing, so it is safe on
databases that already have them.

Revision ID: 20261111_100000
Revises: 20261103_100000
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa


revision = "20261111_100000"
down_revision = "20261103_100000"
branch_labels = None
depends_on = None

TABLE = "installer_rate_history"
INDEXES = {
    "ix_installer_rate_history_installer_id": ["installer_id"],
    "ix_installer_rate_history_effective_from": ["effective_from"],
    "ix_installer_rate_history_effective_to": ["effective_to"],
    "ix_installer_rate_history_is_active": ["is_active"],
}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if TABLE not in inspector.get_table_names():
        op.create_table(
            TABLE,
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
        existing_indexes = set()
    else:
        existing_indexes = {ix["name"] for ix in inspector.get_indexes(TABLE)}

    for name, columns in INDEXES.items():
        if name not in existing_indexes:
            op.create_index(name, TABLE, columns)


def downgrade() -> None:
    # No-op: some databases had this table (with rate data) before this
    # migration existed, so dropping it here could destroy data.
    pass
