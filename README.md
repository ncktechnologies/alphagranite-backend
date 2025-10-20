# Alpha Granite Backend

A FastAPI backend application with proper service architecture following best practices.

## Architecture

The project follows a layered architecture pattern:

```
src/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── database/            # Database layer
│   │   ├── __init__.py      # Database exports
│   │   ├── connection.py    # Database connection and session management
│   │   └── models.py        # SQLModel database models
│   ├── interface/           # Interface layer
│   │   ├── __init__.py      # Interface exports
│   │   └── schemas.py       # Pydantic schemas for API requests/responses
│   ├── service/             # Service layer
│   │   ├── __init__.py      # Service exports
│   │   └── item_service.py  # Business logic for items
│   ├── routers/             # Router layer
│   │   ├── __init__.py      # Router exports
│   │   ├── health.py        # Health check endpoints
│   │   └── items.py         # Item CRUD endpoints
│   └── utils/               # Utilities layer
│       ├── __init__.py      # Utility exports
│       ├── config.py        # Configuration management
│       ├── constants.py     # Application constants
│       └── helpers.py       # Helper functions and exceptions
```

### Layer Responsibilities

- **Database Layer**: Database models, schemas, and connection management
- **Interface Layer**: API request/response schemas and data validation
- **Service Layer**: Business logic and domain operations
- **Router Layer**: API endpoints and HTTP handling
- **Utils Layer**: Configuration, constants, helpers, and common utilities

## Quick Start (Windows PowerShell)

1. **Create and activate virtual environment**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. **Install dependencies**

```powershell
pip install -r requirements.txt
```

3. **Set up environment variables**

```powershell
copy .env.example .env
# Edit .env to set your DATABASE_URL and other configurations
```

4. **Run the application**

```powershell
uvicorn src.app.main:app --reload
```

The API will be available at:
- Main API: http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Items API: http://localhost:8000/api/v1/items

## API Endpoints

### Health
- `GET /health` - Health check

### Items
- `GET /api/v1/items` - List items (with pagination)
- `POST /api/v1/items` - Create item
- `GET /api/v1/items/{id}` - Get item by ID
- `PUT /api/v1/items/{id}` - Update item
- `DELETE /api/v1/items/{id}` - Delete item

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/alpha_granite
DB_ECHO=true

# Application
APP_NAME=Alpha Granite Backend
APP_VERSION=1.0.0
DEBUG=false

# API
API_V1_PREFIX=/api/v1

# CORS
ALLOWED_ORIGINS=*

# Security (optional)
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
<!-- database upgrade command -->
alembic revision --autogenerate -m "Update user model"
alembic upgrade head