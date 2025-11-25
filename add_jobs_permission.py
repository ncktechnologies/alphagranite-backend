import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

load_dotenv()

def add_jobs_permission_to_template_scheduler():
    """Add jobs (templating) READ permission to TEMPLATE SCHEDULER role"""
    
    # Database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found in environment variables")
        return
    
    # Convert async URL to sync
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    
    engine = create_engine(sync_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get TEMPLATE SCHEDULER role
        role_result = db.execute(text("""
            SELECT id, name FROM roles WHERE name = 'TEMPLATE SCHEDULER'
        """))
        role = role_result.fetchone()
        
        if not role:
            print("❌ TEMPLATE SCHEDULER role not found")
            return
        
        role_id = role[0]
        print(f"✅ Found role: {role[1]} (ID: {role_id})")
        
        # Get the "jobs" action menu
        menu_result = db.execute(text("""
            SELECT id, name, code FROM action_menus WHERE code = 'jobs'
        """))
        menu = menu_result.fetchone()
        
        if not menu:
            print("❌ 'jobs' action menu not found")
            return
        
        menu_id = menu[0]
        print(f"✅ Found action menu: {menu[1]} (Code: {menu[2]}, ID: {menu_id})")
        
        # Create or get permission with READ access
        perm_result = db.execute(text("""
            SELECT id FROM permissions 
            WHERE can_create = FALSE 
            AND can_read = TRUE 
            AND can_update = FALSE 
            AND can_delete = FALSE
            LIMIT 1
        """))
        permission = perm_result.fetchone()
        
        if not permission:
            # Create new READ-only permission
            db.execute(text("""
                INSERT INTO permissions (can_create, can_read, can_update, can_delete)
                VALUES (FALSE, TRUE, FALSE, FALSE)
            """))
            db.commit()
            
            perm_result = db.execute(text("""
                SELECT id FROM permissions 
                WHERE can_create = FALSE 
                AND can_read = TRUE 
                AND can_update = FALSE 
                AND can_delete = FALSE
                LIMIT 1
            """))
            permission = perm_result.fetchone()
        
        permission_id = permission[0]
        print(f"✅ Using permission ID: {permission_id} (READ only)")
        
        # Check if role already has this permission
        check_result = db.execute(text("""
            SELECT id FROM role_permissions 
            WHERE role_id = :role_id 
            AND action_menu_id = :menu_id
        """), {"role_id": role_id, "menu_id": menu_id})
        
        existing = check_result.fetchone()
        
        if existing:
            print(f"⚠️  Role already has permission for this action menu")
            # Update to use the READ-only permission
            db.execute(text("""
                UPDATE role_permissions 
                SET permission_id = :permission_id
                WHERE role_id = :role_id 
                AND action_menu_id = :menu_id
            """), {"permission_id": permission_id, "role_id": role_id, "menu_id": menu_id})
            db.commit()
            print(f"✅ Updated permission to READ only")
        else:
            # Add the permission
            db.execute(text("""
                INSERT INTO role_permissions (role_id, action_menu_id, permission_id, created_at, updated_at)
                VALUES (:role_id, :menu_id, :permission_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {"role_id": role_id, "menu_id": menu_id, "permission_id": permission_id})
            db.commit()
            print(f"✅ Added 'jobs' READ permission to TEMPLATE SCHEDULER role")
        
        # Verify the permission was added
        verify_result = db.execute(text("""
            SELECT 
                am.name as menu_name,
                am.code as menu_code,
                p.can_create,
                p.can_read,
                p.can_update,
                p.can_delete
            FROM role_permissions rp
            JOIN action_menus am ON rp.action_menu_id = am.id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = :role_id
            ORDER BY am.name
        """), {"role_id": role_id})
        
        permissions = verify_result.fetchall()
        print(f"\n📋 All permissions for TEMPLATE SCHEDULER role:")
        for perm in permissions:
            menu_name, menu_code, can_create, can_read, can_update, can_delete = perm
            perms = []
            if can_create: perms.append("CREATE")
            if can_read: perms.append("READ")
            if can_update: perms.append("UPDATE")
            if can_delete: perms.append("DELETE")
            print(f"  - {menu_name} ({menu_code}): {', '.join(perms)}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    add_jobs_permission_to_template_scheduler()
