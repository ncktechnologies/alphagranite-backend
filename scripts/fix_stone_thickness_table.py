"""
Add missing columns to tables
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

load_dotenv()

def add_missing_columns():
    """Add missing columns to tables"""
    # Database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found in environment variables")
        return
    
    # Convert async URL to sync for this script
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("Adding missing columns to tables...")
        
        # Add thickness_mm column to stone_thickness if it doesn't exist
        db.execute(text("""
            ALTER TABLE stone_thickness 
            ADD COLUMN IF NOT EXISTS thickness_mm DECIMAL(10, 2);
        """))
        
        # Add edge_type column to edges if it doesn't exist
        db.execute(text("""
            ALTER TABLE edges 
            ADD COLUMN IF NOT EXISTS edge_type VARCHAR(100);
        """))
        
        db.commit()
        print("✅ Columns added successfully!")
        print("   • stone_thickness.thickness_mm")
        print("   • edges.edge_type")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding columns: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_missing_columns()
