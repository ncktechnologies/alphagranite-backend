"""create shop revisions table

Revision ID: 20260602_120000
Revises: 20260522_130000
Create Date: 2026-06-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260602_120000"
down_revision: Union[str, Sequence[str], None] = "20260522_130000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shop_revisions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("fab_id", sa.Integer(), sa.ForeignKey("fabs.id"), nullable=False),
        sa.Column("revision_note", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revision_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_shop_revisions_fab_id", "shop_revisions", ["fab_id"])
    op.create_index("ix_shop_revisions_revision_completed", "shop_revisions", ["revision_completed"])
    op.create_index("ix_shop_revisions_created_at", "shop_revisions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_shop_revisions_created_at", table_name="shop_revisions")
    op.drop_index("ix_shop_revisions_revision_completed", table_name="shop_revisions")
    op.drop_index("ix_shop_revisions_fab_id", table_name="shop_revisions")
    op.drop_table("shop_revisions")