# LeaseBee Railway Deployment Guide

## Quick Start

This application is **100% Railway-ready** with no code changes needed. Just configure environment variables and deploy!

## Prerequisites

- [ ] Railway account (railway.app)
- [ ] AWS account (for S3 storage)
- [ ] Anthropic API key with credits
- [ ] GitHub repository access

## Step 1: Railway Account Setup

1. Go to https://railway.app/
2. Sign up with GitHub
3. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

## Step 2: Create New Railway Project

**Via Dashboard:**
1. Click "New Project"
2. Name it: `leasebee`
3. Click "Add Database" → "PostgreSQL"

**Via CLI:**
```bash
railway init
# Name: leasebee
```

## Step 3: Deploy Backend

### 3.1 Create Backend Service

**Dashboard:**
1. Click "+ New" → "GitHub Repo"
2. Connect `mostlyerror/leasebee` repository
3. Select service root directory: `backend`
4. Railway auto-detects Python

### 3.2 Configure Backend

**Settings → Build & Deploy:**
```
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Watch Paths: backend/**
```

### 3.3 Set Environment Variables

**Copy this template and fill in your values:**

```bash
# Database (Reference from Railway PostgreSQL service)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Anthropic AI (Get from console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# AWS S3 (See Step 5 for S3 setup)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=leasebee-documents-prod
AWS_REGION=us-east-1

# App Configuration
SECRET_KEY=<generate using helper script>
DEBUG=false
ENVIRONMENT=production

# CORS (Update after frontend deploys)
CORS_ORIGINS=http://localhost:3000
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3.4 Deploy Backend

1. Push to `main` branch (or configure different branch)
2. Railway auto-deploys
3. Wait for deployment to complete
4. Note the deployed URL: `https://leasebee-backend-production.up.railway.app`

### 3.5 Run Database Migrations

**Option A - Railway Shell:**
1. Go to backend service → "Shell" tab
2. Run: `alembic upgrade head`

**Option B - CLI:**
```bash
railway link  # Select leasebee project
railway run --service backend alembic upgrade head
```

### 3.6 Verify Backend

```bash
curl https://YOUR-BACKEND-URL.up.railway.app/health

# Expected:
# {"status":"healthy","environment":"production","database":"connected"}
```

## Step 4: Deploy Frontend

### 4.1 Create Frontend Service

**Dashboard:**
1. Click "+ New" → "GitHub Repo"
2. Select same `mostlyerror/leasebee` repository
3. Select service root directory: `frontend`
4. Railway auto-detects Node.js

### 4.2 Configure Frontend

**Settings → Build & Deploy:**
```
Build Command: npm run build
Start Command: npm start
Install Command: npm install
Watch Paths: frontend/**
```

### 4.3 Set Environment Variables

```bash
# Backend API URL (Use your actual backend URL from Step 3.4)
NEXT_PUBLIC_API_URL=https://leasebee-backend-production.up.railway.app
```

### 4.4 Deploy Frontend

1. Railway auto-deploys
2. Wait for build to complete
3. Note the deployed URL: `https://leasebee-production.up.railway.app`

### 4.5 Update Backend CORS

**Go back to backend service:**
1. Settings → Variables
2. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://leasebee-production.up.railway.app,http://localhost:3000
   ```
3. Redeploy backend (or it will redeploy automatically)

## Step 5: Setup AWS S3

### 5.1 Create S3 Bucket

**AWS Console:**
1. Go to S3 → Create bucket
2. Bucket name: `leasebee-documents-prod`
3. Region: `us-east-1`
4. **Block all public access:** ✅ Enabled
5. **Versioning:** ✅ Enabled
6. **Encryption:** AES-256 (default)
7. Create bucket

### 5.2 Create IAM User

**IAM Console:**
1. IAM → Users → "Create user"
2. User name: `leasebee-s3-access`
3. Attach policies directly → Create policy:

**Custom Policy (More Secure):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::leasebee-documents-prod",
        "arn:aws:s3:::leasebee-documents-prod/*"
      ]
    }
  ]
}
```

4. Finish creating user
5. User → Security credentials → Create access key
6. Application running outside AWS → Create
7. **Save Access Key ID and Secret Access Key**
8. Add to backend environment variables

## Step 6: Create Admin User

**Railway Shell (Backend Service):**
```bash
railway run --service backend python
```

**In Python shell:**
```python
from app.core.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

# Create organization
org = Organization(
    id=uuid.uuid4(),
    name="My Organization",
    slug="my-org",
    plan="FREE"
)
db.add(org)
db.commit()
db.refresh(org)

# Create admin user
user = User(
    id=uuid.uuid4(),
    email="admin@yourdomain.com",
    name="Admin User",
    hashed_password=pwd_context.hash("ChangeThisPassword123!"),
    is_active=True
)
db.add(user)
db.commit()
db.refresh(user)

# Add user to organization as admin
member = OrganizationMember(
    organization_id=org.id,
    user_id=user.id,
    role="ADMIN"
)
db.add(member)
db.commit()

print(f"✅ Created admin user: {user.email}")
print(f"   User ID: {user.id}")
print(f"   Org ID: {org.id}")
print(f"   Password: ChangeThisPassword123!")
print(f"\n⚠️  IMPORTANT: Change this password after first login!")

db.close()
```

