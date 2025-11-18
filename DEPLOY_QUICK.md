# 🚀 QUICK DEPLOYMENT GUIDE

## Prerequisites

- Docker & Docker Compose installed
- AWS RDS PostgreSQL database created

## Step 1: Clone Repository

```bash
git clone https://github.com/segunisreal/alpha-granit.git
cd alpha-granit
```

## Step 2: Configure Environment

```bash
cp .env.example .env
nano .env  # or vim .env
```

### Required Configuration:

**AWS RDS Database:**

```env
DATABASE_HOST=your-rds-endpoint.xxxxx.us-east-1.rds.amazonaws.com
DATABASE_PORT=5432
DATABASE_NAME=alpha_granite
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password
```

**Security:**

```env
SECRET_KEY=your-32-char-random-secret-key
JWT_SECRET_KEY=your-32-char-jwt-secret-key
ADMIN_PASSWORD=your_secure_admin_password
```

**CORS:**

```env
CORS_ORIGINS=https://yourfrontend.com,http://localhost:3000
```

## Step 3: Deploy

```bash
make deploy
```

Or use the deployment script:

```bash
./deploy.sh
```

---

## 📋 Available Commands (Makefile)

```bash
make help       # Show all available commands
make build      # Build Docker images
make start      # Start services
make stop       # Stop services
make restart    # Restart services
make logs       # View application logs
make shell      # Open shell in container
make migrate    # Run database migrations
make status     # Show container status
make health     # Run health check
make clean      # Clean up containers
```

---

## ✅ Verify Deployment

```bash
# Quick health check
make health

# Or manually
curl http://localhost:8000/health

# View logs
make logs
```

---

## 🔄 Auto-Migration

The Django-like migration system runs automatically on startup:

- ✅ Creates missing tables from models
- ✅ Removes orphaned tables
- ✅ Waits for AWS RDS to be ready
- ✅ Comprehensive logging

To run migrations manually:

```bash
make migrate
```

---

## 📦 What Gets Deployed

- **FastAPI Application** (4 Uvicorn workers)
- **Auto-migration system** (runs on startup)
- **Health monitoring**
- **Request logging**

**Database:** Connects to your AWS RDS PostgreSQL instance

---

## 🌐 Access Points

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🔧 Troubleshooting

**Container won't start:**

```bash
make logs
make restart
```

**Migration fails:**

```bash
make migrate
```

**RDS connection issues:**

- Verify security group allows inbound traffic on port 5432
- Check RDS endpoint is correct in `.env`
- Ensure database user has proper permissions

---

## 📚 Full Documentation

- **DEPLOYMENT.md** - Complete deployment guide
- **README.md** - Development setup
- See documentation for SSL, monitoring, backups, etc.

---

## 🚨 Important Notes

1. **AWS RDS Setup:**

   - Create PostgreSQL database on AWS RDS
   - Configure security group to allow access
   - Note the endpoint, username, and password

2. **Environment Variables:**

   - Never commit `.env` to git
   - Update all passwords and secrets
   - Configure CORS for your frontend domain

3. **Auto-Migration:**
   - Runs automatically on every startup
   - Safe to run multiple times
   - Check logs with `make logs`

---

## 🎉 That's It!

Your application is now running with:

- ✅ Docker containerization
- ✅ AWS RDS database connection
- ✅ Auto-migrations on startup
- ✅ Production-ready configuration

Use `make help` to see all available commands.
