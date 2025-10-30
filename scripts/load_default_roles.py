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
        # Check if roles table exists and get its structure
        result = db.execute(text("""
            SELECT column_name, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'roles' AND table_schema = 'public'
        """))
        existing_columns = {row[0]: {'nullable': row[1], 'default': row[2]} for row in result.fetchall()}
        
        if not existing_columns:
            # Create roles table if not exists
            db.execute(text("""
                CREATE TABLE roles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        
        # Default roles based on the provided data
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
        try:
            result = db.execute(text("SELECT value_id FROM status WHERE slug = 'active'"))
            active_status = result.fetchone()
            active_status_id = active_status[0] if active_status else 1
        except:
            active_status_id = 1
        
        # Insert roles with proper column handling
        for name, description in roles:
            # Build insert query based on existing table structure
            if 'status' in existing_columns:
                db.execute(text("""
                    INSERT INTO roles (name, description, status, created_at, updated_at) 
                    VALUES (:name, :description, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": name, "description": description, "status": active_status_id})
            else:
                db.execute(text("""
                    INSERT INTO roles (name, description) 
                    VALUES (:name, :description)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": name, "description": description})
        
        # Check if permissions table exists and get its structure
        result = db.execute(text("""
            SELECT column_name, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'permissions' AND table_schema = 'public'
        """))
        perm_columns = {row[0]: {'nullable': row[1], 'default': row[2]} for row in result.fetchall()}
        
        if not perm_columns:
            # Create permissions table if not exists
            db.execute(text("""
                CREATE TABLE permissions (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    module VARCHAR(100),
                    action VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            perm_columns = {'name': {}, 'description': {}, 'module': {}, 'action': {}, 'created_at': {}}
        
        # Get action menu IDs for permissions
        result = db.execute(text("SELECT id, slug FROM action_menu"))
        menu_items = {row[1]: row[0] for row in result.fetchall()}
        
        # Default permissions based on action menu items
        permissions = []
        
        # Generate CRUD permissions for each menu item
        for menu_slug, menu_id in menu_items.items():
            permissions.extend([
                (f"{menu_slug}.create", f"Create {menu_slug}", menu_slug, "create"),
                (f"{menu_slug}.read", f"View {menu_slug}", menu_slug, "read"),
                (f"{menu_slug}.update", f"Update {menu_slug}", menu_slug, "update"),
                (f"{menu_slug}.delete", f"Delete {menu_slug}", menu_slug, "delete")
            ])
        
        # Add system-level permissions
        permissions.extend([
            ("reports.read", "View reports", "reports", "read"),
            ("system.admin", "System administration", "system", "admin")
        ])
        
        # Insert permissions based on existing table structure
        for name, description, module, action in permissions:
            # Check what columns exist and build appropriate insert
            if 'can_create' in perm_columns and 'can_read' in perm_columns:
                # Handle permissions table with CRUD boolean columns
                can_create = action == 'create'
                can_read = action == 'read'
                can_update = action == 'update'
                can_delete = action == 'delete'
                
                # Build column list based on what exists
                columns = ['name', 'description', 'can_create', 'can_read', 'can_update', 'can_delete']
                values = [':name', ':description', ':can_create', ':can_read', ':can_update', ':can_delete']
                params = {
                    "name": name, "description": description, 
                    "can_create": can_create, "can_read": can_read, 
                    "can_update": can_update, "can_delete": can_delete
                }
                
                # Add other common columns if they exist
                if 'created_at' in perm_columns:
                    columns.append('created_at')
                    values.append('CURRENT_TIMESTAMP')
                if 'updated_at' in perm_columns:
                    columns.append('updated_at')
                    values.append('CURRENT_TIMESTAMP')
                if 'status' in perm_columns:
                    columns.append('status')
                    values.append(':status')
                    params['status'] = active_status_id
                
                db.execute(text(f"""
                    INSERT INTO permissions ({', '.join(columns)}) 
                    VALUES ({', '.join(values)})
                    ON CONFLICT (name) DO NOTHING
                """), params)
            elif 'module' in perm_columns and 'action' in perm_columns:
                db.execute(text("""
                    INSERT INTO permissions (name, description, module, action) 
                    VALUES (:name, :description, :module, :action)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": name, "description": description, "module": module, "action": action})
            else:
                # Fallback to basic permissions table structure
                db.execute(text("""
                    INSERT INTO permissions (name, description) 
                    VALUES (:name, :description)
                    ON CONFLICT (name) DO NOTHING
                """), {"name": name, "description": description})
        
        # Check if role_permissions table exists
        result = db.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'role_permissions' AND table_schema = 'public'
        """))
        rp_columns = [row[0] for row in result.fetchall()]
        
        if not rp_columns:
            # Create role_permissions table if not exists
            db.execute(text("""
                CREATE TABLE role_permissions (
                    id SERIAL PRIMARY KEY,
                    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
                    action_menu_id INTEGER REFERENCES action_menu(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(role_id, permission_id)
                )
            """))
            rp_columns = ['id', 'role_id', 'permission_id', 'action_menu_id', 'created_at']
        
        # Assign permissions to Super Administrator (all permissions)
        # First check if assignments already exist to avoid duplicates
        result = db.execute(text("""
            SELECT COUNT(*) FROM role_permissions rp
            JOIN roles r ON r.id = rp.role_id
            WHERE r.name = 'Super Administrator'
        """))
        existing_count = result.fetchone()[0]
        
        if existing_count == 0:
            # Check what table name the foreign key actually references
            result = db.execute(text("""
                SELECT ccu.table_name 
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_name = 'role_permissions' 
                AND tc.constraint_type = 'FOREIGN KEY'
                AND ccu.column_name = 'action_menu_id'
            """))
            fk_table = result.fetchone()
            fk_table_name = fk_table[0] if fk_table else None
            
            if 'action_menu_id' in rp_columns and fk_table_name:
                # Check if the referenced table exists and has data
                result = db.execute(text(f"SELECT COUNT(*) FROM {fk_table_name}"))
                menu_count = result.fetchone()[0]
                
                if menu_count > 0:
                    # Try to match permissions to action menu items using the correct table name
                    db.execute(text(f"""
                        INSERT INTO role_permissions (role_id, permission_id, action_menu_id, created_at, updated_at)
                        SELECT DISTINCT r.id, p.id, 
                               CASE WHEN am.id IS NOT NULL THEN am.id ELSE NULL END,
                               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        FROM roles r, permissions p
                        LEFT JOIN {fk_table_name} am ON p.name LIKE am.slug || '.%'
                        WHERE r.name = 'Super Administrator'
                    """))
                else:
                    print(f"Warning: {fk_table_name} table is empty, inserting role_permissions without action_menu_id")
                    db.execute(text("""
                        INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
                        SELECT r.id, p.id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        FROM roles r, permissions p 
                        WHERE r.name = 'Super Administrator'
                    """))
            else:
                # Simple assignment without action_menu_id
                db.execute(text("""
                    INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
                    SELECT r.id, p.id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    FROM roles r, permissions p 
                    WHERE r.name = 'Super Administrator'
                """))
        
        db.commit()
        
        # Display loaded roles
        result = db.execute(text("SELECT id, name, description FROM roles ORDER BY name"))
        roles_loaded = result.fetchall()
        
        print("✅ Default roles and permissions loaded successfully!")
        print(f"\nLoaded {len(roles_loaded)} roles:")
        for role in roles_loaded:
            print(f"  - {role[1]}: {role[2]}")
            
        # Display permission counts
        result = db.execute(text("SELECT COUNT(*) FROM permissions"))
        perm_count = result.fetchone()[0]
        print(f"\nLoaded {perm_count} permissions")
        
        result = db.execute(text("SELECT COUNT(*) FROM role_permissions"))
        role_perm_count = result.fetchone()[0]
        print(f"Created {role_perm_count} role-permission assignments")
        
        # Show menu-based permissions
        result = db.execute(text("SELECT COUNT(*) FROM action_menu"))
        menu_count = result.fetchone()[0]
        print(f"Permissions based on {menu_count} action menu items")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error loading roles and permissions: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    load_default_roles()