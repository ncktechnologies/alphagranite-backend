"""
Database Connection Test Script
Tests both sync and async database connections
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 70)
print("Database Connection Test")
print("=" * 70)
print(f"Raw DATABASE_URL from .env: {DATABASE_URL}")
print()

# Parse the URL to show components
if DATABASE_URL:
    parts = DATABASE_URL.split("://")
    if len(parts) == 2:
        protocol = parts[0]
        rest = parts[1]
        
        if "@" in rest:
            creds, host_db = rest.split("@", 1)
            if ":" in creds:
                user, password = creds.split(":", 1)
                print(f"Protocol: {protocol}")
                print(f"Username: {user}")
                print(f"Password: {'*' * len(password)} (hidden)")
                print(f"Host/DB: {host_db}")
            else:
                print(f"Full URL: {DATABASE_URL}")
        else:
            print(f"Full URL: {DATABASE_URL}")
    print()

# Test 1: Test sync connection with psycopg2
print("Test 1: Sync Connection (psycopg2)")
print("-" * 70)
try:
    from sqlalchemy import create_engine, text
    
    sync_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1) if DATABASE_URL.startswith("postgresql://") else DATABASE_URL
    print(f"Sync URL: {sync_url[:50]}...")
    
    engine = create_engine(sync_url, echo=False)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✓ Connection successful!")
        print(f"PostgreSQL version: {version[:100]}...")
    engine.dispose()
except Exception as e:
    print(f"✗ Connection failed: {e}")
print()

# Test 2: Test async connection with asyncpg
print("Test 2: Async Connection (asyncpg)")
print("-" * 70)
async def test_async():
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1) if DATABASE_URL.startswith("postgresql://") else DATABASE_URL
        print(f"Async URL: {async_url[:50]}...")
        
        engine = create_async_engine(
            async_url,
            echo=False,
            connect_args={"statement_cache_size": 0}
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ Connection successful!")
            print(f"PostgreSQL version: {version[:100]}...")
        
        await engine.dispose()
    except Exception as e:
        print(f"✗ Connection failed: {e}")

asyncio.run(test_async())
print()

# Test 3: Test raw asyncpg connection (bypass SQLAlchemy)
print("Test 3: Raw asyncpg Connection (no SQLAlchemy)")
print("-" * 70)
async def test_raw_asyncpg():
    try:
        import asyncpg
        
        # Parse DATABASE_URL
        if DATABASE_URL.startswith("postgresql://"):
            # Extract components
            url = DATABASE_URL.replace("postgresql://", "")
            if "@" in url:
                creds, host_db = url.split("@", 1)
                user, password = creds.split(":", 1)
                
                # Decode URL-encoded password
                from urllib.parse import unquote
                password = unquote(password)
                
                if "/" in host_db:
                    host_port, database = host_db.split("/", 1)
                else:
                    host_port = host_db
                    database = "postgres"
                
                if ":" in host_port:
                    host, port = host_port.split(":", 1)
                    port = int(port)
                else:
                    host = host_port
                    port = 5432
                
                print(f"Connecting to: {host}:{port}/{database}")
                print(f"User: {user}")
                
                conn = await asyncpg.connect(
                    user=user,
                    password=password,
                    database=database,
                    host=host,
                    port=port,
                    timeout=10
                )
                
                version = await conn.fetchval("SELECT version()")
                print(f"✓ Connection successful!")
                print(f"PostgreSQL version: {version[:100]}...")
                
                await conn.close()
        else:
            print("Not a PostgreSQL URL")
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_raw_asyncpg())
print()

print("=" * 70)
print("Test Complete")
print("=" * 70)
