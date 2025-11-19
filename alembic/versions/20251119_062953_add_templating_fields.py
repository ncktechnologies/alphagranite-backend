"""add actual_start_date and duration to templatings

Revision ID: add_templating_fields
Revises: a47d77f3fdc1
Create Date: 2025-11-19 06:29:53

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_templating_fields'
down_revision = 'a47d77f3fdc1'
branch_labels = None
depends_on = None


def upgrade():
    """Add actual_start_date and duration columns to templatings table"""
    
    # Add actual_start_date column
    op.add_column('templatings', sa.Column('actual_start_date', sa.DateTime(), nullable=True))
    
    # Add duration column (in hours)
    op.add_column('templatings', sa.Column('duration', sa.Integer(), nullable=True))


def downgrade():
    """Remove actual_start_date and duration columns from templatings table"""
    
    op.drop_column('templatings', 'duration')
    op.drop_column('templatings', 'actual_start_date')
