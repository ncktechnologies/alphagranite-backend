import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

def update_admin_password():
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
        # Update admin password to the new bcrypt hash
        new_password_hash = "$2b$12$49dnM2LEXnhmArPR/Me9Du/oMJbxFu2Ge8PTo81yA74tNl8EBORJy"
        
        result = db.execute(text("""
            UPDATE users 
            SET password = :password_hash, updated_at = CURRENT_TIMESTAMP
            WHERE username = 'admin'
        """), {"password_hash": new_password_hash})
        
        if result.rowcount > 0:
            db.commit()
            print(f"Updated admin password successfully ({result.rowcount} rows affected)")
        else:
            print("No admin user found to update")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating admin password: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    update_admin_password()