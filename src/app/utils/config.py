import os
from dotenv import load_dotenv
from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, create_async_engine

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# If using PostgreSQL, convert to async driver
if DATABASE_URL.startswith('postgresql:'):
    DATABASE_URL = DATABASE_URL.replace('postgresql:', 'postgresql+asyncpg:')

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")

# Superuser credentials
SUPERUSER_USERNAME = os.getenv("SUPERUSER_USERNAME", "admin")
SUPERUSER_EMAIL = os.getenv("SUPERUSER_EMAIL", "admin@example.com")
SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "admin123")
SUPERUSER_FIRST_NAME = os.getenv("SUPERUSER_FIRST_NAME", "Super")
SUPERUSER_LAST_NAME = os.getenv("SUPERUSER_LAST_NAME", "Admin")

# Database connection
engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields a SQLAlchemy async session
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise