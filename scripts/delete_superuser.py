import os
import sys
import asyncio
from dotenv import load_dotenv
from sqlalchemy import delete

# Setup project root and sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

load_dotenv()

from src.app.utils.config import SessionLocal
try:
    import src.app.database.role  # noqa: F401
    import src.app.database.status  # noqa: F401
    import src.app.database.user_role  # noqa: F401
    import src.app.database.department  # noqa: F401
except Exception:
    pass
from src.app.database.user import User

USERNAME = os.getenv("SUPERUSER_USERNAME", "admin")
EMAIL = os.getenv("SUPERUSER_EMAIL", "admin@example.com")

async def delete_superuser():
    async with SessionLocal() as db:
        await db.execute(delete(User).where((User.username == USERNAME) | (User.email == EMAIL)))
        await db.commit()
        print("Superuser deleted if existed.")

if __name__ == "__main__":
    asyncio.run(delete_superuser())
