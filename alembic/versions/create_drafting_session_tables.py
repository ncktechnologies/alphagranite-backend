"""create drafting sessions tables

Revision ID: 2025010901
Revises: 36b7386d9414
Create Date: 2025-01-09
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = '2025010901'
down_revision = '36b7386d9414'  # Current head: alter_drafting_numeric_columns
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'drafting_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('drafter_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='drafting'),
        sa.Column('session_start_time', sa.DateTime(), nullable=False),
        sa.Column('session_end_time', sa.DateTime(), nullable=True),
        sa.Column('current_pause_start_time', sa.DateTime(), nullable=True),
        sa.Column('total_pause_duration', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_time_spent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cumulative_sqft_drafted', sa.String(), nullable=True, server_default='0'),
        sa.Column('work_percentage_done', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_drafting_sessions_fab_id', 'drafting_sessions', ['fab_id'])
    
    op.create_table(
        'drafting_session_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('fab_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('sqft_drafted', sa.String(), nullable=True),
        sa.Column('work_percentage_done', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_drafting_session_notes_session_id', 'drafting_session_notes', ['session_id'])
    op.create_index('ix_drafting_session_notes_fab_id', 'drafting_session_notes', ['fab_id'])


def downgrade() -> None:
    op.drop_table('drafting_session_notes')
    op.drop_table('drafting_sessions')