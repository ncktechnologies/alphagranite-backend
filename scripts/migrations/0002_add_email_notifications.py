"""
Add email_notifications_enabled column to users table
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_email_notifications'
down_revision = None  # Replace with your actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('email_notifications_enabled', sa.Boolean(), server_default='true', nullable=False))


def downgrade():
    op.drop_column('users', 'email_notifications_enabled')