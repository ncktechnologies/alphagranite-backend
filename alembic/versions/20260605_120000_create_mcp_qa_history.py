"""create mcp_qa_history table

Revision ID: 20260605_120000
Revises: 20260602_120000
Create Date: 2026-06-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260605_120000"
down_revision: Union[str, Sequence[str], None] = "20260602_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mcp_qa_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("normalized_question", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False, server_default="report"),
        sa.Column("matched_tool", sa.String(length=128), nullable=True),
        sa.Column("answer_summary", sa.Text(), nullable=True),
        sa.Column("answer_json", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("feedback", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_mcp_qa_history_user_id", "mcp_qa_history", ["user_id"])
    op.create_index("ix_mcp_qa_history_mode", "mcp_qa_history", ["mode"])
    op.create_index("ix_mcp_qa_history_matched_tool", "mcp_qa_history", ["matched_tool"])
    op.create_index("ix_mcp_qa_history_feedback", "mcp_qa_history", ["feedback"])
    op.create_index("ix_mcp_qa_history_created_at", "mcp_qa_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_mcp_qa_history_created_at", table_name="mcp_qa_history")
    op.drop_index("ix_mcp_qa_history_feedback", table_name="mcp_qa_history")
    op.drop_index("ix_mcp_qa_history_matched_tool", table_name="mcp_qa_history")
    op.drop_index("ix_mcp_qa_history_mode", table_name="mcp_qa_history")
    op.drop_index("ix_mcp_qa_history_user_id", table_name="mcp_qa_history")
    op.drop_table("mcp_qa_history")
