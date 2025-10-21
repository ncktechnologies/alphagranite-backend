import sys
import jwt
import uuid
import pytest
import asyncio
from pathlib import Path
from httpx import AsyncClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSessionte_async_engine, AsyncSession

# Ensure project root is on sys.path so tests can import the 'src' package
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app.main import app
from src.app.database.user import User
from src.app.utils.config import get_db
from src.app.database.department import Departmentment


# Use in-memory SQLite database for tests
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create engine and session for testing
test_engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession,
)


# Override the get_db dependency to use our test database
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


# Setup test client with our test database
app.dependency_overrides[get_db] = override_get_db
test_client = TestClient(app)


@pytest.fixture
async def test_db():
    # Create tables
    from src.app.database.user import User
    from src.app.database.status import Status
    from src.app.database.department import Department    
    
    async with test_engine.begin() as conn:
        # Drop and recreate all tables for each test
        await conn.run_sync(User.metadata.drop_all)
        await conn.run_sync(Department.metadata.drop_all)
        await conn.run_sync(Status.metadata.drop_all)
        
        await conn.run_sync(Status.metadata.create_all)
        await conn.run_sync(Department.metadata.create_all)
        await conn.run_sync(User.metadata.create_all)
    
    # Create initial data
    async with TestingSessionLocal() as session:
        # Create status values
        status_values = [
            Status(id=1, name="Active", slug="active", value_id=1),
            Status(id=2, name="Inactive", slug="inactive", value_id=2),
            Status(id=3, name="Deleted", slug="deleted", value_id=3)
        ]
        for status in status_values:
            session.add(status)
        
        # Create a default department
        default_department = Department(
            id=1,
            name="Default Department",
            description="Default department for testing",
            status=1  # Active
        )
        session.add(default_department)
        
        # Create a test admin user
        test_user = User(
            username="testadmin",
            employee_id=uuid.uuid4(),
            email="testadmin@example.com",
            first_name="Test",
            last_name="Admin",
            department=1,
            password="$2b$12$Vh6vhhhSB4nTWQS9h5xcEudxKG8pmH9VBl1mT3kV.N1I1TLEYgOVy",  # hashed 'password123'
            is_super_admin=True,
            status=1  # Active
        )
        session.add(test_user)
        
        await session.commit()
    
    yield session
    
    # Clean up after the test
    async with test_engine.begin() as conn:
        await conn.run_sync(User.metadata.drop_all)
        await conn.run_sync(Department.metadata.drop_all)
        await conn.run_sync(Status.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_department(test_db):
    """Create a test department"""
    async with TestingSessionLocal() as session:
        department = Department(
            name=f"Test Department {uuid.uuid4()}",
            description="Department for testing",
            status=1  # Active
        )
        session.add(department)
        await session.commit()
        await session.refresh(department)
        
        yield department


async def get_test_token_header(client):
    """Helper function to get an authentication token"""
    login_data = {
        "username": "testadmin@example.com",
        "password": "password123"
    }
    
    # If we don't have a working login endpoint, we'll create a token manually
    secret_key = "testsecretkey"
    token_data = {
        "sub": "testadmin@example.com",
        "id": 1,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "is_super_admin": True
    }
    token = jwt.encode(token_data, secret_key, algorithm="HS256")
    
    return {"Authorization": f"Bearer {token}"}


# Fix event loop issues
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
