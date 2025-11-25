"""add fab tracking fields

Revision ID: add_fab_tracking_fields
Revises: a5d50d07adc9
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fab_tracking_fields'
down_revision = 'a5d50d07adc9'  # Latest revision from a5d50d07adc9_add_new_workflow_stages
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new tracking fields to fabs table
    # Templating tracking
    op.add_column('fabs', sa.Column('template_received', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('fabs', sa.Column('template_review_complete', sa.Boolean(), nullable=False, server_default='false'))
    
    # Drafting tracking
    op.add_column('fabs', sa.Column('draft_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('fabs', sa.Column('cad_review_complete', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('fabs', sa.Column('no_of_pieces', sa.Integer(), nullable=True))
    
    # Financial tracking
    op.add_column('fabs', sa.Column('revenue', sa.Float(), nullable=True))
    op.add_column('fabs', sa.Column('gp', sa.Float(), nullable=True))
    
    # SalesCT tracking
    op.add_column('fabs', sa.Column('sct_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('fabs', sa.Column('revised', sa.Boolean(), nullable=False, server_default='false'))
    
    # Cut List tracking
    op.add_column('fabs', sa.Column('shop_date_schedule', sa.DateTime(), nullable=True))
    op.add_column('fabs', sa.Column('final_programming_complete', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('fabs', sa.Column('slab_smith_used', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('fabs', sa.Column('fp_not_needed', sa.Boolean(), nullable=False, server_default='false'))
    
    # Final Programming tracking
    op.add_column('fabs', sa.Column('confirmed_date', sa.DateTime(), nullable=True))
    op.add_column('fabs', sa.Column('wj_time_minutes', sa.Integer(), nullable=True))
    op.add_column('fabs', sa.Column('wj_linft', sa.Float(), nullable=True))
    op.add_column('fabs', sa.Column('edging_linft', sa.Float(), nullable=True))
    op.add_column('fabs', sa.Column('cnc_linft', sa.Float(), nullable=True))
    op.add_column('fabs', sa.Column('miter_linft', sa.Float(), nullable=True))
    op.add_column('fabs', sa.Column('installation_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove the added columns in reverse order
    # Final Programming tracking
    op.drop_column('fabs', 'installation_date')
    op.drop_column('fabs', 'miter_linft')
    op.drop_column('fabs', 'cnc_linft')
    op.drop_column('fabs', 'edging_linft')
    op.drop_column('fabs', 'wj_linft')
    op.drop_column('fabs', 'wj_time_minutes')
    op.drop_column('fabs', 'confirmed_date')
    
    # Cut List tracking
    op.drop_column('fabs', 'fp_not_needed')
    op.drop_column('fabs', 'slab_smith_used')
    op.drop_column('fabs', 'final_programming_complete')
    op.drop_column('fabs', 'shop_date_schedule')
    
    # SalesCT tracking
    op.drop_column('fabs', 'revised')
    op.drop_column('fabs', 'sct_completed')
    
    # Financial tracking
    op.drop_column('fabs', 'gp')
    op.drop_column('fabs', 'revenue')
    
    # Drafting tracking
    op.drop_column('fabs', 'no_of_pieces')
    op.drop_column('fabs', 'cad_review_complete')
    op.drop_column('fabs', 'draft_completed')
    
    # Templating tracking
    op.drop_column('fabs', 'template_review_complete')
    op.drop_column('fabs', 'template_received')
