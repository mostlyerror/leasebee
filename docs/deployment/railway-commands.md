# 🛤️ Railway CLI Quick Reference

Essential Railway CLI commands for LeaseBee deployment and management.

---

## 🔗 Project & Service Management

### Link to Project
```bash
# Link to the leasebee project
railway link
# Then select:
# - Project: leasebee
# - Environment: production
```

### Check Current Status
```bash
# Show current linked project/service
railway status

# List all environment variables
railway variables

# List variables for specific service
railway variables --service backend
railway variables --service frontend
```

### View Logs
```bash
# Stream backend logs
railway logs --service backend

# Stream frontend logs
railway logs --service frontend

# View last 100 lines
railway logs --service backend --lines 100
```

---

## 🗃️ Database Operations

### Run Database Migrations
```bash
# From backend directory
cd backend
railway run --service backend alembic upgrade head
```

### Check Database Tables
```bash
railway run --service backend python -c "from app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

### Access PostgreSQL Shell
```bash
railway run --service Postgres psql
```

### Run SQL Query
```bash
railway run --service Postgres psql -c "SELECT COUNT(*) FROM users;"
```

---

## 👤 User Management

### Create Admin User
```bash
railway run --service backend python scripts/create_admin_user.py
```

### Check Users in Database
```bash
railway run --service Postgres psql -c "SELECT id, email, name, is_active FROM users;"
```

### Check Organizations
```bash
railway run --service Postgres psql -c "SELECT id, name, slug, plan FROM organizations;"
```

---

## ⚙️ Environment Variables

### Set a Variable
```bash
# Set single variable
railway variables set --service backend ANTHROPIC_API_KEY=sk-ant-...

# Set from file
railway variables set --service backend --from-file .env.production
```

### Get a Variable
```bash
railway variables get --service backend ANTHROPIC_API_KEY
```

### Delete a Variable
```bash
railway variables delete --service backend OLD_VARIABLE_NAME
```

---

## 🚀 Deployment

### Trigger Manual Deployment
```bash
# Redeploy current version
railway up --service backend

# Deploy with environment selection
railway up --service backend --environment production
```

### Check Deployment Status
```bash
railway status
```

---

## 🐚 Interactive Shell Access

### Backend Shell
```bash
# Open shell in backend container
railway shell --service backend

# Run single command
railway run --service backend ls -la

# Start Python REPL
railway run --service backend python
```

### Database Shell
```bash
# PostgreSQL interactive shell
railway run --service Postgres psql $DATABASE_URL
```

---

## 🔍 Health Checks

### Check Backend Health
```bash
# Get backend URL first
BACKEND_URL=$(railway service --service backend | grep "URL" | awk '{print $2}')

# Check health endpoint
curl $BACKEND_URL/health

# Or manually:
curl https://your-backend-url.up.railway.app/health
```

### Check Frontend
```bash
curl -I https://your-frontend-url.up.railway.app
```

---

## 📊 Monitoring & Debugging

### View Recent Logs
```bash
# Last 50 lines
railway logs --service backend --lines 50

# Follow logs in real-time
railway logs --service backend --follow
```

### Check Resource Usage
```bash
railway status --service backend
```

### Check Environment
```bash
# Show all environment variables
railway variables --service backend

# Export to .env format
railway variables --service backend --kv > .env.railway
```

---

## 🔧 Common Commands for LeaseBee

### Full Deployment Sequence
```bash
# 1. Link to project
railway link

# 2. Run migrations
railway run --service backend alembic upgrade head

# 3. Create admin user
railway run --service backend python scripts/create_admin_user.py

# 4. Check backend health
curl $(railway service backend | grep URL | awk '{print $2}')/health

# 5. View logs
railway logs --service backend --lines 100
```

### Update CORS After Frontend Deploys
```bash
# Get frontend URL
FRONTEND_URL="https://your-frontend-url.up.railway.app"

# Update CORS origins
railway variables set --service backend CORS_ORIGINS="$FRONTEND_URL,http://localhost:3000"

# Trigger redeploy
railway up --service backend
```

### Rollback to Previous Deployment
```bash
# List recent deployments
railway deployments --service backend

# Rollback to specific deployment
railway rollback --service backend --deployment <deployment-id>
```

---

## 🆘 Troubleshooting Commands

### Backend Won't Start
```bash
# Check logs for errors
railway logs --service backend --lines 200

# Check environment variables
railway variables --service backend

# Check if database is accessible
railway run --service backend python -c "from app.database import engine; engine.connect(); print('✅ Database connected')"
```

### Database Migration Issues
```bash
# Check current migration version
railway run --service backend alembic current

# Show migration history
railway run --service backend alembic history

# Downgrade one version
railway run --service backend alembic downgrade -1

# Upgrade to latest
railway run --service backend alembic upgrade head
```

### CORS Issues
```bash
# Check current CORS setting
railway variables get --service backend CORS_ORIGINS

# Update CORS
railway variables set --service backend CORS_ORIGINS="https://frontend-url.up.railway.app,http://localhost:3000"
```

---

## 🔑 Getting Service URLs

### Get Backend URL
```bash
# Method 1: From Railway CLI
railway domain --service backend

# Method 2: From dashboard
# Go to: Settings → Networking → Domains
```

### Get Frontend URL
```bash
railway domain --service frontend
```

---

## 💾 Backup & Restore

### Backup Database
```bash
# Dump database to file
railway run --service Postgres pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
# Restore from backup file
railway run --service Postgres psql $DATABASE_URL < backup_20260202.sql
```

---

## 📝 Useful Aliases

Add these to your `~/.zshrc` or `~/.bashrc`:

```bash
# LeaseBee Railway shortcuts
alias rb-backend='railway logs --service backend --follow'
alias rb-frontend='railway logs --service frontend --follow'
alias rb-status='railway status'
alias rb-vars='railway variables'
alias rb-migrate='railway run --service backend alembic upgrade head'
alias rb-shell='railway shell --service backend'
alias rb-psql='railway run --service Postgres psql'
```

---

## 🔗 Quick Links

- **Railway Dashboard:** https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
- **Railway Docs:** https://docs.railway.app/
- **Railway CLI Docs:** https://docs.railway.app/develop/cli

---

## 📚 Related Documentation

- `DEPLOY_NOW.md` - Step-by-step deployment guide
- `ENV_VARIABLES_REFERENCE.md` - All environment variables
- `DEPLOYMENT_STATUS.md` - Current deployment progress
- `verify-deployment.sh` - Automated verification script

---

**Pro Tip:** Use `railway --help` to see all available commands and options!
