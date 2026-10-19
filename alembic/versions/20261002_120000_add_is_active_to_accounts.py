"""add is_active to accounts

Inactive accounts are hidden from account selection (GET /accounts) but still
listed on the accounts management screen (GET /accounts/all).

Revision ID: 20261002_120000
Revises: 20260930_120000
Create Date: 2026-10-02

"""
from alembic import op
import sqlalchemy as sa


revision = "20261002_120000"
down_revision = "20260930_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_accounts_is_active", "accounts", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_accounts_is_active", table_name="accounts")
    op.drop_column("accounts", "is_active")
