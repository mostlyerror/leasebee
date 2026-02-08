# 🚀 LeaseBee Railway Deployment Guide

## ⚡ Quick Status

- ✅ Railway CLI authenticated as Ben (benjamintpoon@gmail.com)
- ✅ Project created: `leasebee`
- ✅ PostgreSQL database provisioned and running
- ✅ Current branch: `feat/accuracy-improvements`
- ❌ Backend service: NOT DEPLOYED (next step)
- ❌ Frontend service: NOT DEPLOYED

**Project URL:** https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80

---

## 🎯 STEP 1: Deploy Backend Service (DO THIS NOW)

### Why Web Dashboard?
Railway requires initial monorepo service setup via web dashboard to configure the root directory correctly.

### Instructions:

1. **Open Railway Project:**
   ```
   https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
   ```

2. **Create Backend Service:**
   - Click "+ New" button
   - Select "GitHub Repo"
   - Choose repository: `mostlyerror/leasebee`
   - Select branch: `feat/accuracy-improvements`
   - **⚠️ CRITICAL: Set Root Directory = `backend`**

3. **Configure Service Settings:**

   Navigate to the new service → Settings

   **Service Name:**
   ```
   backend
   ```

   **Build Settings:**
   - Build Command: (auto-detected from requirements.txt)
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Watch Paths: `backend/**` (optional, for auto-deploy)

4. **Add Environment Variables:**

   Go to Variables tab and add these:

   ```bash
   # Database (Reference from Postgres service)
   DATABASE_URL=${{Postgres.DATABASE_URL}}

   # Security
   SECRET_KEY=dh0U8CJta3rH7cks7JVrs6nR85s5IlhonG8ghogLrZk
   DEBUG=false
   ENVIRONMENT=production

   # Anthropic AI (✅ FROM YOUR LOCAL .ENV)
   ANTHROPIC_API_KEY=sk-ant-YOUR-API-KEY-HERE
   ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

   # AWS S3 (⚠️ YOU NEED TO PROVIDE REAL CREDENTIALS)
   AWS_ACCESS_KEY_ID=<your-aws-access-key>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret>
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=leasebee-documents-prod

   # CORS (will update after frontend deploys)
   CORS_ORIGINS=http://localhost:3000
   ```

   **Note:** The `DATABASE_URL=${{Postgres.DATABASE_URL}}` syntax tells Railway to inject the database URL from your Postgres service automatically.

5. **Deploy:**
   - Railway will automatically detect Python and start building
   - Wait for deployment to complete
   - Check deployment logs for any errors

6. **Get Backend URL:**
   - Go to Settings → Networking
   - Copy the public URL (will be something like `https://backend-production-xxxx.up.railway.app`)
   - Save this URL - you'll need it for frontend and CORS configuration

---

## 🔄 STEP 2: Run Database Migrations

After backend deploys successfully, run migrations to create database tables:

### Option A: Using Railway CLI (Recommended)

```bash
cd /Users/benjaminpoon/dev/leasebee/backend
railway link  # Select leasebee project, production environment, backend service
railway run alembic upgrade head
```

### Option B: Using Railway Web Shell

1. Go to backend service → Deployments tab
2. Click on latest deployment → Shell
3. Run: `alembic upgrade head`

### Verify Tables Created

