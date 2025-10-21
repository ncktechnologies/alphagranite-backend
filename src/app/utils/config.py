import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")

# Superuser credentials
SUPERUSER_USERNAME = os.getenv("SUPERUSER_USERNAME", "admin")
SUPERUSER_EMAIL = os.getenv("SUPERUSER_EMAIL", "admin@example.com")
SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "admin123")
SUPERUSER_FIRST_NAME = os.getenv("SUPERUSER_FIRST_NAME", "Super")
SUPERUSER_LAST_NAME = os.getenv("SUPERUSER_LAST_NAME", "Admin")