"""add is_completed to all stage tables

Revision ID: add_is_completed_stages
Revises: 20251119_081035
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_completed_stages'
down_revision = '20251119_081035'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_completed column to templatings table
    op.execute("""
        ALTER TABLE templatings 
        ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE
    """)
    
    # Add is_completed column to draftings table
    op.execute("""
        ALTER TABLE draftings 
        ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE
    """)
    
    # Add is_completed column to pre_draft_reviews table
    op.execute("""
        ALTER TABLE pre_draft_reviews 
        ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE
    """)
    
    # Add is_completed column to slab_smiths table
    op.execute("""
        ALTER TABLE slab_smiths 
        ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE
    """)
    
    # Add is_completed column to sales_cts table
    op.execute("""
        ALTER TABLE sales_cts 
        ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE
    """)
    
    # Add is_completed column to cut_list table
    op.execute("""
        ALTER TABLE cut_list 
        ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE
    """)
    
    # Add is_completed column to final_programmings table
    op.execute("""
        ALTER TABLE final_programmings 
        ADD COLUMN IF NOT EXISTS is_completed BOOLEAN NOT NULL DEFAULT FALSE
    """)


def downgrade() -> None:
    # Remove is_completed column from all tables
    op.execute("ALTER TABLE templatings DROP COLUMN IF EXISTS is_completed")
    op.execute("ALTER TABLE draftings DROP COLUMN IF EXISTS is_completed")
    op.execute("ALTER TABLE pre_draft_reviews DROP COLUMN IF EXISTS is_completed")
    op.execute("ALTER TABLE slab_smiths DROP COLUMN IF EXISTS is_completed")
    op.execute("ALTER TABLE sales_cts DROP COLUMN IF EXISTS is_completed")
    op.execute("ALTER TABLE cut_list DROP COLUMN IF EXISTS is_completed")
    op.execute("ALTER TABLE final_programmings DROP COLUMN IF EXISTS is_completed")
