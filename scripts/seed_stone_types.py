"""
Stone Types Seeder Script

This script seeds the stone_types table with predefined stone type values.
Run this script to populate the database with default stone type options.
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

# Stone types data (alphabetically ordered)
STONE_TYPES_DATA = [
    {"name": "CAMBRIA", "description": "Cambria"},
    {"name": "CS", "description": "Caesarstone"},
    {"name": "DELLA TERRA QUARTZ", "description": "Della Terra Quartz"},
    {"name": "DK", "description": "Dekton"},
    {"name": "GS", "description": "Granite"},
    {"name": "LS", "description": "Limestone"},
    {"name": "MS", "description": "Marble"},
    {"name": "MSI Q-QUARTZ", "description": "MSI Q Quartz"},
    {"name": "NEOLITH", "description": "Neolith"},
    {"name": "ONYX", "description": "Onyx"},
    {"name": "PC-CAESARSTONE", "description": "Caesarstone Porcelain"},
    {"name": "PC-DELLA TERRA", "description": "Della Terra Porcelain"},
    {"name": "PC-PANORAMIC", "description": "Panoramic Porcelain"},
    {"name": "PC-PORCELANOSA", "description": "Porcelanosa Porcelain"},
    {"name": "PC-STRATUS", "description": "Stratus Porcelain"},
    {"name": "PQ", "description": "Pental Quartz"},
    {"name": "QZ", "description": "Quartzite"},
    {"name": "SANDSTONE", "description": "Sandstone"},
    {"name": "SOAPSTONE", "description": "Soapstone"},
    {"name": "SQ", "description": "Stratus Quartz"},
    {"name": "SS", "description": "Silestone"},
    {"name": "TERRAZZO", "description": "Terrazzo"},
    {"name": "TRAVERTINE", "description": "Travertine"},
]


def get_sync_url(database_url: str) -> str:
    """Convert async database URL to sync for migrations."""
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    return database_url


def seed_stone_types():
    """Seed the stone_types table with predefined values."""
    
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
            print("🔍 Checking existing stone types records...")
            
            # Check if any stone types records already exist
            result = session.execute(text("SELECT COUNT(*) FROM stone_types"))
            existing_count = result.scalar()
            
            if existing_count > 0:
                print(f"⚠️  Found {existing_count} existing stone types records.")
                response = input("Do you want to continue and add new records (duplicates will be skipped)? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("🚫 Seeding cancelled.")
                    return False
            
            print("🌱 Starting stone types seeding...")
            
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
            
            for stone_type_data in STONE_TYPES_DATA:
                try:
                    # Check if this stone type already exists
                    check_result = session.execute(
                        text("SELECT id FROM stone_types WHERE name = :name"),
                        {"name": stone_type_data["name"]}
                    )
                    
                    if check_result.first():
                        print(f"⏭️  Skipping {stone_type_data['name']} (already exists)")
                        skipped_count += 1
                        continue
                    
                    # Insert new stone type
                    insert_query = text("""
                        INSERT INTO stone_types (name, description, status_id, created_by, created_at)
                        VALUES (:name, :description, :status_id, :created_by, :created_at)
                    """)
                    
                    session.execute(insert_query, {
                        "name": stone_type_data["name"],
                        "description": stone_type_data["description"],
                        "status_id": status_id,
                        "created_by": created_by_user_id,
                        "created_at": datetime.now()
                    })
                    
                    print(f"✅ Added stone type: {stone_type_data['name']} - {stone_type_data['description']}")
                    added_count += 1
                    
                except Exception as e:
                    print(f"❌ Error adding {stone_type_data['name']}: {str(e)}")
                    continue
            
            # Commit all changes
            session.commit()
            
            print(f"\n🎉 Stone types seeding completed!")
            print(f"   ✅ Added: {added_count} records")
            print(f"   ⏭️  Skipped: {skipped_count} records")
            print(f"   📊 Total in database: {added_count + existing_count}")
            
            # Show final list
            print("\n📋 Current stone types records:")
            result = session.execute(text("""
                SELECT id, name, description 
                FROM stone_types 
                ORDER BY name ASC
            """))
            
            for row in result:
                print(f"   {row[0]:2d}. {row[1]:<20s} - {row[2]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False


if __name__ == "__main__":
    print("🏗️  Stone Types Seeder")
    print("=" * 50)
    
    success = seed_stone_types()
    
    if success:
        print("\n✨ Seeding completed successfully!")
    else:
        print("\n💥 Seeding failed!")
        sys.exit(1)