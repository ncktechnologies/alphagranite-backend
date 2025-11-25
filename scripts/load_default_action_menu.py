# -*- coding: utf-8 -*-
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

def load_default_action_menu():
    """Load default action menu items into the database"""
    
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
        # Check if action_menus table exists and get its structure
        result = db.execute(text("""
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'action_menus'
        """))
        existing_columns = {row[0]: {'nullable': row[1], 'default': row[2]} for row in result.fetchall()}

        if not existing_columns:
            # Create action_menus table with the minimal schema used by the app
            db.execute(text("""
                CREATE TABLE action_menus (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    code VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

        # Default action menu items (name, code)
        menu_items = [
            ("Employees", "employees"),
            ("Department", "department"),
            ("Jobs", "jobs"),
            ("Shop", "shop"),
            ("Settings", "settings"),
            ("Stone Thickness", "stone_thickness"),
            ("Stone Color", "stone_color"),
            ("Stone Type", "stone_type"),
            ("Edges", "edges"),
            ("Accounts", "accounts"),
            ("FAB IDs", "fabids"),
        ]

        # Insert action menu items idempotently (check by code)
        for name, code in menu_items:
            exists = db.execute(text("SELECT id FROM action_menus WHERE code = :code"), {"code": code}).fetchone()
            if not exists:
                db.execute(text("""
                    INSERT INTO action_menus (name, code, created_at, updated_at)
                    VALUES (:name, :code, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), {"name": name, "code": code})

        db.commit()

        # Display loaded menu items
        result = db.execute(text("SELECT id, name, code FROM action_menus ORDER BY id"))
        menu_loaded = result.fetchall()

        print("✅ Default action menu items loaded successfully!")
        print("\nLoaded {} menu items:".format(len(menu_loaded)))
        for menu in menu_loaded:
            print("  - {} ({})".format(menu[1], menu[2]))
        
    except Exception as e:
        db.rollback()
        print("❌ Error loading action menus items: {}".format(str(e)))
    finally:
        db.close()

if __name__ == "__main__":
    load_default_action_menu()