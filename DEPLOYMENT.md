# Alpha Granite Backend - Docker Deployment Guide

## 🚀 Quick Start Deployment

### Prerequisites

- Docker installed on your server
- Docker Compose installed
- Git installed

### Deployment Steps

1. **Clone or pull the repository:**

   ```bash
   git clone https://github.com/segunisreal/alpha-granit.git
   cd alpha-granit
   # OR if already cloned:
   git pull origin job
   ```

2. **Create/Update .env file:**

   ```bash
   cp .env.example .env
   nano .env  # or vim .env
   ```

   Update these critical values:

   - `DATABASE_PASSWORD` - Strong database password
   - `SECRET_KEY` - Random 32+ character string
   - `JWT_SECRET_KEY` - Random 32+ character string
   - `ADMIN_PASSWORD` - Secure admin password
   - `CORS_ORIGINS` - Your frontend domain

3. **Run deployment script:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

That's it! The application will:

- ✅ Automatically create/update database tables
- ✅ Remove tables not in models
- ✅ Start all services
- ✅ Run health checks

## 📋 Manual Deployment

If you prefer manual control:

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Stop
docker-compose down

# Restart
docker-compose restart web
```

> The stack includes `redis`, `celery_worker` and `celery_beat`. Any change to
> `requirements.txt` (Celery was added there) requires `--build`, not just a restart.

## ⏱️ Background Jobs (Celery + Redis)

Scheduled data pulls (currently the HCP payroll/staff-roster ingestion) run through
Celery rather than inside the API process.

| Service | Role |
| --- | --- |
| `redis` | Broker + result backend, appendonly persistence on the `redis_data` volume |
| `celery_worker` | Executes tasks (`--concurrency=2`) |
| `celery_beat` | Ticks every minute and dispatches whatever is due |

Beat runs `hcp_payroll.dispatch_due_ingestions` every minute. That task reads the
active rows in `hcp_payroll_source_configs` and queues `hcp_payroll.ingest_config`
only for configs whose `schedule_*` columns match the current time, so schedules are
edited through the API and never hardcoded in beat.

```bash
# Worker / beat logs
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# Inspect the queue
docker-compose exec celery_worker celery -A src.app.tasks.celery_app.celery_app inspect active

# Fire an ingestion by hand (config id 1)
docker-compose exec celery_worker \
  celery -A src.app.tasks.celery_app.celery_app call hcp_payroll.ingest_config --args='[1]'
```

**Run exactly one `celery_beat` container.** There is no distributed lock, so a
second replica would duplicate every pull.

### HCP ingestion endpoints

All admin-only, under `/api/v1/hcp-payroll`:

| Route | Purpose |
| --- | --- |
| `POST /settings` | Create a config (one per saved report) |
| `POST /settings/{id}/test` | Dry run — fetches and parses, persists nothing |
| `POST /settings/{id}/ingest` | Real pull — writes run + snapshot + rows |
| `GET /runs?setting_id=` | Run history with HTTP status and errors |
| `GET /staff-roster/latest` | Newest roster snapshot plus active employee count |

After deploying, verify connectivity with `/settings/{id}/test` before enabling the
schedule.

## 🔄 Auto Migration System

The Django-like migration system runs automatically on startup:

### What it does:

1. **Creates missing tables** - Any new models are automatically created
2. **Removes orphaned tables** - Tables not in models are dropped
3. **Waits for database** - Ensures PostgreSQL is ready before starting
4. **Logs everything** - Detailed migration logs for debugging

### Migration Script: `scripts/auto_migrate.py`

This runs before the application starts every time.

### Manual Migration:

```bash
# Run migration manually
docker-compose exec web python scripts/auto_migrate.py

# Or from host
python scripts/auto_migrate.py
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Nginx (Port 80/443)           │
│         (Reverse Proxy + SSL)           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      FastAPI App (Port 8000)            │
│    - Auto Migration on Startup          │
│    - 4 Uvicorn Workers                  │
│    - Health Checks                      │
└──────────────┬──────────────────────────┘
               │
               ├──────────────┐
               │              ▼
               │   ┌─────────────────────────────┐
               │   │   Redis (Port 6379)         │
               │   │   - Celery broker/backend   │
               │   └──────────┬──────────────────┘
               │              │
               │              ▼
               │   ┌─────────────────────────────┐
               │   │  celery_worker + celery_beat│
               │   │  - Scheduled HCP pulls      │
               │   └──────────┬──────────────────┘
               │              │
               ▼              ▼
┌─────────────────────────────────────────┐
│    PostgreSQL 15 (Port 5432)            │
│    - Persistent Volume                  │
│    - Health Checks                      │
└─────────────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables (.env)

**Required:**

- `DATABASE_PASSWORD` - PostgreSQL password
- `SECRET_KEY` - Application secret key
- `JWT_SECRET_KEY` - JWT token secret
- `ADMIN_PASSWORD` - Initial admin password

**Optional:**

