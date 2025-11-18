# Alpha Granite Backend

A production-grade FastAPI backend application for granite fabrication management with automated database migrations and Docker deployment.

## 🎯 Features

- **Auto Migrations**: Django-like migration system - no manual SQL needed
- **Production Ready**: Docker containerization with AWS RDS integration
- **Security**: JWT authentication, CORS protection, bcrypt password hashing
- **Health Checks**: Automated service health monitoring
- **Scalable**: 4 Uvicorn workers, async database operations
- **Observable**: Comprehensive logging and request tracking
- **FAB Workflow**: 10-stage fabrication workflow management

---

## 📋 Table of Contents

- [Quick Start - Local Development](#-local-development)
- [Production Deployment](#-production-deployment)
- [Available Commands](#-available-commands-makefile)
- [API Endpoints](#-api-endpoints)
- [Auto-Migration System](#-auto-migration-system)
- [Troubleshooting](#-troubleshooting)
- [Architecture](#-architecture)

---

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL (local or AWS RDS)

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/segunisreal/alpha-granit.git
cd alpha-granit
```

2. **Create virtual environment**
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

**Local .env configuration:**
```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=alpha_granite
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars
ADMIN_PASSWORD=your_admin_password

CORS_ORIGINS=http://localhost:3000
DEBUG=True
```

5. **Run auto-migration** (creates all database tables)
```bash
python scripts/auto_migrate.py
```

6. **Start the application**
```bash
uvicorn src.app.main:app --reload --port 8000
```

### Access Points (Local)

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Interactive Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🚀 Production Deployment

### Prerequisites

- Docker & Docker Compose installed on server
- **AWS RDS PostgreSQL** database created and accessible

### AWS RDS Setup

1. Create a PostgreSQL database on AWS RDS
2. Configure Security Group to allow inbound traffic on port 5432
3. Note down: endpoint, database name, username, password

### Deployment Steps

1. **Clone repository**
```bash
git clone https://github.com/segunisreal/alpha-granit.git
cd alpha-granit
```

2. **Configure environment**
```bash
cp .env.example .env
nano .env  # or vim .env
```

**Production .env configuration:**
```env
# AWS RDS Database
DATABASE_HOST=your-db.xxxxx.us-east-1.rds.amazonaws.com
DATABASE_PORT=5432
DATABASE_NAME=alpha_granite
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password

# Security (IMPORTANT: Use strong random keys)
SECRET_KEY=your-32-char-random-secret-key-here
JWT_SECRET_KEY=your-32-char-jwt-secret-key-here
ADMIN_PASSWORD=your_secure_admin_password

# CORS (Update with your frontend domain)
CORS_ORIGINS=https://yourfrontend.com,http://localhost:3000

# Application
APP_ENV=production
DEBUG=False
APP_PORT=8000
```

3. **Deploy**
```bash
make deploy
```

Or using the deploy script:
```bash
chmod +x deploy.sh
./deploy.sh
```

**That's it!** ✅ The application will:
- Build Docker images
- Connect to AWS RDS
- Run auto-migrations (create all tables)
- Start FastAPI with 4 workers
- Run health checks

### Verify Deployment

```bash
# Quick health check
make health

# Or manually
curl http://localhost:8000/health

# View logs
make logs
```

---

## 📋 Available Commands (Makefile)

```bash
make help       # Show all available commands
make build      # Build Docker images
make start      # Start services
make stop       # Stop services
make restart    # Restart services
make logs       # View application logs (follow mode)
make shell      # Open shell in container
make migrate    # Run database migrations
make status     # Show container status
make health     # Run health check
make clean      # Clean up containers and images
make deploy     # Full deployment (build and start)
```

---

## 🔄 Auto-Migration System

The Django-like migration system runs **automatically on startup**:

### What It Does

- ✅ **Creates missing tables** - New models automatically become tables
- ✅ **Removes orphaned tables** - Deleted models = tables dropped
- ✅ **Waits for database** - Ensures DB is ready before migrating
- ✅ **Comprehensive logging** - All changes are logged

### How It Works

```python
# Compares your SQLModel models with actual database
model_tables = get_model_tables()     # From code
db_tables = get_database_tables()     # From database

missing = model_tables - db_tables    # Creates these
extra = db_tables - model_tables      # Drops these
```

### Run Manually

```bash
# In Docker
make migrate

# Locally
python scripts/auto_migrate.py
```

### View Migration Logs

```bash
make logs | grep -i migration
```

---

## 🌐 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration  
- `POST /auth/refresh` - Refresh access token

### Health
- `GET /health` - System health check

### Core Business Operations
- **Jobs** - `/api/v1/jobs` - Business job management
- **FABs** - `/api/v1/fabs` - Fabrication workflow (10 stages)
- **Employees** - `/api/v1/employees` - Employee management
- **Departments** - `/api/v1/departments` - Department CRUD
- **Accounts** - `/api/v1/accounts` - Customer accounts
- **Files** - `/api/v1/files` - File upload/management

### Fabrication Resources
- **Stone Types** - `/api/v1/stone-types`
- **Stone Colors** - `/api/v1/stone-colors`
- **Stone Thickness** - `/api/v1/stone-thickness`
- **Edges** - `/api/v1/edges`

### Full Documentation
Visit `/docs` for complete interactive API documentation

---

## 🔧 Troubleshooting

### Container Issues

```bash
# Check logs
make logs

# Restart services
make restart

# Rebuild from scratch
make clean
make build
make start
```

### Migration Issues

```bash
# Run migrations manually
make migrate

# Check migration logs
make logs | grep -i migration
```

### AWS RDS Connection Issues

**Checklist:**
- [ ] RDS Security Group allows inbound on port 5432
- [ ] RDS endpoint is correct in `.env`
- [ ] Database name, user, password are correct
- [ ] RDS is publicly accessible (if connecting from outside VPC)
- [ ] Network connectivity (try `telnet endpoint 5432`)

**Test connection:**
```bash
# From local machine
psql -h your-endpoint.rds.amazonaws.com -U postgres -d alpha_granite

# From Docker container
make shell
python -c "from src.app.database import get_db; print('Connected!')"
```

### Application Won't Start

```bash
# Check all logs
make logs

# Check container status
make status

# Rebuild and restart
make build
make start
```

### Health Check Fails

```bash
# Run health check
make health

# Check if container is running
docker ps

# Check application logs
make logs
```

---

## 🏗️ Architecture

### Project Structure

```
alpha-granit/
├── src/app/
│   ├── main.py              # FastAPI application entry
│   ├── database/            # SQLModel models
│   │   ├── user.py
│   │   ├── fab.py
│   │   ├── business_job.py
│   │   └── ...
│   ├── routers/             # API endpoints
│   │   ├── auth.py
│   │   ├── fabs.py
│   │   ├── jobs.py
│   │   └── ...
│   ├── service/             # Business logic
│   │   ├── auth.py
│   │   ├── job_crud.py
│   │   └── ...
│   ├── interface/           # Request/Response schemas
│   └── utils/               # Config, helpers, constants
├── scripts/
│   └── auto_migrate.py      # Auto-migration system ⭐
├── tests/                   # Unit tests
├── static/                  # Uploads and static files
├── Dockerfile               # Production Docker image
├── docker-compose.yml       # Service orchestration
├── Makefile                 # Management commands
└── requirements.txt         # Python dependencies
```

### Layer Responsibilities

- **Database Layer**: SQLModel models, database connection
- **Router Layer**: API endpoints, request handling
- **Service Layer**: Business logic, CRUD operations
- **Interface Layer**: Pydantic schemas for validation
- **Utils Layer**: Configuration, helpers, constants

### Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (AWS RDS)
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Authentication**: JWT tokens, bcrypt
- **Container**: Docker
- **Server**: Uvicorn (4 workers)
- **Testing**: pytest, pytest-asyncio

---

## 📦 What Gets Deployed

### Docker Container
- FastAPI application (4 Uvicorn workers)
- Auto-migration system (runs on startup)
- Health monitoring endpoints
- Request logging middleware

### External Services
- **Database**: AWS RDS PostgreSQL (managed separately)
- **Reverse Proxy**: Nginx (configure separately if needed)

---

## 🔒 Security Notes

### Production Checklist

- [ ] Change all default passwords in `.env`
- [ ] Use strong random keys (32+ characters) for `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` with your actual frontend domain
- [ ] Set `DEBUG=False` in production
- [ ] Ensure AWS RDS security group is properly configured
- [ ] Enable SSL/HTTPS for production API
- [ ] Set up regular database backups
- [ ] Review and restrict user permissions

### Generate Secure Keys

```bash
# Generate random secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📚 Additional Documentation

- **DEPLOYMENT.md** - Comprehensive deployment guide
- **DEPLOYMENT_SUMMARY.md** - Feature overview and reference
- **/docs** - Interactive API documentation (when app is running)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

---

## 📝 License

This project is proprietary software for Alpha Granite.

---

## 🆘 Support

For issues or questions:
1. Check logs: `make logs`
2. Run health check: `make health`
3. Review this README and DEPLOYMENT.md
4. Check container status: `make status`

---

**Built with ❤️ for Alpha Granite**
