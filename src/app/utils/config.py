import os
import pathlib
from dotenv import load_dotenv
from functools import lru_cache
from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

load_dotenv()

# Base directory for the project
BASE_DIR = pathlib.Path(__file__).parent.parent.parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")


# Superuser credentials
SUPERUSER_USERNAME = os.getenv("SUPERUSER_USERNAME", "admin")
SUPERUSER_EMAIL = os.getenv("SUPERUSER_EMAIL", "admin@example.com")
SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "admin123")
SUPERUSER_FIRST_NAME = os.getenv("SUPERUSER_FIRST_NAME", "Super")
SUPERUSER_LAST_NAME = os.getenv("SUPERUSER_LAST_NAME", "Admin")

# File upload configuration
STATIC_DIR = os.getenv("STATIC_DIR", os.path.join(BASE_DIR, "static"))
UPLOADS_DIR = os.getenv("UPLOADS_DIR", os.path.join(STATIC_DIR, "uploads"))
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 5 * 1024 * 1024))  # 5 MB default
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx").split(",")

# API base URL for generating file URLs
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

class Settings(BaseSettings):
    """Application settings."""
    STATIC_DIR: str = STATIC_DIR
    UPLOADS_DIR: str = UPLOADS_DIR
    MAX_UPLOAD_SIZE: int = MAX_UPLOAD_SIZE
    API_BASE_URL: str = API_BASE_URL
    
    @property
    def ALLOWED_EXTENSIONS(self):
        return ALLOWED_EXTENSIONS

@lru_cache
def get_settings():
    """Get application settings."""
    return Settings()

# Ensure directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Database connection
# Configure engine with statement_cache_size=0 for pgBouncer compatibility
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"statement_cache_size": 0} if "postgresql" in DATABASE_URL else {}
)
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