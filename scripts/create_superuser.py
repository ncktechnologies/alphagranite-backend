#!/usr/bin/env python3
"""
Create a superuser for local development / tests.
This script uses the project's async SessionLocal so it works with
async drivers like aiosqlite or asyncpg.

It will also seed minimal lookup rows required by the User model
( Status with value_id=1 and Department with id=1 ).
"""
import os
import sys
import bcrypt
import asyncio
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select
from dotenv import load_dotenv

# Ensure project root is on path so imports from `src` work when running this script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

# Load env vars
load_dotenv()

# Import models (some modules only register mappers on import)
# Import order can matter; import dependent modules early to register mappers.
try:
    import src.app.database.role  # noqa: F401
    import src.app.database.status  # noqa: F401
    import src.app.database.user_role  # noqa: F401
    import src.app.database.department  # noqa: F401
    import src.app.database.job  # noqa: F401 - Import JobApplication before User
except Exception:
    # We'll still import specific classes below and let errors propagate with clearer messages
    pass

from src.app.database.user import User
from src.app.database.status import Status
from src.app.database.department import Department


def _env_default(name: str, default: str) -> str:
    return os.getenv(name, default)

USERNAME = _env_default("SUPERUSER_USERNAME", "admin")
EMAIL = _env_default("SUPERUSER_EMAIL", "admin@example.com")
PASSWORD = _env_default("SUPERUSER_PASSWORD", "admin123@Daewi1")
FIRST_NAME = _env_default("SUPERUSER_FIRST_NAME", "Super")
LAST_NAME = _env_default("SUPERUSER_LAST_NAME", "Admin")


async def _create_superuser_async():
    # Import SessionLocal lazily so config loads with env vars applied
    from src.app.utils.config import SessionLocal, DATABASE_URL

    print(f"Using DATABASE_URL: {DATABASE_URL}")

    async with SessionLocal() as db:  # type: ignore
        # Seed Status with value_id=1 if missing
        try:
            res = await db.execute(select(Status).where(Status.value_id == 1))
            status_row = res.scalars().first()
            if not status_row:
                status_row = Status(name="Active", slug="active", value_id=1)
                db.add(status_row)
                await db.commit()
                await db.refresh(status_row)
                print("Seeded status row with value_id=1.")
        except Exception as e:
            await db.rollback()
            print("Error while ensuring status row:", e)
            raise

        # Seed Department with id=1 if missing
        try:
            res = await db.execute(select(Department).where(Department.id == 1))
            dept_row = res.scalars().first()
            if not dept_row:
                dept_row = Department(id=1, name="Default", description="Default department", status=1)
                db.add(dept_row)
                await db.commit()
                await db.refresh(dept_row)
                print("Seeded department row with id=1.")
        except Exception as e:
            await db.rollback()
            print("Error while ensuring department row:", e)
            raise

        # Check if user exists
        try:
            res = await db.execute(select(User).where((User.username == USERNAME) | (User.email == EMAIL)))
            existing_user = res.scalars().first()
            if existing_user:
                print(f"Superuser with username '{USERNAME}' or email '{EMAIL}' already exists (id={existing_user.id})")
                return
        except Exception as e:
            print("Error while querying existing user:", e)
            raise

        # Hash password using passlib CryptContext to match app logic
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt_sha256"], deprecated="auto")
            hashed_password = pwd_context.hash(PASSWORD)
        except Exception as e:
            print("Error hashing password:", e)
            raise

        # Create user
        try:
            user = User(
                username=USERNAME,
                email=EMAIL,
                password=hashed_password,
                employee_id=uuid4(),
                first_name=FIRST_NAME,
                last_name=LAST_NAME,
                department=1,
                status=1,
                is_super_admin=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                role_id=None,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print("Superuser created successfully:")
            print(f"  Username: {USERNAME}")
            print(f"  Email: {EMAIL}")
            print(f"  ID: {user.id}")
        except Exception as e:
            await db.rollback()
            print("Error creating superuser:", e)
            raise


def main():
    try:
        asyncio.run(_create_superuser_async())
    except Exception as e:
        print("create_superuser failed:", e)
        raise


if __name__ == "__main__":
    main()