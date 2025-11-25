"""add new workflow stages

Revision ID: a5d50d07adc9
Revises: add_is_completed_stages
Create Date: 2025-11-25 12:42:39.183695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5d50d07adc9'
down_revision: Union[str, Sequence[str], None] = 'add_is_completed_stages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create WJ Programming table
    op.create_table(
        'wj_programmings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('drafter_id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_start_date', sa.DateTime(), nullable=False),
        sa.Column('scheduled_end_date', sa.DateTime(), nullable=False),
        sa.Column('drafter_start_date', sa.DateTime(), nullable=True),
        sa.Column('drafter_end_date', sa.DateTime(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('file_ids', sa.String(), nullable=True),
        sa.Column('no_of_pieces', sa.String(), nullable=True),
        sa.Column('total_ln_ft', sa.String(), nullable=True),
        sa.Column('notes', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create WJ Scheduling table
    op.create_table(
        'wj_schedulings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('technician_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_start_date', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end_date', sa.DateTime(), nullable=True),
        sa.Column('actual_start_date', sa.DateTime(), nullable=True),
        sa.Column('actual_end_date', sa.DateTime(), nullable=True),
        sa.Column('total_ln_ft', sa.String(), nullable=True),
        sa.Column('completed_ln_ft', sa.String(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Resurface Scheduling table
    op.create_table(
        'resurface_schedulings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('technician_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_start_date', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end_date', sa.DateTime(), nullable=True),
        sa.Column('actual_start_date', sa.DateTime(), nullable=True),
        sa.Column('actual_end_date', sa.DateTime(), nullable=True),
        sa.Column('total_sqft', sa.String(), nullable=True),
        sa.Column('completed_sqft', sa.String(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Revisions table
    op.create_table(
        'revisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('revision_type', sa.String(), nullable=False),
        sa.Column('requested_by', sa.Integer(), nullable=False),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('scheduled_start_date', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end_date', sa.DateTime(), nullable=True),
        sa.Column('actual_start_date', sa.DateTime(), nullable=True),
        sa.Column('actual_end_date', sa.DateTime(), nullable=True),
        sa.Column('revision_notes', sa.String(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('file_ids', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Cost of Stone table
    op.create_table(
        'cost_of_stones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('stone_color_id', sa.Integer(), nullable=True),
        sa.Column('stone_type_id', sa.Integer(), nullable=True),
        sa.Column('total_sqft', sa.String(), nullable=True),
        sa.Column('cost_per_sqft', sa.String(), nullable=True),
        sa.Column('total_cost', sa.String(), nullable=True),
        sa.Column('waste_percentage', sa.String(), nullable=True),
        sa.Column('calculated_by', sa.Integer(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Install Scheduling table
    op.create_table(
        'install_schedulings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('installer_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_install_date', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end_date', sa.DateTime(), nullable=True),
        sa.Column('actual_install_date', sa.DateTime(), nullable=True),
        sa.Column('total_sqft', sa.String(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create Install Completion table
    op.create_table(
        'install_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('installer_id', sa.Integer(), nullable=False),
        sa.Column('install_date', sa.DateTime(), nullable=False),
        sa.Column('completion_date', sa.DateTime(), nullable=False),
        sa.Column('total_sqft_installed', sa.String(), nullable=True),
        sa.Column('customer_signature', sa.String(), nullable=True),
        sa.Column('completion_notes', sa.String(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('file_ids', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('install_completions')
    op.drop_table('install_schedulings')
    op.drop_table('cost_of_stones')
    op.drop_table('revisions')
    op.drop_table('resurface_schedulings')
    op.drop_table('wj_schedulings')
    op.drop_table('wj_programmings')
