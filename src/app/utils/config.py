import os
import pathlib
from datetime import date, datetime, time
from dotenv import load_dotenv
from functools import lru_cache
from typing import AsyncGenerator
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from src.app.utils.helpers import APP_TIMEZONE_NAME, to_app_tz

load_dotenv()


def _use_app_timezone_for_datetimes() -> None:
    """Treat every datetime column as America/Chicago wall-clock time.

    The columns are `timestamp without time zone`. Writes are sent as
    timestamptz and Postgres stores them in the session TimeZone (pinned to
    America/Chicago on the engine below); reads come back naive and are
    labelled America/Chicago. Naive input is assumed to already be Chicago time.
    A plain date compared with one of these columns is taken as midnight that
    day, the same as Postgres does when it compares a date with a timestamp.
    """
    try:
        from sqlmodel.sql.sqltypes import UTCDateTime
    except ImportError:
        return

    def process_bind_param(self, value, dialect):
        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime.combine(value, time.min)
        return to_app_tz(value)

    def process_result_value(self, value, dialect):
        return to_app_tz(value)

    UTCDateTime.process_bind_param = process_bind_param
    UTCDateTime.process_result_value = process_result_value


_use_app_timezone_for_datetimes()

# Base directory for the project
BASE_DIR = pathlib.Path(__file__).parent.parent.parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please configure your database connection.")

# Convert to async driver for the application
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
elif DATABASE_URL.startswith('postgresql+psycopg2://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql+psycopg2://', 'postgresql+asyncpg://', 1)

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
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx,glb").split(",")

# API base URL for generating file URLs
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Support Email Configuration
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "odyssey@alphagraniteaustin.com")

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
# Configure engine with statement_cache_size=0 for pgBouncer compatibility.
# The session TimeZone is pinned so stored/returned timestamps are always
# America/Chicago, regardless of the Postgres server's own timezone setting.
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "statement_cache_size": 0,
        "server_settings": {"timezone": APP_TIMEZONE_NAME},
    } if "postgresql" in DATABASE_URL else {}
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