```bash
railway run python -c "from app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

Expected tables:
- users
- organizations
- organization_members
- leases
- extractions
- field_corrections

---

## 🎨 STEP 3: Deploy Frontend Service

1. **Open Railway Project:**
   ```
   https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
   ```

2. **Create Frontend Service:**
   - Click "+ New" button
   - Select "GitHub Repo"
   - Choose repository: `mostlyerror/leasebee`
   - Select branch: `feat/accuracy-improvements`
   - **⚠️ CRITICAL: Set Root Directory = `frontend`**

3. **Configure Service Settings:**

   **Service Name:**
   ```
   frontend
   ```

   **Build Settings:**
   - Build Command: `npm run build`
   - Start Command: `npm start`
   - Install Command: `npm install`
   - Watch Paths: `frontend/**` (optional)

4. **Add Environment Variable:**

   ```bash
   NEXT_PUBLIC_API_URL=<your-backend-url-from-step-1>
   ```

   Example:
   ```
   NEXT_PUBLIC_API_URL=https://backend-production-xxxx.up.railway.app
   ```

   **⚠️ Important:** Must include `NEXT_PUBLIC_` prefix for Next.js to expose it to the browser.

5. **Deploy:**
   - Railway will auto-detect Node.js and start building
   - Wait for build and deployment to complete
   - Frontend will be available at public URL

6. **Get Frontend URL:**
   - Go to Settings → Networking
   - Copy the public URL (e.g., `https://frontend-production-xxxx.up.railway.app`)

---

## 🔗 STEP 4: Update CORS Configuration

Now that you have the frontend URL, update backend CORS settings:

1. **Go to Backend Service → Variables**
2. **Update CORS_ORIGINS:**
   ```
   CORS_ORIGINS=<your-frontend-url>,http://localhost:3000
   ```

   Example:
   ```
   CORS_ORIGINS=https://frontend-production-xxxx.up.railway.app,http://localhost:3000
   ```

3. **Redeploy Backend:**
   - Backend should auto-redeploy with new variable
   - Or manually trigger redeploy from Deployments tab

---

## 👤 STEP 5: Create Admin User

### Using Railway Shell:

1. Go to backend service → Deployments → Latest → Shell
2. Run: `python`
3. Paste this code:

```python
from app.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

# Create organization
org = Organization(
    id=uuid.uuid4(),
    name="LeaseBee Admin",
    slug="leasebee-admin",
    plan="FREE"
)
db.add(org)
db.commit()
db.refresh(org)

# Create admin user
user = User(
    id=uuid.uuid4(),
    email="admin@leasebee.com",
    name="Admin User",
    hashed_password=pwd_context.hash("ChangeMe123!"),
    is_active=True
)
db.add(user)
db.commit()
db.refresh(user)

print(f"✅ Created organization: {org.name} (ID: {org.id})")
print(f"✅ Created user: {user.email} (ID: {user.id})")
print(f"\n⚠️  Add user to organization with this SQL:")
print(f"INSERT INTO organization_members (organization_id, user_id, role)")
print(f"VALUES ('{org.id}', '{user.id}', 'ADMIN');")
```

4. Copy the SQL statement from output
5. Exit Python shell (Ctrl+D or `exit()`)
6. Run the SQL command:

```bash
railway run psql $DATABASE_URL -c "INSERT INTO organization_members (organization_id, user_id, role) VALUES ('<org-id>', '<user-id>', 'ADMIN');"
```

**Or use Railway CLI locally:**

```bash
cd /Users/benjaminpoon/dev/leasebee/backend
railway run python -c "
from app.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

org = Organization(id=uuid.uuid4(), name='LeaseBee Admin', slug='leasebee-admin', plan='FREE')
db.add(org)
db.commit()
db.refresh(org)

user = User(id=uuid.uuid4(), email='admin@leasebee.com', name='Admin User', hashed_password=pwd_context.hash('ChangeMe123!'), is_active=True)
db.add(user)
db.commit()
db.refresh(user)

print(f'Org ID: {org.id}')
print(f'User ID: {user.id}')
"
```

---

## ✅ STEP 6: Verify Deployment

### Backend Health Check:

```bash
curl https://<your-backend-url>/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "connected"
}
```

### Frontend Check:

```bash
curl -I https://<your-frontend-url>
```

Expected: `200 OK`

### End-to-End Test:

1. Open frontend URL in browser
2. Click "Sign Up"
3. Create account with organization
4. Verify redirect to dashboard
5. Test lease upload (if S3 configured)

---

## 🐛 Troubleshooting

### Backend Won't Start

**Check logs:**
```bash
railway logs --service backend
```

**Common issues:**
- Missing environment variables
- Database connection failed
- Port binding error (ensure using `$PORT`)

### Frontend Can't Reach Backend

**Symptoms:** API errors in browser console

**Solutions:**
1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check backend CORS_ORIGINS includes frontend URL
3. Ensure backend is deployed and healthy
4. Rebuild frontend (env vars are baked into build)

### CORS Errors

**Error:** "Access-Control-Allow-Origin" blocked

**Fix:**
1. Backend → Variables → CORS_ORIGINS
2. Add frontend URL (with https://)
3. Redeploy backend

### Database Connection Failed

**Check:**
```bash
railway variables --service backend
```

Ensure `DATABASE_URL` points to `${{Postgres.DATABASE_URL}}`

### Migrations Failed

**Error:** Tables don't exist

**Run migrations:**
```bash
cd backend
railway run alembic upgrade head
```

---

## 📊 Current Configuration Summary

### Backend Service
```yaml
Name: backend
Root Directory: backend
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Branch: feat/accuracy-improvements
Environment Variables:
  - DATABASE_URL: ${{Postgres.DATABASE_URL}}
  - SECRET_KEY: dh0U8CJta3rH7cks7JVrs6nR85s5IlhonG8ghogLrZk
  - ANTHROPIC_API_KEY: ✅ FROM LOCAL .ENV
  - AWS credentials: ⚠️ NEED REAL CREDENTIALS (currently using "test")
  - CORS_ORIGINS: <to-be-updated-after-frontend-deploy>
```

### Frontend Service
```yaml
Name: frontend
Root Directory: frontend
Build: npm run build
Start: npm start
Branch: feat/accuracy-improvements
Environment Variables:
  - NEXT_PUBLIC_API_URL: <backend-url>
```

### Database Service
```yaml
Name: Postgres
Type: PostgreSQL
Status: ✅ Running
DATABASE_URL: Available as ${{Postgres.DATABASE_URL}}
```

---

## 🎯 Deployment Checklist

### Pre-Deploy
- [x] Railway account created
- [x] Railway CLI authenticated
- [x] Project created: leasebee
- [x] PostgreSQL database provisioned
- [x] SECRET_KEY generated
- [ ] Get Anthropic API key
- [ ] Get AWS S3 credentials
- [ ] Verify S3 bucket exists

### Backend Deploy
- [ ] Create service via web dashboard
- [ ] Set root directory: `backend`
- [ ] Add all environment variables
- [ ] Configure start command
- [ ] Deploy and verify
- [ ] Run database migrations
- [ ] Test /health endpoint

### Frontend Deploy
- [ ] Create service via web dashboard
- [ ] Set root directory: `frontend`
- [ ] Add NEXT_PUBLIC_API_URL
- [ ] Deploy and verify
- [ ] Test homepage loads

### Post-Deploy
- [ ] Update backend CORS_ORIGINS
- [ ] Create admin user
- [ ] Test signup/login
- [ ] Test lease upload
- [ ] Verify end-to-end flow

---

## 🚀 Next Steps After Deployment

1. **Custom Domain (Optional):**
   - Add CNAME records in your DNS
   - Configure in Railway: Settings → Networking → Custom Domains

2. **Monitoring:**
   - Setup error tracking (Sentry)
   - Configure alerts in Railway
   - Monitor resource usage

3. **Security:**
   - Change admin password
   - Enable rate limiting
   - Setup backup schedule
   - Regular security updates

4. **Scaling:**
   - Monitor API usage
   - Consider upgrading Railway plan
   - Add caching layer (Redis)
   - Database read replicas

---

## 💰 Cost Estimate

**Railway (Pro Plan):**
- Backend: ~$10-15/month
- Frontend: ~$5-10/month
- PostgreSQL: ~$5/month
- **Total: ~$20-30/month**

**External:**
- AWS S3: ~$1-5/month
- Anthropic API: Pay per use (~$0.015/document)

---

## 📝 Important Notes

1. **Monorepo Structure:** Must set root directory for each service
2. **Environment Variables:** NEXT_PUBLIC_ prefix required for frontend
3. **CORS:** Must update after frontend URL is known
4. **Database:** Use ${{Postgres.DATABASE_URL}} reference syntax
5. **Migrations:** Must run manually after first backend deploy
6. **Drafts:** Backend makes drafts, frontend needs published documents

---

## 🔗 Quick Links

- Railway Project: https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
- Repository: https://github.com/mostlyerror/leasebee
- Branch: feat/accuracy-improvements

---

**Ready to deploy!** Start with Step 1 above. All code is Railway-ready with zero changes needed. 🚀
