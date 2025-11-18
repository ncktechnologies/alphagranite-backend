# Alpha Granite Backend

A production-grade FastAPI backend application for granite fabrication management with automated database migrations and Docker deployment.

## 🚀 Quick Deployment (Production)

### One-Command Deployment

```bash
git clone https://github.com/segunisreal/alpha-granit.git
cd alpha-granit
cp .env.example .env
# Edit .env with your production values
./deploy.sh
```

That's it! The application will:
- ✅ Automatically create/update database tables (Django-like migrations)
- ✅ Remove orphaned tables not in models
- ✅ Start all services with health checks
- ✅ Set up Nginx reverse proxy

**See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions**

## 🎯 Features

- **Auto Migrations**: Django-like migration system - no manual SQL needed
- **Production Ready**: Docker + Docker Compose with multi-stage builds
- **Security**: JWT authentication, CORS, rate limiting
- **Health Checks**: Automated service health monitoring
- **Scalable**: Nginx reverse proxy, 4 Uvicorn workers
- **Observable**: Comprehensive logging and request tracking

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

## 🛠️ Local Development

### Quick Start (Windows PowerShell)

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

4. **Run auto migration (creates/updates tables)**

```powershell
python scripts/auto_migrate.py
```

5. **Run the application**

```powershell
uvicorn src.app.main:app --reload
```

The API will be available at:
- Main API: http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Interactive API docs: http://localhost:8000/redoc

## 🐳 Docker Commands

```bash
# Start application
./manage.sh start

# View logs
./manage.sh logs

# Run migrations
./manage.sh migrate

# Database backup
./manage.sh backup

# Open shell in container
./manage.sh shell

# Check status
./manage.sh status

# See all commands
./manage.sh
```

## 📋 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/refresh` - Refresh token

### Health
- `GET /health` - System health check

### Business Operations
- Jobs, FABs, Employees, Departments, etc.
- See `/docs` for full API documentation
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