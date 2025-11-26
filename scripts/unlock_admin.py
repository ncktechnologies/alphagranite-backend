#!/usr/bin/env python3
"""Unlock the admin account"""

import asyncio
import sys
import os

# Add the src directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

# Database URL
DATABASE_URL = "postgresql+asyncpg://admin:Admin%40Gr%40n1%2Be%21@93.114.128.181:5432/alpha_granite"

async def unlock_admin():
    """Unlock the admin account"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        result = await conn.execute(
            text("UPDATE users SET is_locked = FALSE, failed_login_attempts = 0 WHERE username = :username"),
            {"username": "admin"}
        )
        print(f"✅ Unlocked admin account ({result.rowcount} rows)")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(unlock_admin())
