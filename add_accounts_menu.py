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

def add_accounts_action_menu():
    """Add 'accounts' action menu to the database"""
    
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
        # Check if accounts action menu already exists
        result = db.execute(text("""
            SELECT id, name, code FROM action_menus WHERE code = 'accounts'
        """))
        existing = result.fetchone()
        
        if existing:
            print(f"✅ 'accounts' action menu already exists (ID: {existing[0]})")
        else:
            # Add accounts action menu
            db.execute(text("""
                INSERT INTO action_menus (name, code, created_at, updated_at)
                VALUES ('Accounts', 'accounts', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """))
            db.commit()
            print(f"✅ Added 'Accounts' action menu")
        
        # Get the accounts menu ID
        result = db.execute(text("""
            SELECT id FROM action_menus WHERE code = 'accounts'
        """))
        menu = result.fetchone()
        menu_id = menu[0]
        
        # Get READ-only permission
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
            # Create READ-only permission
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
        
        # Add accounts READ permission to TEMPLATE SCHEDULER role
        role_result = db.execute(text("""
            SELECT id, name FROM roles WHERE name = 'TEMPLATE SCHEDULER'
        """))
        role = role_result.fetchone()
        
        if role:
            role_id = role[0]
            
            # Check if role already has this permission
            check_result = db.execute(text("""
                SELECT id FROM role_permissions 
                WHERE role_id = :role_id 
                AND action_menu_id = :menu_id
            """), {"role_id": role_id, "menu_id": menu_id})
            
            if check_result.fetchone():
                print(f"⚠️  TEMPLATE SCHEDULER already has accounts permission")
            else:
                # Add the permission
                db.execute(text("""
                    INSERT INTO role_permissions (role_id, action_menu_id, permission_id, created_at, updated_at)
                    VALUES (:role_id, :menu_id, :permission_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), {"role_id": role_id, "menu_id": menu_id, "permission_id": permission_id})
                db.commit()
                print(f"✅ Added 'accounts' READ permission to TEMPLATE SCHEDULER role")
        
        # Display all action menus
        print("\n📚 All action menus:")
        result = db.execute(text("""
            SELECT id, name, code FROM action_menus ORDER BY name
        """))
        menus = result.fetchall()
        for menu in menus:
            print(f"  - ID: {menu[0]}, Name: {menu[1]}, Code: {menu[2]}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    add_accounts_action_menu()
