# 🚀 QUICK START - Deploy in 3 Steps

## For Server Deployment:

### Step 1: Clone Repository
```bash
git clone https://github.com/segunisreal/alpha-granit.git
cd alpha-granit
```

### Step 2: Configure Environment
```bash
cp .env.example .env
nano .env
```

**Update these critical values:**
```env
DATABASE_PASSWORD=your_secure_password_here
SECRET_KEY=your-32-char-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
ADMIN_PASSWORD=your_admin_password_here
CORS_ORIGINS=https://yourfrontend.com
```

### Step 3: Deploy!
```bash
chmod +x deploy.sh
./deploy.sh
```

**That's it!** ✅

The application will:
- Build Docker images
- Start PostgreSQL database
- Run auto-migrations (create all tables)
- Start FastAPI with 4 workers
- Start Nginx reverse proxy
- Run health checks

---

## Verify Deployment:

```bash
# Check health
curl http://localhost:8000/health

# Or run automated health check
./healthcheck.sh

# View logs
./manage.sh logs
```

---

## Access Points:

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Nginx**: http://localhost (if configured)

---

## Common Commands:

```bash
./manage.sh start      # Start services
./manage.sh stop       # Stop services
./manage.sh logs       # View logs
./manage.sh backup     # Backup database
./manage.sh status     # Check status
```

---

## Auto-Migration:

✅ **Runs automatically on startup**
- Creates missing tables
- Removes orphaned tables
- No manual SQL needed!

See migration logs:
```bash
docker-compose logs web | grep -i migration
```

---

## Troubleshooting:

**If something fails:**
```bash
# Check logs
docker-compose logs

# Restart
./manage.sh restart

# Rebuild
./manage.sh build
```

---

## Full Documentation:

- **DEPLOYMENT.md** - Complete deployment guide
- **DEPLOYMENT_SUMMARY.md** - Feature overview
- **README.md** - Development setup

---

## Need Help?

1. Check logs: `./manage.sh logs`
2. Run health check: `./healthcheck.sh`
3. Review: DEPLOYMENT.md
4. Check containers: `docker-compose ps`

---

**🎉 Enjoy your deployed application!**
