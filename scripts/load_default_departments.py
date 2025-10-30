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

def load_default_departments():
    """Load default departments into the database"""
    
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
        # Check if departments table exists and get its structure
        result = db.execute(text("""
            SELECT column_name, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'departments' AND table_schema = 'public'
        """))
        existing_columns = {row[0]: {'nullable': row[1], 'default': row[2]} for row in result.fetchall()}
        
        if not existing_columns:
            # Create departments table if not exists
            db.execute(text("""
                CREATE TABLE departments (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        
        # Default departments
        departments = [
            ("CAD", "Computer-Aided Design department"),
            ("FABRICATION", "Manufacturing and fabrication operations"),
            ("INSTALL", "Installation and field services"),
            ("OFFICE", "Administrative and office operations"),
            ("SALES", "Sales and customer relations"),
            ("TEMPLATE", "Template creation and production"),
            ("WAREHOUSE", "Warehouse and inventory management")
        ]
        
        # Get Active status value_id from status table
        result = db.execute(text("SELECT value_id FROM status WHERE slug = 'active'"))
        active_status = result.fetchone()
        if not active_status:
            raise Exception("'active' status not found in status table. Please seed status values first.")
        active_status_id = active_status[0]
        
        # Insert departments with proper column handling
        for name, description in departments:
            # Build insert query based on existing table structure
            if 'status' in existing_columns:
                db.execute(text("""
                    INSERT INTO departments (name, description, status, created_at, updated_at) 
                    VALUES (:name, :description, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": name, "description": description, "status": active_status_id})
            elif 'created_at' in existing_columns and existing_columns['created_at']['nullable'] == 'NO':
                db.execute(text("""
                    INSERT INTO departments (name, description, created_at, updated_at) 
                    VALUES (:name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": name, "description": description})
            else:
                db.execute(text("""
                    INSERT INTO departments (name, description) 
                    VALUES (:name, :description)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": name, "description": description})
        
        db.commit()
        
        # Display loaded departments
        result = db.execute(text("SELECT id, name, description FROM departments ORDER BY name"))
        departments_loaded = result.fetchall()
        
        print("✅ Default departments loaded successfully!")
        print(f"\nLoaded {len(departments_loaded)} departments:")
        for dept in departments_loaded:
            print(f"  - {dept[1]}: {dept[2]}")
        return departments_loaded
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error loading departments: {str(e)}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    load_default_departments()