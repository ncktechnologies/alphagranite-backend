"""
Script to create all tables from SQLModel models in the database.
Run this once to initialize your database tables.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlmodel import SQLModel
from sqlmodel import create_engine
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

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:password@localhost:5432/alpha_granite"
)
engine = create_engine(DATABASE_URL, echo=True)

if __name__ == "__main__":
    SQLModel.metadata.create_all(engine)
    print("All tables created.")
