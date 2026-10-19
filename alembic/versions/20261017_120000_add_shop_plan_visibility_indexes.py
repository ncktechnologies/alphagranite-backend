"""add shop plan FAB lookup and incomplete-plan visibility indexes

Revision ID: 20261017_120000
Revises: 20261006_120000
"""
from alembic import op
import sqlalchemy as sa


revision = "20261017_120000"
down_revision = "20261006_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_shop_cut_plans_fab_id",
            "shop_cut_plans",
            ["fab_id"],
            postgresql_concurrently=True,
            if_not_exists=True,
        )
        op.create_index(
            "ix_shop_cut_plans_incomplete_fab_id",
            "shop_cut_plans",
            ["fab_id"],
            postgresql_where=sa.text("coalesce(work_percentage, 0) < 100"),
            postgresql_concurrently=True,
            if_not_exists=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_shop_cut_plans_incomplete_fab_id",
            table_name="shop_cut_plans",
            postgresql_concurrently=True,
            if_exists=True,
        )
        op.drop_index(
            "ix_shop_cut_plans_fab_id",
            table_name="shop_cut_plans",
            postgresql_concurrently=True,
            if_exists=True,
        )