## Step 7: End-to-End Testing

### 7.1 Test Backend Health

```bash
curl https://YOUR-BACKEND-URL.up.railway.app/health
```

Expected: `{"status":"healthy",...}`

### 7.2 Test Frontend

1. Navigate to: `https://YOUR-FRONTEND-URL.up.railway.app`
2. Should see login page
3. Login with admin credentials
4. Should redirect to dashboard

### 7.3 Test Full Flow

1. **Signup:** Create new account with organization
2. **Login:** Verify JWT authentication works
3. **Upload:** Upload a test PDF lease
4. **Extract:** Wait for Claude API extraction (20-30 seconds)
5. **Review:** Verify PDF viewer and extracted fields
6. **Submit:** Complete review and submit feedback

### 7.4 Check Logs

**Backend logs:**
```bash
railway logs --service backend
```

**Frontend logs:**
```bash
railway logs --service frontend
```

## Step 8: Custom Domain (Optional)

### 8.1 Backend Domain

1. Backend service → Settings → Domains
2. Add custom domain: `api.yourdomain.com`
3. In your DNS provider, add CNAME:
   ```
   api.yourdomain.com → leasebee-backend-production.up.railway.app
   ```

### 8.2 Frontend Domain

1. Frontend service → Settings → Domains
2. Add custom domain: `app.yourdomain.com`
3. In your DNS provider, add CNAME:
   ```
   app.yourdomain.com → leasebee-production.up.railway.app
   ```

### 8.3 Update Environment Variables

**Backend:**
```bash
CORS_ORIGINS=https://app.yourdomain.com,http://localhost:3000
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

Redeploy both services after updating.

## Troubleshooting

### Issue: CORS Errors

**Symptom:** Frontend can't reach backend

**Fix:**
1. Check backend `CORS_ORIGINS` includes frontend URL
2. Ensure URLs use `https://` (not `http://`)
3. Redeploy backend after changing CORS

### Issue: Database Connection Failed

**Fix:**
1. Verify `DATABASE_URL` is correctly referenced from Postgres service
2. Check PostgreSQL service is running in Railway dashboard
3. Verify migrations ran: `railway run --service backend alembic current`

### Issue: S3 Upload Failed

**Fix:**
1. Verify AWS credentials are correct
2. Check bucket name and region match
3. Verify IAM user has S3 permissions
4. Check backend logs for specific error

### Issue: Anthropic API Error

**Fix:**
1. Verify `ANTHROPIC_API_KEY` is valid
2. Check API credits at console.anthropic.com
3. Confirm model name: `claude-3-5-sonnet-20241022`

### Issue: Frontend Env Var Not Working

**Fix:**
1. Verify variable starts with `NEXT_PUBLIC_`
2. Redeploy frontend (env vars are baked into build)
3. Check browser console for actual URL being used

## Monitoring & Maintenance

### View Logs

```bash
# Backend
railway logs --service backend --tail

# Frontend
railway logs --service frontend --tail
```

### Database Backups

Railway automatically backs up PostgreSQL daily.

**Manual backup:**
```bash
railway run --service backend pg_dump > backup-$(date +%Y%m%d).sql
```

### Cost Monitoring

**Railway Dashboard:**
- View usage on project overview
- Set usage alerts in project settings
- Estimated: $20-30/month for both services + database

**External Costs:**
- AWS S3: ~$1-5/month
- Anthropic API: ~$0.015 per document

### Scaling

**If you need more resources:**
1. Project settings → Upgrade to Pro plan
2. Service settings → Increase resource limits
3. Consider adding Redis for caching
4. Add database read replicas for heavy load

## Security Checklist

- [ ] Change admin password after first login
- [ ] Use strong SECRET_KEY (random 32+ characters)
- [ ] Keep Anthropic API key secure
- [ ] Restrict S3 bucket with custom IAM policy
- [ ] Enable Railway 2FA
- [ ] Set up Sentry or error tracking (optional)
- [ ] Configure backup schedule
- [ ] Review Railway access logs regularly

## Next Steps

After successful deployment:

1. **Add Sentry** for error tracking
2. **Setup email service** for notifications
3. **Configure backups** schedule
4. **Add monitoring** and alerts
5. **Implement rate limiting** (optional)
6. **Add health checks** monitoring

---

## Support

- Railway Docs: https://docs.railway.app
- LeaseBee Issues: https://github.com/mostlyerror/leasebee/issues

**Deployment Complete! 🚀**
