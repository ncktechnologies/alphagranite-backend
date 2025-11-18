"""
Script to add missing columns to the fabs table
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.app.interface.database import get_db_session

async def fix_fabs_table():
    """Add missing columns to fabs table"""
    
    async for db in get_db_session():
        try:
            print("Checking and adding missing columns to fabs table...")
            
            # Add stone_type_id column
            await db.execute(text("""
                ALTER TABLE fabs 
                ADD COLUMN IF NOT EXISTS stone_type_id INTEGER REFERENCES stone_types(id);
            """))
            print("✓ Added stone_type_id column")
            
            # Add stone_color_id column
            await db.execute(text("""
                ALTER TABLE fabs 
                ADD COLUMN IF NOT EXISTS stone_color_id INTEGER REFERENCES stone_colors(id);
            """))
            print("✓ Added stone_color_id column")
            
            # Add stone_thickness_id column
            await db.execute(text("""
                ALTER TABLE fabs 
                ADD COLUMN IF NOT EXISTS stone_thickness_id INTEGER REFERENCES stone_thickness(id);
            """))
            print("✓ Added stone_thickness_id column")
            
            # Add edge_id column
            await db.execute(text("""
                ALTER TABLE fabs 
                ADD COLUMN IF NOT EXISTS edge_id INTEGER REFERENCES edges(id);
            """))
            print("✓ Added edge_id column")
            
            await db.commit()
            print("\n✅ Successfully added all missing columns to fabs table!")
            
            # Verify the columns
            result = await db.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'fabs' 
                AND column_name IN ('stone_type_id', 'stone_color_id', 'stone_thickness_id', 'edge_id')
                ORDER BY column_name;
            """))
            columns = result.fetchall()
            
            print("\nVerified columns:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_fabs_table())
