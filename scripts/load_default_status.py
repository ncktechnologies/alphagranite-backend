import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

load_dotenv()

def load_default_status():
    """Load default status values into the database"""
    
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
        # Check if status table exists and get its structure
        result = db.execute(text("""
            SELECT column_name, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'status' AND table_schema = 'public'
        """))
        existing_columns = {row[0]: {'nullable': row[1], 'default': row[2]} for row in result.fetchall()}
        
        if not existing_columns:
            # Create status table if not exists
            db.execute(text("""
                CREATE TABLE status (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL UNIQUE,
                    value_id INTEGER NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        
        # Default status values
        status_values = [
            (1, "Active", "active"),
            (2, "Inactive", "inactive"),
            (3, "Deleted", "deleted"),
            (4, "Pending", "pending"),
            (5, "Suspended", "suspended"),
            (6, "Archived", "archived"),
            (7, "Draft", "draft"),
            (8, "Completed", "completed")
        ]
        
        # Insert status values
        for value_id, name, slug in status_values:
            db.execute(text("""
                INSERT INTO status (value_id, name, slug, created_at, updated_at) 
                VALUES (:value_id, :name, :slug, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (value_id) DO NOTHING
            """), {"value_id": value_id, "name": name, "slug": slug})
        
        db.commit()
        
        # Display loaded status values
        result = db.execute(text("SELECT value_id, name, slug FROM status ORDER BY value_id"))
        status_loaded = result.fetchall()
        
        print("✅ Default status values loaded successfully!")
        print(f"\nLoaded {len(status_loaded)} status values:")
        for status in status_loaded:
            print(f"  - {status[0]}: {status[1]} ({status[2]})")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error loading status values: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    load_default_status()