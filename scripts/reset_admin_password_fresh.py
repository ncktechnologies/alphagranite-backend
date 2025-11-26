#!/usr/bin/env python3
"""Reset admin password with fresh hash"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
from passlib.context import CryptContext

# Database URL
DATABASE_URL = "postgresql+asyncpg://admin:Admin%40Gr%40n1%2Be%21@93.114.128.181:5432/alpha_granite"

async def reset_admin():
    """Reset admin password"""
    # Generate new hash
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password = "admin123@Daewi1"
    hashed = pwd_context.hash(password)
    
    print(f"New hash: {hashed}")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""UPDATE users 
                   SET password = :password_hash, 
                       is_locked = FALSE, 
                       failed_login_attempts = 0,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE username = :username"""),
            {"username": "admin", "password_hash": hashed}
        )
        print(f"✅ Reset admin password ({result.rowcount} rows)")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_admin())
