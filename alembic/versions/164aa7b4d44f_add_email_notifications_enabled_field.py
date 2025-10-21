"""Add email_notifications_enabled field

Revision ID: 164aa7b4d44f
Revises: feec8e77ba36
Create Date: 2025-10-21 03:31:06.210223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '164aa7b4d44f'
down_revision: Union[str, Sequence[str], None] = 'feec8e77ba36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add email_notifications_enabled column to users table."""
    # Only add the email_notifications_enabled column
    op.add_column('users', sa.Column('email_notifications_enabled', sa.Boolean(), server_default='true', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema - Remove email_notifications_enabled column."""
    # Only drop the email_notifications_enabled column
    op.drop_column('users', 'email_notifications_enabled')
    # ### end Alembic commands ###
