"""Script to clear all FABs and related workflow data from the database"""
import asyncio
import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.app.database import engine

async def clear_all_fabs():
    """Delete all FABs and related workflow stage data"""
    
    async with engine.begin() as conn:
        print("Clearing all FAB workflow data...")
        
        # Delete in order to respect foreign key constraints
        tables = [
            'fab_notes',
            'templatings',
            'draftings',
            'pre_draft_reviews',
            'slab_smiths',
            'sales_cts',
            'cut_list',
            'final_programmings',
            'wj_programmings',
            'wj_schedulings',
            'resurface_schedulings',
            'revisions',
            'cost_of_stones',
            'install_schedulings',
            'install_completions',
            'fabs'
        ]
        
        for table in tables:
            result = await conn.execute(text(f'DELETE FROM {table}'))
            deleted_count = result.rowcount
            print(f"  ✓ Cleared {deleted_count} records from {table}")
        
        print("\n✅ All FABs and related workflow data cleared successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(clear_all_fabs())

