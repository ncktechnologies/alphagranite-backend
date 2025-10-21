import os
import sys
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.app.database.user import User

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_superuser():
    # Get credentials from environment
    username = os.getenv("SUPERUSER_USERNAME", "admin")
    email = os.getenv("SUPERUSER_EMAIL", "admin@example.com")
    password = os.getenv("SUPERUSER_PASSWORD", "admin123")
    first_name = os.getenv("SUPERUSER_FIRST_NAME", "Super")
    last_name = os.getenv("SUPERUSER_LAST_NAME", "Admin")
    
    # Database connection
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found in environment variables")
        return
    
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if superuser already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"Superuser with username '{username}' or email '{email}' already exists")
            return
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create superuser
        superuser = User(
            username=username,
            email=email,
            password=hashed_password,
            employee_id=uuid4(),
            first_name=first_name,
            last_name=last_name,
            department=1,  # Default department
            status=1,      # Active status
            is_super_admin=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(superuser)
        db.commit()
        db.refresh(superuser)
        
        print(f"Superuser created successfully:")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"ID: {superuser.id}")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating superuser: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_superuser()