- `APP_PORT` - API port (default: 8000)
- `DATABASE_HOST` - DB host (default: db)
- `CORS_ORIGINS` - Allowed origins
- `LOG_LEVEL` - Logging level (default: INFO)
- `APP_ENV_FILE` - Env file used by compose (default: `.env.staging`)
- `BASE_URL` - Public API URL (default: `https://api.staging.odysseytracker.com`)
- `CELERY_BROKER_URL` - Broker/backend (default: `redis://redis:6379/0`)
- `CELERY_TIMEZONE` - Beat timezone (default: `America/Chicago`)
- `HCP_BASE_URL` - HCP API host (default: `https://secure.saashr.com`)
- `HCP_PAYROLL_SCHEDULER_ENABLED` - Legacy in-process scheduler; compose sets it to
  `false` so Celery beat is the only scheduler. Set `true` only if running without Redis.

### Ports

- **8000** - FastAPI application
- **80** - Nginx HTTP
- **443** - Nginx HTTPS (configure SSL first)
- **5432** - PostgreSQL database
- **6379** - Redis (internal to the compose network, not published)

## 📊 Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Or through nginx
curl http://localhost/health
```

### Logs

```bash
# Application logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db

# Nginx logs
docker-compose logs -f nginx

# Background jobs
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat

# All logs
docker-compose logs -f
```

### Container Status

```bash
# Check running containers
docker-compose ps

# Check resource usage
docker stats
```

## 🔒 Security Best Practices

1. **Change default passwords** in `.env`
2. **Use strong SECRET_KEY** (32+ random characters)
3. **Enable HTTPS** in production (configure nginx SSL)
4. **Restrict CORS_ORIGINS** to your frontend domain
5. **Keep Docker images updated**
6. **Use secrets management** for production

## 🔐 SSL/HTTPS Setup (Production)

1. **Get SSL certificate** (Let's Encrypt recommended):

   ```bash
   # Install certbot
   sudo apt-get install certbot

   # Get certificate
   sudo certbot certonly --standalone -d yourdomain.com
   ```

2. **Copy certificates:**

   ```bash
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
   ```

3. **Update nginx.conf** - Uncomment HTTPS server block

4. **Restart:**
   ```bash
   docker-compose restart nginx
   ```

## 🗄️ Database Management

### Backup

```bash
# Create backup
docker-compose exec db pg_dump -U admin alpha_granite > backup_$(date +%Y%m%d_%H%M%S).sql

# Or using docker
docker exec alpha_granite_db pg_dump -U admin alpha_granite > backup.sql
```

### Restore

```bash
# Restore from backup
docker-compose exec -T db psql -U admin alpha_granite < backup.sql
```

### Access Database

```bash
# PostgreSQL shell
docker-compose exec db psql -U admin -d alpha_granite

# From host (if you have psql)
psql -h localhost -U admin -d alpha_granite
```

## 🐛 Troubleshooting

### Migration Issues

```bash
# Check migration logs
docker-compose logs web | grep -i migration

# Run migration manually
docker-compose exec web python scripts/auto_migrate.py
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify connection
docker-compose exec db pg_isready -U admin
```

### Application Crashes

```bash
# Check logs
docker-compose logs --tail=100 web

# Restart application
docker-compose restart web

# Rebuild if needed
docker-compose up -d --build web
```

### Port Conflicts

If ports are already in use, update in `.env`:

```env
APP_PORT=8001
DATABASE_PORT=5433
NGINX_HTTP_PORT=8080
```

### Scheduled Pulls Not Running

```bash
# Is beat ticking? Look for "Scheduler: Sending due task"
docker-compose logs --tail=50 celery_beat

# Is the worker connected to the broker?
docker-compose logs --tail=50 celery_worker

# Is Redis reachable?
docker-compose exec redis redis-cli ping
```

Common causes:

- Container not rebuilt after `celery[redis]` was added to `requirements.txt`
- Config row is `is_active = false`, or its `schedule_*` columns never match
- Duplicate pulls means more than one `celery_beat` container is running
- Credentials rejected by HCP; check `GET /api/v1/hcp-payroll/runs` for the error

## 📦 Updates and Maintenance

### Update Application

```bash
# Pull latest code
git pull origin job

# Rebuild and restart
docker-compose up -d --build

# Check logs
docker-compose logs -f web
```

### Clean Up

```bash
# Remove stopped containers
docker-compose down

# Remove volumes (⚠️ deletes data)
docker-compose down -v

# Clean up images
docker system prune -a
```

## 🎯 Production Checklist

- [ ] Update all passwords in `.env`
- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` with actual frontend domain
- [ ] Set `DEBUG=False`
- [ ] Configure SSL certificates
- [ ] Enable HTTPS in nginx
- [ ] Set up database backups (cron job)
- [ ] Configure firewall rules
- [ ] Set up monitoring/alerting
- [ ] Review and adjust resource limits
- [ ] Test failover scenarios
- [ ] Run exactly one `celery_beat` replica
- [ ] Verify HCP configs with `POST /api/v1/hcp-payroll/settings/{id}/test` before enabling

## 📞 Support

For issues or questions:

- Check logs first: `docker-compose logs -f`
- Review this documentation
- Check Docker/FastAPI documentation

## 🔄 CI/CD Integration

To integrate with GitHub Actions or similar:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main, job]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          ssh user@server 'cd /app && git pull && ./deploy.sh'
```
