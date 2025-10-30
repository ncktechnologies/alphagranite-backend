import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

load_dotenv()

def get_sync_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    return database_url


def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set")
        return

    sync_url = get_sync_url(database_url)
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        username = os.getenv("SUPERUSER_USERNAME", "admin")
        # Get superuser
        res = db.execute(text("SELECT id, username, email, is_super_admin, role_id FROM users WHERE username = :username"), {"username": username})
        user = res.fetchone()
        print("Superuser row:")
        print(user)

        # List action menus
        res = db.execute(text("SELECT id, name, code FROM action_menus ORDER BY id"))
        menus = res.fetchall()
        print("\nAction menus (count={}):".format(len(menus)))
        for m in menus:
            print(m)

    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == '__main__':
    main()
