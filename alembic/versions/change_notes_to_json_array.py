"""change notes to json array

Revision ID: notes_to_json_array
Revises: ab9dd56baec0
Create Date: 2025-11-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'notes_to_json_array'
down_revision = 'ab9dd56baec0'  # Current head
branch_labels = None
depends_on = None


def upgrade():
    """
    Change notes columns from TEXT to JSONB array across all tables.
    Preserves existing notes by converting them to single-element arrays.
    Only processes tables where the notes column exists.
    """
    
    # List of tables with notes columns
    tables_with_notes = [
        'fabs',
        'templatings',
        'final_programmings',
        'job_technician_workflows',
        'operation_workflow'
    ]
    
    for table in tables_with_notes:
        # Check if notes column exists before processing
        connection = op.get_bind()
        result = connection.execute(sa.text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table}' AND column_name = 'notes'
        """))
        
        if result.fetchone():
            # Step 1: Add new JSONB column
            op.add_column(table, sa.Column('notes_new', postgresql.JSONB, nullable=True))
            
            # Step 2: Migrate existing data - convert string to array
            op.execute(sa.text(f"""
                UPDATE {table}
                SET notes_new = CASE 
                    WHEN notes IS NULL OR notes = '' THEN '[]'::jsonb
                    ELSE jsonb_build_array(notes)
                END
            """))
            
            # Step 3: Drop old column
            op.drop_column(table, 'notes')
            
            # Step 4: Rename new column to notes
            op.alter_column(table, 'notes_new', new_column_name='notes')


def downgrade():
    """
    Revert notes columns from JSONB array back to TEXT.
    Takes the first element of the array if it exists.
    """
    
    tables_with_notes = [
        'fabs',
        'templatings',
        'final_programmings',
        'job_technician_workflows',
        'operation_workflow'
    ]
    
    for table in tables_with_notes:
        # Check if notes column exists before processing
        connection = op.get_bind()
        result = connection.execute(sa.text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table}' AND column_name = 'notes'
        """))
        
        if result.fetchone():
            # Step 1: Add new TEXT column
            op.add_column(table, sa.Column('notes_new', sa.Text, nullable=True))
            
            # Step 2: Migrate data back - take first element of array
            op.execute(sa.text(f"""
                UPDATE {table}
                SET notes_new = CASE 
                    WHEN jsonb_array_length(notes) > 0 THEN notes->>0
                    ELSE NULL
                END
            """))
            
            # Step 3: Drop JSONB column
            op.drop_column(table, 'notes')
            
            # Step 4: Rename new column to notes
            op.alter_column(table, 'notes_new', new_column_name='notes')
