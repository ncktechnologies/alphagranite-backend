"""
Setup Template Scheduler and Install Scheduler roles with their permissions
Run this script to initialize the role-permission system
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

load_dotenv()

def setup_scheduler_roles():
    """Setup Template Scheduler and Install Scheduler roles with permissions"""
    # Database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    # Convert async URL to sync for this script
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("Setting up Template Scheduler and Install Scheduler roles")
        print("=" * 70)
        
        # Get Active status value_id from status table
        result = db.execute(text("SELECT value_id FROM status WHERE slug = 'active'"))
        active_status = result.fetchone()
        active_status_id = active_status[0] if active_status else 1
        
        # Define roles
        roles = [
            {
                "name": "TEMPLATE SCHEDULER",
                "description": "Template scheduling with access to Templating, Pre-draft, Drafting, and FAB creation",
                "permissions": ["TEMPLATING", "PREDRAFT", "DRAFTING", "fabids"]
            },
            {
                "name": "INSTALL SCHEDULER",
                "description": "Installation scheduling with access to Drafting",
                "permissions": ["DRAFTING"]
            }
        ]
        
        # Insert roles and their permissions
        for role_data in roles:
            role_name = role_data["name"]
            role_description = role_data["description"]
            
            # Insert role
            result = db.execute(text("""
                INSERT INTO roles (name, description, status, created_at, updated_at)
                VALUES (:name, :description, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO UPDATE 
                SET description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """), {"name": role_name, "description": role_description, "status": active_status_id})
            
            role = result.fetchone()
            role_id = role[0] if role else None
            
            if not role_id:
                # If no RETURNING, fetch the role_id
                result = db.execute(text("SELECT id FROM roles WHERE name = :name"), {"name": role_name})
                role = result.fetchone()
                role_id = role[0] if role else None
            
            print(f"\n✓ Role created/updated: {role_name} (ID: {role_id})")
            
            # Create/update permissions for this role
            for perm_name in role_data["permissions"]:
                # Insert permission if not exists
                db.execute(text("""
                    INSERT INTO permissions (name, description, can_create, can_read, can_update, can_delete, created_at, updated_at)
                    VALUES (:name, :description, true, true, true, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (name) DO NOTHING
                """), {
                    "name": perm_name,
                    "description": f"Access to {perm_name} functionality"
                })
                
                # Get permission ID
                result = db.execute(text("SELECT id FROM permissions WHERE name = :name"), {"name": perm_name})
                perm = result.fetchone()
                perm_id = perm[0] if perm else None
                
                if perm_id:
                    # For fabids permission, link to fabids action_menu
                    action_menu_id = None
                    if perm_name == "fabids":
                        # Get fabids action_menu_id
                        menu_result = db.execute(text("SELECT id FROM action_menus WHERE code = :code"), {"code": "fabids"})
                        menu = menu_result.fetchone()
                        action_menu_id = menu[0] if menu else None
                    
                    # Link role to permission via role_permissions table
                    db.execute(text("""
                        INSERT INTO role_permissions (role_id, permission_id, action_menu_id, created_at, updated_at)
                        VALUES (:role_id, :permission_id, :action_menu_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT DO NOTHING
                    """), {"role_id": role_id, "permission_id": perm_id, "action_menu_id": action_menu_id})
                    
                    print(f"  ✓ Permission linked: {perm_name} (ID: {perm_id}, Action Menu ID: {action_menu_id})")
        
        db.commit()
        
        print("\n" + "=" * 70)
        print("✅ Setup completed successfully!")
        print("=" * 70)
        print("\nRoles created:")
        print("  1. TEMPLATE SCHEDULER - Sees 3 widgets (TEMPLATING, PREDRAFT, DRAFTING)")
        print("  2. INSTALL SCHEDULER - Sees 2 widgets (DRAFTING)")
        print("\nUsers can be assigned to these roles via the user_roles table.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_scheduler_roles()
