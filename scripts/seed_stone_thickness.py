"""
Stone Thickness Seeder Script

This script seeds the stone_thickness table with predefined thickness values.
Run this script to populate the database with default stone thickness options.
"""

import os
import sys
import asyncio
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Stone thickness data (in the specified order)
STONE_THICKNESS_DATA = [
    {"thickness": "3cm", "thickness_mm": 30.0, "description": "Standard thick slab - 3 centimeters"},
    {"thickness": "2cm", "thickness_mm": 20.0, "description": "Standard medium slab - 2 centimeters"},
    {"thickness": "1.6cm", "thickness_mm": 16.0, "description": "Medium-thin slab - 1.6 centimeters"},
    {"thickness": "1.8cm", "thickness_mm": 18.0, "description": "Medium slab - 1.8 centimeters"},
    {"thickness": "1cm", "thickness_mm": 10.0, "description": "Thin slab - 1 centimeter"},
    {"thickness": "12mm", "thickness_mm": 12.0, "description": "12 millimeter thin slab"},
    {"thickness": "8mm", "thickness_mm": 8.0, "description": "8 millimeter ultra-thin slab"},
    {"thickness": "6mm", "thickness_mm": 6.0, "description": "6 millimeter ultra-thin slab"},
    {"thickness": "4mm", "thickness_mm": 4.0, "description": "4 millimeter ultra-thin slab"},
]


def get_sync_url(database_url: str) -> str:
    """Convert async database URL to sync for migrations."""
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    return database_url


def seed_stone_thickness():
    """Seed the stone_thickness table with predefined values."""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    # Convert to sync URL
    sync_url = get_sync_url(database_url)
    print(f"📦 Using database: {sync_url.split('@')[-1] if '@' in sync_url else sync_url}")
    
    try:
        # Create engine and session
        engine = create_engine(sync_url)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            print("🔍 Checking existing stone thickness records...")
            
            # Check if any stone thickness records already exist
            result = session.execute(text("SELECT COUNT(*) FROM stone_thickness"))
            existing_count = result.scalar()
            
            if existing_count > 0:
                print(f"⚠️  Found {existing_count} existing stone thickness records.")
                response = input("Do you want to continue and add new records (duplicates will be skipped)? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("🚫 Seeding cancelled.")
                    return False
            
            print("🌱 Starting stone thickness seeding...")
            
            # Get a default user ID for created_by (try to find first superuser)
            user_result = session.execute(text("SELECT id FROM users WHERE is_super_admin = true LIMIT 1"))
            user_row = user_result.first()
            
            if not user_row:
                print("❌ No superuser found. Please create a superuser first.")
                return False
            
            created_by_user_id = user_row[0]
            print(f"👤 Using user ID {created_by_user_id} as creator")
            
            # Active status ID (assuming 1 is active)
            status_id = 1
            
            added_count = 0
            skipped_count = 0
            
            for thickness_data in STONE_THICKNESS_DATA:
                try:
                    # Check if this thickness already exists
                    check_result = session.execute(
                        text("SELECT id FROM stone_thickness WHERE thickness = :thickness"),
                        {"thickness": thickness_data["thickness"]}
                    )
                    
                    if check_result.first():
                        print(f"⏭️  Skipping {thickness_data['thickness']} (already exists)")
                        skipped_count += 1
                        continue
                    
                    # Insert new stone thickness
                    insert_query = text("""
                        INSERT INTO stone_thickness (thickness, thickness_mm, description, status_id, created_by, created_at)
                        VALUES (:thickness, :thickness_mm, :description, :status_id, :created_by, :created_at)
                    """)
                    
                    session.execute(insert_query, {
                        "thickness": thickness_data["thickness"],
                        "thickness_mm": thickness_data["thickness_mm"],
                        "description": thickness_data["description"],
                        "status_id": status_id,
                        "created_by": created_by_user_id,
                        "created_at": datetime.now()
                    })
                    
                    print(f"✅ Added stone thickness: {thickness_data['thickness']} ({thickness_data['thickness_mm']}mm)")
                    added_count += 1
                    
                except Exception as e:
                    print(f"❌ Error adding {thickness_data['thickness']}: {str(e)}")
                    continue
            
            # Commit all changes
            session.commit()
            
            print(f"\n🎉 Stone thickness seeding completed!")
            print(f"   ✅ Added: {added_count} records")
            print(f"   ⏭️  Skipped: {skipped_count} records")
            print(f"   📊 Total in database: {added_count + existing_count}")
            
            # Show final list
            print("\n📋 Current stone thickness records:")
            result = session.execute(text("""
                SELECT id, thickness, thickness_mm, description 
                FROM stone_thickness 
                ORDER BY thickness_mm DESC
            """))
            
            for row in result:
                print(f"   {row[0]:2d}. {row[1]:6s} ({row[2]:4.1f}mm) - {row[3]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False


if __name__ == "__main__":
    print("🏗️  Stone Thickness Seeder")
    print("=" * 50)
    
    success = seed_stone_thickness()
    
    if success:
        print("\n✨ Seeding completed successfully!")
    else:
        print("\n💥 Seeding failed!")
        sys.exit(1)