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

def load_default_roles():
    """Load default roles into the database"""
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
        # Ensure roles table exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Default roles
        roles = [
            ("Super Administrator", "Full system access and administration"),
            ("Administrator", "System administration with limited super admin functions"),
            ("Sales Manager", "Manages sales team and operations"),
            ("Sales", "Sales representative access"),
            ("Operations Manager", "Manages daily operations"),
            ("Fabrication Manager", "Manages fabrication processes"),
            ("Fabricator", "Fabrication worker access"),
            ("Template", "Template creation and management"),
            ("CAD Lead", "Lead CAD designer with team management"),
            ("CAD", "CAD design and drafting"),
            ("Installer", "Installation team access"),
            ("Install Scheduling", "Installation scheduling and coordination"),
            ("Purchasing", "Purchasing and procurement"),
            ("Template & Production Scheduling", "Production planning and scheduling"),
            ("Material Handler", "Material handling and inventory"),
            ("Accounting", "Financial and accounting access"),
            ("View Only", "Read-only access to system")
        ]
        # Get Active status value_id from status table
        result = db.execute(text("SELECT value_id FROM status WHERE slug = 'active'"))
        active_status = result.fetchone()
        active_status_id = active_status[0] if active_status else 1
        # Insert roles
        for name, description in roles:
            db.execute(text("""
                INSERT INTO roles (name, description, status, created_at, updated_at)
                VALUES (:name, :description, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO NOTHING
            """), {"name": name, "description": description, "status": active_status_id})
        # Ensure permissions table exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                can_create BOOLEAN DEFAULT false,
                can_update BOOLEAN DEFAULT false,
                can_delete BOOLEAN DEFAULT false,
                can_read BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Get action menu items
        result = db.execute(text("SELECT id, code FROM action_menus"))
        menu_items = {row[1]: row[0] for row in result.fetchall()}
        # Default permissions - simplified to match Permission model
        permissions = []
        for menu_slug, menu_id in menu_items.items():
            # Create one permission per action menu with all CRUD flags
            permissions.append((
                f"{menu_slug}.all",
                f"Full access to {menu_slug}",
                True, True, True, True  # can_create, can_read, can_update, can_delete
            ))
        # Add system-wide permissions
        permissions.append(("reports.view", "View reports", False, True, False, False))
        permissions.append(("system.admin", "System administration", True, True, True, True))
        
        for name, description, can_create, can_read, can_update, can_delete in permissions:
            db.execute(text("""
                INSERT INTO permissions (name, description, can_create, can_read, can_update, can_delete, created_at, updated_at)
                VALUES (:name, :description, :can_create, :can_read, :can_update, :can_delete, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO NOTHING
            """), {
                "name": name,
                "description": description,
                "can_create": can_create,
                "can_read": can_read,
                "can_update": can_update,
                "can_delete": can_delete
            })
        # Ensure role_permissions table exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                id SERIAL PRIMARY KEY,
                role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
                action_menu_id INTEGER REFERENCES action_menus(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(role_id, permission_id)
            )
        """))
        # Assign all permissions to Super Administrator
        result = db.execute(text("SELECT id FROM roles WHERE name = 'Super Administrator'"))
        super_admin = result.fetchone()
        if super_admin:
            super_admin_id = super_admin[0]
            result = db.execute(text("SELECT id FROM permissions"))
            permission_ids = [row[0] for row in result.fetchall()]
            for perm_id in permission_ids:
                db.execute(text("""
                    INSERT INTO role_permissions (role_id, permission_id, created_at)
                    VALUES (:role_id, :perm_id, CURRENT_TIMESTAMP)
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                """), {"role_id": super_admin_id, "perm_id": perm_id})
        print("Default roles and permissions loaded successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error loading roles and permissions: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    load_default_roles()