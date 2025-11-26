"""
Auto Migration Script - Django-like migration system
Automatically creates, updates, and removes database tables based on SQLModel models
Runs on application startup to ensure database schema is in sync
"""

import sys
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables BEFORE any other imports
load_dotenv()

# Set flag to prevent async engine creation during migration
os.environ["SKIP_ASYNC_ENGINE"] = "1"

from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import logging

# Get DATABASE_URL directly from environment to avoid importing config.py
# (which would trigger async engine creation)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please configure your database connection in the .env file."
    )

# Convert async driver to sync driver for migration operations
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

# Import all models to ensure they're registered with SQLModel
# Import directly from model files (not from __init__.py which imports config)
from src.app.database.user import User
from src.app.database.role import Role
from src.app.database.permission import Permission
from src.app.database.role_permission import RolePermission
from src.app.database.department import Department
from src.app.database.status import Status
from src.app.database.action_menu import ActionMenu
from src.app.database.audit_trail import AuditTrail
from src.app.database.account import Account
from src.app.database.business_job import BusinessJob
from src.app.database.job import Job
from src.app.database.fab import Fab
from src.app.database.edge import Edge
from src.app.database.stone_type import StoneType
from src.app.database.stone_color import StoneColor
from src.app.database.stone_thickness import StoneThickness
from src.app.database.file import File
from src.app.database.shop_planning import ShopPlanning
from src.app.database.planning_section import PlanningSection
from src.app.database.shop_planning_section import ShopPlanningSection
from src.app.database.operation_workflow import OperationWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_model_tables():
    """Get all table names from SQLModel models"""
    model_tables = set()
    for table in SQLModel.metadata.tables.values():
        model_tables.add(table.name)
    return model_tables


def get_database_tables(engine):
    """Get all existing table names from database"""
    inspector = inspect(engine)
    return set(inspector.get_table_names())


def drop_extra_tables(engine, extra_tables):
    """Drop tables that exist in database but not in models"""
    if not extra_tables:
        logger.info("✓ No extra tables to drop")
        return
    
    logger.warning(f"Found {len(extra_tables)} extra table(s) to drop: {', '.join(extra_tables)}")
    
    with engine.connect() as conn:
        for table_name in extra_tables:
            try:
                # Drop table with CASCADE to handle dependencies
                conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
                conn.commit()
                logger.info(f"✓ Dropped table: {table_name}")
            except Exception as e:
                logger.error(f"✗ Error dropping table {table_name}: {e}")
                conn.rollback()


def create_missing_tables(engine, missing_tables):
    """Create tables that exist in models but not in database"""
    if not missing_tables:
        logger.info("✓ No missing tables to create")
        return
    
    logger.info(f"Found {len(missing_tables)} missing table(s): {', '.join(missing_tables)}")
    
    # Create all tables (SQLModel will only create missing ones)
    try:
        SQLModel.metadata.create_all(engine)
        logger.info(f"✓ Created missing tables")
    except Exception as e:
        logger.error(f"✗ Error creating tables: {e}")
        raise


def sync_database_schema():
    """Main function to synchronize database schema with models"""
    logger.info("=" * 70)
    logger.info("Starting Auto Migration (Django-like)")
    logger.info("=" * 70)
    
    try:
        # Create synchronous engine for schema operations
        engine = create_engine(DATABASE_URL, echo=False)
        
        logger.info(f"Connected to database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'local'}")
        
        # Get model and database tables
        model_tables = get_model_tables()
        db_tables = get_database_tables(engine)
        
        logger.info(f"Models define {len(model_tables)} table(s)")
        logger.info(f"Database has {len(db_tables)} existing table(s)")
        
        # Calculate differences
        missing_tables = model_tables - db_tables
        extra_tables = db_tables - model_tables
        common_tables = model_tables & db_tables
        
        logger.info(f"Common tables: {len(common_tables)}")
        logger.info(f"Missing tables (to create): {len(missing_tables)}")
        logger.info(f"Extra tables (to drop): {len(extra_tables)}")
        
        # Drop extra tables first
        if extra_tables:
            logger.warning("⚠ Dropping extra tables...")
            drop_extra_tables(engine, extra_tables)
        
        # Create missing tables
        if missing_tables:
            logger.info("Creating missing tables...")
            create_missing_tables(engine, missing_tables)
        
        # Verify final state
        final_db_tables = get_database_tables(engine)
        logger.info(f"Final database table count: {len(final_db_tables)}")
        
        engine.dispose()
        
        logger.info("=" * 70)
        logger.info("✓ Auto Migration Completed Successfully")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"✗ Auto Migration Failed: {e}")
        logger.error("=" * 70)
        raise


def verify_database_connection():
    """Verify database connection before migration"""
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        logger.info("✓ Database connection verified")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def wait_for_database(max_retries=30, delay=2):
    """Wait for database to be ready"""
    logger.info("Waiting for database to be ready...")
    for i in range(max_retries):
        if verify_database_connection():
            return True
        logger.info(f"Attempt {i + 1}/{max_retries} - Database not ready, waiting {delay}s...")
        time.sleep(delay)
    
    logger.error("Database did not become ready in time")
    return False


def main():
    """Main entry point"""
    try:
        # Wait for database to be ready (important for Docker)
        if not wait_for_database():
            sys.exit(1)
        
        # Run synchronous schema sync
        sync_database_schema()
        
        logger.info("Database is ready for application startup")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
