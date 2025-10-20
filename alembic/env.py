import os
import sys
from alembic import context
from dotenv import load_dotenv
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool

# Load environment variables from .env
load_dotenv()

# Add project root to sys.path for model imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from sqlmodel import SQLModel
# Import all models for autogenerate support
from src.app.database.user import User
from src.app.database.role import Role
from src.app.database.file import File
from src.app.database.status import Status
from src.app.database.user_role import UserRole
from src.app.database.department import Department
from src.app.database.permission import Permission
from src.app.database.action_menu import ActionMenu
from src.app.database.audit_trail import AuditTrail
from src.app.database.role_permission import RolePermission

# Set target_metadata for 'autogenerate'
target_metadata = SQLModel.metadata

# Get database URL from environment or alembic.ini
DATABASE_URL = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

def run_migrations_offline():
    """
    Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """
    Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
