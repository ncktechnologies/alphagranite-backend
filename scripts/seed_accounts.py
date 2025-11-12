"""
Seed script to populate accounts table from CSV data
"""
import sys
import asyncio
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.app.utils.config import get_dbt_db


async def seed_accounts():
    """Seed accounts from the CSV data"""
    
    # Account names from the CSV
    account_names = [
        "Aggie Construction",
        "AHS Construction",
        "Alexis Granite Design",
        "Alexis Justine Design",
        "Architectural Surfaces",
        "Archive Properties",
        "Arrowhead",
        "Austin Fieldworks, LLC",
        "Austin Living Landscapes",
        "Austin Pool Designs",
        "Austin Turnkey Services, Inc.",
        "B&O Construction",
        "Bang Design Studio",
        "Bartholomew, Michelle",
        "Baxter Builders Group",
        "Beacon Construction",
        "Bee Happy Houses",
        "Benchmark Design~Build",
        "Bide Studio",
        "Big Country Design & Construction",
        "Blacksmith Homes",
        "Blake Smith Construction",
        "Blue Horse Building & Design",
        "Brand H Const.",
        "Brent House Construction",
        "Brian K. Stevens Const.",
        "Brother Sun Builders",
        "Brown & Beaux",
        "Bruce Doxey",
        "Brunkenhoefer Construction",
        "Burgett, Paula",
        "Burnette Builders",
        "California Closets-TX Hill Country",
        "Camelot Custom Homes",
        "Campbell Brown Construction",
        "Canaan Modern",
        "Canco Construction",
        "Capital Construction Company",
        "Capitol City Contracting",
        "Cardwell Builders Inc.",
        "Caroline Pinkston",
        "Cathlyn Davis Design",
        "Cava Luxury Homes,LLC",
        "CB Crafted Homes",
        "CCG Development",
        "Centurion Homes",
        "CG&S Design-Build",
        "Classic Constructors",
        "Coastal Interiors",
        "Concept Services",
        "Coregon Building Company",
        "Crabtree Design Build",
        "Cuppett Kilpatrick",
        "Curran Construction",
        "Custom Sheet Metal",
        "Cutters Landscape",
        "Dalgleish Construction",
        "Davenport Builders",
        "David Smith Builders",
        "David Wilkes Builders",
        "Decorum Stone",
        "DeVos Commercial",
        "Direct Surfaces",
        "Divine Cabinets",
        "Double R Carpentry",
        "Dowbuilt",
        "Drees Custom Homes",
        "Drews Hunt Builders",
        "Drophouse Design",
        "Duecker Construction",
        "Edgewater Premier Pools",
        "Egmodern, llc",
        "elev8 Builders",
        "Elizabeth Baird Architecture & Design",
        "Enabler LLC",
        "Enchanted Landscape",
        "Encore Stone Studio",
        "Enve Builders",
        "Enviroplan Architects Planners",
        "Epic Design-Build",
        "Escarpment Construction",
        "FIA Homes",
        "Fleener Co., LLC",
        "Fletco Construction",
        "Floyd Smith",
        "Foursquare Builders, LLC",
        "Foyer Build",
        "Franklin Alan",
        "Freccia Group",
        "FSB Custom Homes, LLC",
        "Gail Bell",
        "Gasparini Custom Homes",
        "Gil Leija",
        "GNS Custom Stoneworks",
        "Godsey Homes",
        "Goliath Luxury Homes",
        "Gossett & Company, LLC",
        "Grace Hall Design",
        "Granite Radiance",
        "Graniteworks",
        "Hager Construction",
        "Hank Gregory Builders",
        "Havens Construction",
        "Hill Country Custom Homes",
        "Hilliard Services",
        "Hilltown Building Co.",
        "Home As Art",
        "Huddleston Custom Homes",
        "Hunter, Carol",
        "Hutte, Michael & Patti",
        "Ignite Outdoor Kitchens",
        "J K Bernhard Construction",
        "JAG Builders",
        "Jameson Interiors",
        "Jauregui Architect Builders",
        "Jay Corder Architect",
        "JM Construction",
        "John Phillip Builders",
        "Jordan Restoration, Inc.",
        "JP Studio Designs",
        "JT Tull Custom Homes",
        "Kaity Hoang",
        "Kimi Hannusch",
        "Kingwood Cabinets",
        "Kitchen Solvers",
        "Koch McIntyre Construction",
        "Kristen Nix Interiors",
        "L&S Homes",
        "Lake Group Builders",
        "Lakeline Homes",
        "Lavaca Building Company",
        "Liberty Construction Services",
        "Lilianne Steckel Interior Designer",
        "LJD Ranch",
        "Lucy Howard Design",
        "MA Renovation",
        "Maas Contracting Inc.",
        "MacConnell Renovations",
        "Makeway Const.",
        "Mark Spilotro",
        "Material Design",
        "Meeks Slack Construction",
        "Meridian Custom Homes",
        "Method Building Company",
        "Mezger Homes, LLC",
        "Miars Construction",
        "Modern Stoneworks",
        "Moontower Design And Build",
        "Mothers Ruin",
        "MOXI Construction",
        "Muncie Construction",
        "Munn Renovations",
        "N2 Stone",
        "Natalie Howe Design",
        "Natural Marble And Granite",
        "Newcastle Homes",
        "North Loop Builders, LLC",
        "Nurys LLC",
        "Objets Ltd.",
        "Outland Construction Co",
        "Page Paul Architecture",
        "The Pankonien Group",
        "PB Fine Construction",
        "Pecan Street Building Company",
        "Phil Jackson Studio",
        "Pilgrim Building Co.",
        "R Builders",
        "Randall Custom Homes",
        "Rauser Construction",
        "RD Horton Construction",
        "Red Dog Welding Co.",
        "RedOven Builds",
        "ReDunn Homes",
        "RenderATX",
        "Reyme Designs",
        "RisherMartin",
        "Round Rock Remodeling",
        "Ryan Hinkson Construction",
        "Saavedra Design Studio",
        "SAGIVS",
        "Sarah Isa Interiors",
        "Shoberg Homes",
        "Sierra Custom Remodeling",
        "Signature Cabinets",
        "Sky West Builders",
        "Smith Builders",
        "Spaces Designed",
        "Specialty Builders",
        "Stehling Construction",
        "Stewart and Company",
        "Straight & Level Construction Company",
        "Straight Stacked Tile & Stone",
        "Stratus Surfaces LLC",
        "Studio Sin Fin",
        "Tamim Works, LLC",
        "Tande Holdings, LLC",
        "Task Building LLC",
        "Tatanka Group",
        "Taunton, Lindsay",
        "TBC Services LLC",
        "Tenney Construction",
        "The Cabinetry Studio by Twelve Stones",
        "The Magic Helpers",
        "The Svendsson Brothers, LLC",
        "Toluca Granite",
        "Toor Countertops",
        "Townline Development",
        "Transfiguration Greek Orthodox Church",
        "Venco Construction",
        "Vick Homes",
        "Vinson Radke Homes",
        "Vintinner Construction",
        "Waller Building Company, LLC",
        "Warriner Construction, LLC",
        "Wheelhouse Design",
        "William Ham Construction",
        "Woodeye Construction",
        "Woodwerd",
        "Woolsey Construction",
        "Wyeth Custom Homes",
        "Yellow Door Design",
        "Zuber Construction",
    ]
    
    async for db in get_db():
        try:
            # Get the first user (system user) to use as created_by
            user_result = await db.execute(text("SELECT id FROM users LIMIT 1"))
            system_user = user_result.fetchone()
            
            if not system_user:
                print("❌ Error: No user found in the database. Please create a user first.")
                return
            
            created_by = system_user[0]
            
            # Check for existing accounts
            existing_result = await db.execute(text("SELECT name FROM accounts"))
            existing_names = {row[0] for row in existing_result.fetchall()}
            
            print(f"Found {len(existing_names)} existing accounts")
            
            # Add new accounts
            added_count = 0
            skipped_count = 0
            
            for account_name in account_names:
                if account_name in existing_names:
                    print(f"⏭️  Skipping existing account: {account_name}")
                    skipped_count += 1
                    continue
                
                # Insert new account using raw SQL
                await db.execute(text("""
                    INSERT INTO accounts (name, status_id, created_by, created_at)
                    VALUES (:name, :status_id, :created_by, CURRENT_TIMESTAMP)
                """), {
                    "name": account_name,
                    "status_id": 1,  # Active status
                    "created_by": created_by
                })
                added_count += 1
                print(f"✅ Adding account: {account_name}")
            
            # Commit all changes
            await db.commit()
            
            print(f"\n{'='*60}")
            print(f"✅ Seeding completed successfully!")
            print(f"   • Added: {added_count} accounts")
            print(f"   • Skipped: {skipped_count} existing accounts")
            print(f"   • Total in CSV: {len(account_names)} accounts")
            print(f"{'='*60}")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error seeding accounts: {str(e)}")
            raise
        finally:
            await db.close()


if __name__ == "__main__":
    print("Starting account seeding...")
    asyncio.run(seed_accounts())
