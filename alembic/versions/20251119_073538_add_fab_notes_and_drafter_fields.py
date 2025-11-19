"""add_fab_notes_and_drafter_fields

Revision ID: 20251119_073538
Revises: 305e16b8ae3d
Create Date: 2025-11-19 14:35:38

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251119_073538'
down_revision: Union[str, Sequence[str], None] = '305e16b8ae3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add fab_notes table and drafter fields to fabs table."""
    
    # Create fab_notes table
    op.create_table(
        'fab_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('stage', sa.String(length=255), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['fab_id'], ['fabs.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for fab_notes
    op.create_index('ix_fab_notes_fab_id', 'fab_notes', ['fab_id'], unique=False)
    op.create_index('ix_fab_notes_stage', 'fab_notes', ['stage'], unique=False)
    
    # Add drafter fields to fabs table
    op.add_column('fabs', sa.Column('drafter_id', sa.Integer(), nullable=True))
    op.add_column('fabs', sa.Column('drafter_assigned_by', sa.Integer(), nullable=True))
    op.add_column('fabs', sa.Column('drafter_assigned_at', sa.DateTime(), nullable=True))
    
    # Create foreign key constraints for drafter fields
    op.create_foreign_key('fk_fabs_drafter_id', 'fabs', 'users', ['drafter_id'], ['id'])
    op.create_foreign_key('fk_fabs_drafter_assigned_by', 'fabs', 'users', ['drafter_assigned_by'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop foreign key constraints for drafter fields
    op.drop_constraint('fk_fabs_drafter_assigned_by', 'fabs', type_='foreignkey')
    op.drop_constraint('fk_fabs_drafter_id', 'fabs', type_='foreignkey')
    
    # Drop drafter fields from fabs table
    op.drop_column('fabs', 'drafter_assigned_at')
    op.drop_column('fabs', 'drafter_assigned_by')
    op.drop_column('fabs', 'drafter_id')
    
    # Drop indexes for fab_notes
    op.drop_index('ix_fab_notes_stage', table_name='fab_notes')
    op.drop_index('ix_fab_notes_fab_id', table_name='fab_notes')
    
    # Drop fab_notes table
    op.drop_table('fab_notes')
