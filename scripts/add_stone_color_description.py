import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set in environment or .env")

print("Connecting to DB:", DATABASE_URL)
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()
try:
    cur.execute("ALTER TABLE stone_colors ADD COLUMN IF NOT EXISTS description TEXT;")
    print("ALTER TABLE executed (column ensured)")
finally:
    cur.close()
    conn.close()
