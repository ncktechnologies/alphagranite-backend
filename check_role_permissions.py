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

def check_role_permissions():
    """Check what permissions TEMPLATE SCHEDULER role has"""
    
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
        result = db.execute(text("""
            SELECT id, name FROM roles WHERE name LIKE '%TEMPLATE%'
        """))
        roles = result.fetchall()
        
        if not roles:
            print("❌ No roles found with 'TEMPLATE' in name")
            return
        
        print("📋 Roles found:")
        for role in roles:
            print(f"  - ID: {role[0]}, Name: {role[1]}")
        
        # Get permissions for each role
        for role in roles:
            role_id, role_name = role[0], role[1]
            print(f"\n🔍 Checking permissions for role: {role_name} (ID: {role_id})")
            
            # Get action menu permissions
            perm_result = db.execute(text("""
                SELECT 
                    am.id as menu_id,
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
            
            permissions = perm_result.fetchall()
            
            if not permissions:
                print(f"  ❌ No permissions found for this role")
            else:
                print(f"  ✅ Found {len(permissions)} action menu permissions:")
                for perm in permissions:
                    menu_id, menu_name, menu_code, can_create, can_read, can_update, can_delete = perm
                    perms = []
                    if can_create: perms.append("CREATE")
                    if can_read: perms.append("READ")
                    if can_update: perms.append("UPDATE")
                    if can_delete: perms.append("DELETE")
                    print(f"    - {menu_name} ({menu_code}): {', '.join(perms)}")
            
            # Get users assigned to this role
            users_result = db.execute(text("""
                SELECT u.id, u.username, u.email
                FROM user_roles ur
                JOIN users u ON ur.user_id = u.id
                WHERE ur.role_id = :role_id
            """), {"role_id": role_id})
            
            users = users_result.fetchall()
            if users:
                print(f"\n  👥 Users assigned to this role:")
                for user in users:
                    print(f"    - {user[1]} ({user[2]})")
        
        # Check all available action menus
        print("\n\n📚 All available action menus:")
        menus_result = db.execute(text("""
            SELECT id, name, code FROM action_menus ORDER BY name
        """))
        menus = menus_result.fetchall()
        for menu in menus:
            print(f"  - ID: {menu[0]}, Name: {menu[1]}, Code: {menu[2]}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    check_role_permissions()
