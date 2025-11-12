"""
Create missing tables that aren't in the current database schema
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

def create_missing_tables():
    """Create missing tables in the database"""
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
        print("Creating missing tables...")
        
        # Create accounts table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                account_number VARCHAR(100) UNIQUE,
                description TEXT,
                contact_person VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(50),
                address TEXT,
                status_id INTEGER NOT NULL REFERENCES status(value_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by INTEGER NOT NULL REFERENCES users(id),
                updated_at TIMESTAMP,
                updated_by INTEGER REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS ix_accounts_name ON accounts(name);
            CREATE INDEX IF NOT EXISTS ix_accounts_account_number ON accounts(account_number);
        """))
        
        # Create stone_colors table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS stone_colors (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                color_code VARCHAR(50),
                status_id INTEGER NOT NULL REFERENCES status(value_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by INTEGER NOT NULL REFERENCES users(id),
                updated_at TIMESTAMP,
                updated_by INTEGER REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS ix_stone_colors_name ON stone_colors(name);
        """))
        
        # Create stone_types table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS stone_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                status_id INTEGER NOT NULL REFERENCES status(value_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by INTEGER NOT NULL REFERENCES users(id),
                updated_at TIMESTAMP,
                updated_by INTEGER REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS ix_stone_types_name ON stone_types(name);
        """))
        
        # Create stone_thickness table  
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS stone_thickness (
                id SERIAL PRIMARY KEY,
                thickness VARCHAR(50) NOT NULL UNIQUE,
                thickness_mm DECIMAL(10, 2),
                description TEXT,
                status_id INTEGER NOT NULL REFERENCES status(value_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by INTEGER NOT NULL REFERENCES users(id),
                updated_at TIMESTAMP,
                updated_by INTEGER REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS ix_stone_thickness_thickness ON stone_thickness(thickness);
        """))
        
        # Create edges table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS edges (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                edge_type VARCHAR(100),
                description TEXT,
                status_id INTEGER NOT NULL REFERENCES status(value_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                created_by INTEGER NOT NULL REFERENCES users(id),
                updated_at TIMESTAMP,
                updated_by INTEGER REFERENCES users(id)
            );
            CREATE INDEX IF NOT EXISTS ix_edges_name ON edges(name);
        """))
        
        db.commit()
        print("✅ Missing tables created successfully!")
        print("   • accounts")
        print("   • stone_colors")
        print("   • stone_types")
        print("   • stone_thickness")
        print("   • edges")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating tables: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_missing_tables()
