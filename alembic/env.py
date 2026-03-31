import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv 
from sqlalchemy import engine_from_config

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env
load_dotenv()

# Import SQLModel for SQLModel.metadata
from sqlmodel import SQLModel

# Import your models to register them with SQLModel.metadata
from src.app.database.user import User
from src.app.database.file import File
from src.app.database.role import Role
from src.app.database.status import Status
from src.app.database.user_role import UserRole
from src.app.database.user_role import UserRole
from src.app.database.department import Department
from src.app.database.permission import Permission
from src.app.database.audit_trail import AuditTrail
# Import other models so SQLModel.metadata includes them for autogenerate
from src.app.database.action_menu import ActionMenu
from src.app.database.role_permission import RolePermission
# Import business models from generated schemas to avoid duplicates
from src.app.interface.generated_schemas import (
    # PlanningSection, WorkStation,
     Templating, SlabSmith, ShopPlanning, 
)
# Import any additional models here as needed

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


# Get DATABASE_URL from environment variable and force psycopg2 for migrations
database_url = os.environ.get("DATABASE_URL")
if database_url is None:
    raise Exception("DATABASE_URL environment variable is not set")

# Convert async driver to sync driver for migrations
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")

# Escape % characters for configparser by doubling them
# This is needed because configparser treats % as interpolation character
escaped_url = database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", escaped_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set up target metadata for autogenerate support
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
