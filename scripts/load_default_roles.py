import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

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
                INSERT INTO roles (name, description, created_at, updated_at)
                VALUES (:name, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO NOTHING
            """), {"name": name, "description": description})
        # Ensure permissions table exists
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                module VARCHAR(100),
                action VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Get action menu items
        result = db.execute(text("SELECT id, code FROM action_menus"))
        menu_items = {row[1]: row[0] for row in result.fetchall()}
        # Default permissions
        permissions = []
        for menu_slug, menu_id in menu_items.items():
            permissions.extend([
                (f"{menu_slug}.create", f"Create {menu_slug}", menu_slug, "create"),
                (f"{menu_slug}.read", f"View {menu_slug}", menu_slug, "read"),
                (f"{menu_slug}.update", f"Update {menu_slug}", menu_slug, "update"),
                (f"{menu_slug}.delete", f"Delete {menu_slug}", menu_slug, "delete")
            ])
        permissions.extend([
            ("reports.read", "View reports", "reports", "read"),
            ("system.admin", "System administration", "system", "admin")
        ])
        for name, description, module, action in permissions:
            db.execute(text("""
                INSERT INTO permissions (name, description, module, action, created_at)
                VALUES (:name, :description, :module, :action, CURRENT_TIMESTAMP)
                ON CONFLICT (name) DO NOTHING
            """), {"name": name, "description": description, "module": module, "action": action})
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