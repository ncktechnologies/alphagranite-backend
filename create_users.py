#!/usr/bin/env python3
"""
Script to create user/employee accounts in the database.
Run from project root: python create_users.py
"""

import asyncio
import bcrypt
from uuid import uuid4
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = "postgresql+asyncpg://admin:Admin%40Gr%40n1%2Be%21@93.114.128.181:5432/alpha_granite_staging"

# Users to create
USERS_DATA = [
    {
        "first_name": "Gustavo",
        "last_name": "Sandoval",
        "username": "gsandoval",
        "email": "chuks@carpediemts.com",
        "password": "Sandoval123!",
        "is_super_admin": True,
        "department": 1
    },
    {
        "first_name": "Luis",
        "last_name": "Becerril",
        "username": "lbecerril",
        "email": "chuks@carpediemts.com",
        "password": "Becerril123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Fernando",
        "last_name": "Valencia",
        "username": "fvalencia",
        "email": "chuks@carpediemts.com",
        "password": "Valencia123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Jasiel",
        "last_name": "Pena",
        "username": "jpena",
        "email": "chuks@carpediemts.com",
        "password": "Pena123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Victor",
        "last_name": "Juarez",
        "username": "vjuarez",
        "email": "chuks@carpediemts.com",
        "password": "Juarez123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Faustino",
        "last_name": "Velasco",
        "username": "fvelasco",
        "email": "chuks@carpediemts.com",
        "password": "Velasco123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Alejandro",
        "last_name": "Ramirez",
        "username": "aramirez",
        "email": "chuks@carpediemts.com",
        "password": "Ramirez123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Rufino",
        "last_name": "Marcelino",
        "username": "rmarcelino",
        "email": "chuks@carpediemts.com",
        "password": "Marcelino123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Virgilio",
        "last_name": "Denova",
        "username": "vdenova",
        "email": "chuks@carpediemts.com",
        "password": "Denova123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Jose",
        "last_name": "Corona",
        "username": "jcorona",
        "email": "chuks@carpediemts.com",
        "password": "Corona123!",
        "is_super_admin": False,
        "department": 1
    },
    {
        "first_name": "Juan",
        "last_name": "Zuniga",
        "username": "jzuniga",
        "email": "chuks@carpediemts.com",
        "password": "Zuniga123!",
        "is_super_admin": False,
        "department": 1
    },
]


def hash_password(password: str) -> str:
    """Hash password using bcrypt (same as in employee.py)"""
    password_bytes = password.encode('utf-8')[:72]
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
    return hashed_password


async def create_users():
    """Create users in the database"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            print("Starting user creation...")
            
            # Create users
            created_count = 0
            for user_data in USERS_DATA:
                username = user_data["username"]
                
                # Check if user already exists using raw SQL
                result = await session.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": username}
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    print(f"  ⚠️  User '{username}' already exists. Skipping...")
                    continue
                
                # Create user with raw SQL
                hashed_pwd = hash_password(user_data["password"])
                employee_id = str(uuid4())
                now = datetime.now()
                
                await session.execute(
                    text("""
                        INSERT INTO users 
                        (username, employee_id, email, first_name, last_name, password, 
                         is_super_admin, department, status, is_first_login, created_at, updated_at)
                        VALUES 
                        (:username, :employee_id, :email, :first_name, :last_name, :password,
                         :is_super_admin, :department, :status, :is_first_login, :created_at, :updated_at)
                    """),
                    {
                        "username": username,
                        "employee_id": employee_id,
                        "email": user_data["email"],
                        "first_name": user_data["first_name"],
                        "last_name": user_data["last_name"],
                        "password": hashed_pwd,
                        "is_super_admin": user_data["is_super_admin"],
                        "department": user_data["department"],
                        "status": 1,
                        "is_first_login": True,
                        "created_at": now,
                        "updated_at": now
                    }
                )
                
                print(f"  ✓ Created user: {user_data['first_name']} {user_data['last_name']} ({username})")
                created_count += 1
            
            await session.commit()
            print(f"\n✅ Successfully created {created_count} user(s)!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {str(e)}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_users())
