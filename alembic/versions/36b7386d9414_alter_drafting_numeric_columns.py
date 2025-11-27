"""alter_drafting_numeric_columns

Revision ID: 36b7386d9414
Revises: add_fab_tracking_fields
Create Date: 2025-11-27 09:31:39.552713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36b7386d9414'
down_revision: Union[str, Sequence[str], None] = 'add_fab_tracking_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alter total_sqft_drafted from VARCHAR to NUMERIC (FLOAT)
    op.execute("""
        ALTER TABLE draftings 
        ALTER COLUMN total_sqft_drafted TYPE NUMERIC USING total_sqft_drafted::NUMERIC
    """)
    
    # Alter no_of_piece_drafted from VARCHAR to INTEGER
    op.execute("""
        ALTER TABLE draftings 
        ALTER COLUMN no_of_piece_drafted TYPE INTEGER USING no_of_piece_drafted::INTEGER
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert total_sqft_drafted back to VARCHAR
    op.execute("""
        ALTER TABLE draftings 
        ALTER COLUMN total_sqft_drafted TYPE VARCHAR USING total_sqft_drafted::VARCHAR
    """)
    
    # Revert no_of_piece_drafted back to VARCHAR
    op.execute("""
        ALTER TABLE draftings 
        ALTER COLUMN no_of_piece_drafted TYPE VARCHAR USING no_of_piece_drafted::VARCHAR
    """)
