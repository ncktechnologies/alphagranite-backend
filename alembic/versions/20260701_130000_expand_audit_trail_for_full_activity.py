"""expand audit_trails for full activity coverage

Revision ID: 20260701_130000
Revises: 20260626_120000
Create Date: 2026-07-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260701_130000"
down_revision: Union[str, Sequence[str], None] = "20260626_120000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("audit_trails", sa.Column("operation", sa.String(length=50), nullable=True))
    op.add_column("audit_trails", sa.Column("resource_type", sa.String(length=100), nullable=True))
    op.add_column("audit_trails", sa.Column("changed_fields", sa.JSON(), nullable=True))
    op.add_column("audit_trails", sa.Column("old_values", sa.JSON(), nullable=True))
    op.add_column("audit_trails", sa.Column("new_values", sa.JSON(), nullable=True))
    op.add_column("audit_trails", sa.Column("request_path", sa.String(length=500), nullable=True))
    op.add_column("audit_trails", sa.Column("request_method", sa.String(length=10), nullable=True))
    op.add_column("audit_trails", sa.Column("response_status_code", sa.Integer(), nullable=True))

    op.create_index("ix_audit_trails_user_created", "audit_trails", ["user_id", "created_at"], unique=False)
    op.create_index("ix_audit_trails_resource_record_created", "audit_trails", ["resource_type", "record_id", "created_at"], unique=False)
    op.create_index("ix_audit_trails_operation_created", "audit_trails", ["operation", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_trails_operation_created", table_name="audit_trails")
    op.drop_index("ix_audit_trails_resource_record_created", table_name="audit_trails")
    op.drop_index("ix_audit_trails_user_created", table_name="audit_trails")

    op.drop_column("audit_trails", "response_status_code")
    op.drop_column("audit_trails", "request_method")
    op.drop_column("audit_trails", "request_path")
    op.drop_column("audit_trails", "new_values")
    op.drop_column("audit_trails", "old_values")
    op.drop_column("audit_trails", "changed_fields")
    op.drop_column("audit_trails", "resource_type")
    op.drop_column("audit_trails", "operation")
