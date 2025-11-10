"""
Edges Seeder Script

This script seeds the edges table with predefined edge types.
Run this script to populate the database with default edge options.
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

# Edges data (alphabetically ordered)
EDGES_DATA = [
    {"name": "BEVEL", "edge_type": "Decorative", "description": "Angled edge cut at 45 degrees"},
    {"name": "BUTT JOINT LAMINATION", "edge_type": "Laminated", "description": "Edge-to-edge lamination joint"},
    {"name": "CHISEL", "edge_type": "Textured", "description": "Hand-chiseled textured edge"},
    {"name": "COVE", "edge_type": "Rounded", "description": "Concave rounded edge"},
    {"name": "COVE DUPONT", "edge_type": "Rounded", "description": "Dupont style concave rounded edge"},
    {"name": "CUSTOM", "edge_type": "Custom", "description": "Custom designed edge profile"},
    {"name": "DEMI BULLNOSE", "edge_type": "Rounded", "description": "Half rounded bullnose edge"},
    {"name": "DUPONT", "edge_type": "Decorative", "description": "Classic Dupont edge profile"},
    {"name": "FLAT HONED", "edge_type": "Flat", "description": "Flat edge with honed finish"},
    {"name": "FLAT POLISH", "edge_type": "Flat", "description": "Flat edge with polished finish"},
    {"name": "FULL BULLNOSE", "edge_type": "Rounded", "description": "Complete rounded bullnose edge"},
    {"name": "HALF BULLNOSE", "edge_type": "Rounded", "description": "Half rounded bullnose edge"},
    {"name": "MITER", "edge_type": "Angled", "description": "Mitered edge joint at angle"},
    {"name": "OGEE", "edge_type": "Decorative", "description": "S-shaped decorative edge"},
    {"name": "PLANER", "edge_type": "Flat", "description": "Flat planed edge"},
    {"name": "SMALL OGEE", "edge_type": "Decorative", "description": "Smaller S-shaped decorative edge"},
    {"name": "STACKED", "edge_type": "Laminated", "description": "Multiple layer stacked edge"},
    {"name": "WATERFALL", "edge_type": "Continuous", "description": "Continuous waterfall edge"},
    {"name": "WIDE BULLNOSE", "edge_type": "Rounded", "description": "Wide rounded bullnose edge"},
]


def get_sync_url(database_url: str) -> str:
    """Convert async database URL to sync for migrations."""
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    return database_url


def seed_edges():
    """Seed the edges table with predefined values."""
    
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
            print("🔍 Checking existing edges records...")
            
            # Check if any edges records already exist
            result = session.execute(text("SELECT COUNT(*) FROM edges"))
            existing_count = result.scalar()
            
            if existing_count > 0:
                print(f"⚠️  Found {existing_count} existing edges records.")
                response = input("Do you want to continue and add new records (duplicates will be skipped)? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("🚫 Seeding cancelled.")
                    return False
            
            print("🌱 Starting edges seeding...")
            
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
            
            for edge_data in EDGES_DATA:
                try:
                    # Check if this edge already exists
                    check_result = session.execute(
                        text("SELECT id FROM edges WHERE name = :name"),
                        {"name": edge_data["name"]}
                    )
                    
                    if check_result.first():
                        print(f"⏭️  Skipping {edge_data['name']} (already exists)")
                        skipped_count += 1
                        continue
                    
                    # Insert new edge
                    insert_query = text("""
                        INSERT INTO edges (name, edge_type, description, status_id, created_by, created_at)
                        VALUES (:name, :edge_type, :description, :status_id, :created_by, :created_at)
                    """)
                    
                    session.execute(insert_query, {
                        "name": edge_data["name"],
                        "edge_type": edge_data["edge_type"],
                        "description": edge_data["description"],
                        "status_id": status_id,
                        "created_by": created_by_user_id,
                        "created_at": datetime.now()
                    })
                    
                    print(f"✅ Added edge: {edge_data['name']} ({edge_data['edge_type']}) - {edge_data['description']}")
                    added_count += 1
                    
                except Exception as e:
                    print(f"❌ Error adding {edge_data['name']}: {str(e)}")
                    continue
            
            # Commit all changes
            session.commit()
            
            print(f"\n🎉 Edges seeding completed!")
            print(f"   ✅ Added: {added_count} records")
            print(f"   ⏭️  Skipped: {skipped_count} records")
            print(f"   📊 Total in database: {added_count + existing_count}")
            
            # Show final list grouped by edge type
            print("\n📋 Current edges records (grouped by type):")
            result = session.execute(text("""
                SELECT id, name, edge_type, description 
                FROM edges 
                ORDER BY edge_type ASC, name ASC
            """))
            
            current_type = ""
            for row in result:
                if row[2] != current_type:
                    current_type = row[2]
                    print(f"\n   {current_type.upper()} EDGES:")
                print(f"     {row[0]:2d}. {row[1]:<25s} - {row[3]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False


if __name__ == "__main__":
    print("🏗️  Edges Seeder")
    print("=" * 50)
    
    success = seed_edges()
    
    if success:
        print("\n✨ Seeding completed successfully!")
    else:
        print("\n💥 Seeding failed!")
        sys.exit(1)