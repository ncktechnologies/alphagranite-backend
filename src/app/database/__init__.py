"""
Expose the async DB dependency and session factory.

This module previously created a synchronous engine and session factory
which caused conflicts when the application used async drivers (aiosqlite
or asyncpg). To prepare the codebase for an async migration we now
re-export the async engine/session/get_db that live in
`src.app.utils.config` so other modules importing `from src.app.database
import get_db` receive the async dependency.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from src.app.utils.config import get_db as get_db_async, engine as engine_async, SessionLocal as AsyncSessionLocal

# Re-export commonly used symbols under the old package
get_db = get_db_async
engine = engine_async
SessionLocal = AsyncSessionLocal
Base = declarative_base()

__all__ = ["get_db", "engine", "SessionLocal", "Base", "AsyncSession"]