# ✅ LeaseBee Railway Deployment Checklist

Quick reference for deploying LeaseBee to Railway. Check off each item as you complete it.

---

## 📋 Pre-Deployment Setup

### Railway Project
- [x] Railway account created
- [x] Railway CLI installed (v4.27.4)
- [x] Authenticated as Ben (benjamintpoon@gmail.com)
- [x] Project created: "leasebee"
- [x] PostgreSQL database provisioned
- [x] Project URL: https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80

### Credentials & Keys
- [x] SECRET_KEY generated: `Gh2ylbOzErSpJhk22pZzqx5MBhWUBEzaUTdBi1deaE0`
- [ ] Anthropic API key ready (from https://console.anthropic.com/)
- [ ] AWS Access Key ID ready
- [ ] AWS Secret Access Key ready
- [ ] S3 bucket name decided (suggested: `leasebee-documents-prod`)

---

## 🔧 Step 1: Deploy Backend Service

### Create Service (Web Dashboard)
- [ ] Open https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
- [ ] Click "+ New" → "GitHub Repo"
- [ ] Select: `mostlyerror/leasebee`
- [ ] Branch: `feat/accuracy-improvements`
- [ ] **Set Root Directory: `backend`** ⚠️ CRITICAL

### Configure Service
- [ ] Name: `backend`
- [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Watch Paths: `backend/**` (optional)

### Add Environment Variables
- [ ] `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- [ ] `SECRET_KEY=Gh2ylbOzErSpJhk22pZzqx5MBhWUBEzaUTdBi1deaE0`
- [ ] `DEBUG=false`
- [ ] `ENVIRONMENT=production`
- [ ] `ANTHROPIC_API_KEY=<your-key>`
- [ ] `ANTHROPIC_MODEL=claude-sonnet-4-5-20250929`
- [ ] `AWS_ACCESS_KEY_ID=<your-key>`
- [ ] `AWS_SECRET_ACCESS_KEY=<your-secret>`
- [ ] `AWS_REGION=us-east-1`
- [ ] `S3_BUCKET_NAME=<your-bucket>`
- [ ] `CORS_ORIGINS=http://localhost:3000` (will update later)

### Deploy & Verify
- [ ] Trigger deployment
- [ ] Wait for build to complete
- [ ] Check logs for errors
- [ ] Get backend URL from Settings → Networking
- [ ] Backend URL: `___________________________________`
- [ ] Test health endpoint: `curl https://<backend-url>/health`
- [ ] Verify response: `{"status":"healthy","database":"connected"}`

---

## 🗄️ Step 2: Database Migrations

### Run Migrations
- [ ] Option A: `railway run --service backend alembic upgrade head`
- [ ] OR Option B: Use Railway web shell → `alembic upgrade head`

### Verify Tables Created
- [ ] `railway run --service backend python -c "from app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"`
- [ ] Confirm tables exist: users, organizations, organization_members, leases, extractions, field_corrections

---

## 🎨 Step 3: Deploy Frontend Service

### Create Service (Web Dashboard)
- [ ] Open https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
- [ ] Click "+ New" → "GitHub Repo"
- [ ] Select: `mostlyerror/leasebee`
- [ ] Branch: `feat/accuracy-improvements`
- [ ] **Set Root Directory: `frontend`** ⚠️ CRITICAL

### Configure Service
- [ ] Name: `frontend`
- [ ] Build Command: `npm run build`
- [ ] Start Command: `npm start`
- [ ] Install Command: `npm install`
- [ ] Watch Paths: `frontend/**` (optional)

### Add Environment Variables
- [ ] `NEXT_PUBLIC_API_URL=<backend-url-from-step-1>`
  - Example: `https://backend-production-xxxx.up.railway.app`
  - ⚠️ Must include `NEXT_PUBLIC_` prefix
  - ⚠️ No trailing slash

### Deploy & Verify
- [ ] Trigger deployment
- [ ] Wait for build to complete
- [ ] Check logs for errors
- [ ] Get frontend URL from Settings → Networking
- [ ] Frontend URL: `___________________________________`
- [ ] Test homepage: `curl -I https://<frontend-url>`
- [ ] Verify response: `200 OK`

---

## 🔗 Step 4: Update CORS Configuration

### Update Backend CORS
- [ ] Go to backend service → Variables
- [ ] Update `CORS_ORIGINS` to: `<frontend-url>,http://localhost:3000`
  - Example: `https://frontend-production-xxxx.up.railway.app,http://localhost:3000`
  - ⚠️ Comma-separated, no spaces
- [ ] Redeploy backend (should auto-trigger)
- [ ] Verify deployment completes

### Test CORS
- [ ] Open frontend URL in browser
- [ ] Open browser console
- [ ] Check for CORS errors (should be none)

---

## 👤 Step 5: Create Admin User

### Using Railway Shell
- [ ] Go to backend service → Deployments → Latest → Shell
- [ ] Run Python commands (see DEPLOY_NOW.md Step 5)
- [ ] Note organization ID: `___________________________________`
- [ ] Note user ID: `___________________________________`
- [ ] Run SQL to add user to organization
- [ ] Verify: Admin user created successfully

### OR Using Railway CLI
- [ ] `cd /Users/benjaminpoon/dev/leasebee/backend`
- [ ] `railway run python <script>` (see ENV_VARIABLES_REFERENCE.md)
- [ ] Note IDs and run SQL command

---

## ✅ Step 6: Verification & Testing

### Automated Verification
- [ ] Run: `./verify-deployment.sh`
- [ ] Enter backend URL
- [ ] Enter frontend URL
- [ ] Review test results
- [ ] Fix any failures before proceeding

### Manual End-to-End Test
- [ ] Open frontend URL in browser: `___________________________________`
- [ ] Click "Sign Up"
- [ ] Create test account:
  - Email: `test@example.com`
  - Password: `TestPassword123!`
  - Organization: `Test Org`
- [ ] Verify redirect to dashboard
- [ ] Check dashboard loads correctly
- [ ] Test navigation (header links)

### Test Lease Upload (If S3 Configured)
- [ ] Click "Upload Lease" or similar
- [ ] Select test PDF file
- [ ] Verify upload succeeds
- [ ] Check extraction starts
- [ ] Verify PDF viewer loads
- [ ] Test field review interface
- [ ] Submit feedback

### Check Logs
- [ ] Backend logs: `railway logs --service backend`
  - [ ] No error messages
  - [ ] Database connections successful
  - [ ] API requests logging correctly
- [ ] Frontend logs: `railway logs --service frontend`
  - [ ] No error messages
  - [ ] Pages rendering correctly

---

## 🌐 Step 7: AWS S3 Setup (Required for PDF uploads)

### Create S3 Bucket
- [ ] AWS Console → S3 → Create Bucket
- [ ] Name: `leasebee-documents-prod` (or your choice)
- [ ] Region: `us-east-1`
- [ ] Block all public access: ✅ Enabled
- [ ] Bucket versioning: ✅ Enabled (optional)
- [ ] Default encryption: AES-256

### Create IAM User
- [ ] AWS Console → IAM → Users → Add User
- [ ] Username: `leasebee-s3-access`
- [ ] Attach policy: `AmazonS3FullAccess` OR custom policy (see below)
- [ ] Create access key → Application running outside AWS
- [ ] Copy Access Key ID: `___________________________________`
- [ ] Copy Secret Access Key: `___________________________________`
- [ ] Add to backend environment variables
- [ ] Redeploy backend

### Custom IAM Policy (More Secure)
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

---

## 🎉 Step 8: Final Verification

### Health Checks
- [ ] Backend health: `curl https://<backend-url>/health`
  ```json
  {
    "status": "healthy",
    "environment": "production",
    "database": "connected"
  }
  ```
- [ ] Frontend loads: Visit frontend URL
- [ ] API docs accessible: `https://<backend-url>/docs`

### Complete User Flow
- [ ] User signup works
- [ ] Email validation works
- [ ] Login works
- [ ] JWT tokens working (no auth errors)
- [ ] Dashboard loads with user data
- [ ] Organization shows correctly
- [ ] Lease upload works (requires S3)
- [ ] Extraction completes (requires Anthropic API)
- [ ] PDF viewer displays correctly
- [ ] Field review interface works
- [ ] Feedback submission works
- [ ] Data persists in database

### Security Checks
- [ ] HTTPS enabled (automatic on Railway)
- [ ] CORS configured correctly
- [ ] No secrets in logs
- [ ] No error stack traces exposed to frontend
- [ ] Admin password changed from default

---

## 📊 Post-Deployment Tasks

### Monitoring & Alerts
- [ ] Setup Railway resource alerts
- [ ] Configure budget alerts
- [ ] Monitor Anthropic API usage
- [ ] Monitor AWS S3 costs
- [ ] Check database size/usage

### Documentation
- [ ] Document deployed URLs in team wiki/docs
- [ ] Share admin credentials securely (1Password, etc.)
- [ ] Update README with production deployment info
- [ ] Document backup/restore procedures

### Optional Enhancements
- [ ] Configure custom domain (e.g., api.leasebee.com, app.leasebee.com)
- [ ] Setup Sentry for error tracking
- [ ] Add Redis for caching
- [ ] Configure database backups
- [ ] Setup CI/CD webhooks
- [ ] Enable Railway auto-deployments on git push

---

## 🐛 Troubleshooting Reference

### Common Issues

**Backend won't start:**
- Check logs: `railway logs --service backend`
- Verify all environment variables are set
- Confirm DATABASE_URL is correct
- Check for port binding errors

**Frontend can't reach backend:**
- Verify NEXT_PUBLIC_API_URL is set correctly
- Check CORS_ORIGINS includes frontend URL
- Ensure backend is healthy
- Rebuild frontend (env vars are baked in)

**CORS errors:**
- Update backend CORS_ORIGINS with frontend URL
- Ensure URL includes https://
- No trailing slashes
- Redeploy backend

**Database connection failed:**
- Check DATABASE_URL reference: `${{Postgres.DATABASE_URL}}`
- Verify PostgreSQL service is running
- Run migrations if tables don't exist

**S3 upload failed:**
- Verify AWS credentials
- Check bucket name and region
- Confirm IAM permissions
- Test credentials with AWS CLI

**Anthropic API errors:**
- Verify API key is valid
- Check API credits/quota
- Confirm model name is correct

---

## 📝 Important Notes

1. **Monorepo:** Must set root directory for each service
2. **Env Vars:** Use `NEXT_PUBLIC_` prefix for frontend vars
3. **CORS:** Update after getting frontend URL
4. **Database:** Use `${{Postgres.DATABASE_URL}}` syntax
5. **Migrations:** Run manually after first deploy
6. **Rebuilds:** Frontend must rebuild when env vars change
7. **Secrets:** Never commit to git, Railway encrypts at rest

---

## 🔗 Quick Links

- **Railway Project:** https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
- **GitHub Repo:** https://github.com/mostlyerror/leasebee
- **Branch:** feat/accuracy-improvements
- **Backend URL:** `___________________________________`
- **Frontend URL:** `___________________________________`

---

## 📚 Additional Documentation

- **DEPLOY_NOW.md** - Detailed deployment guide
- **ENV_VARIABLES_REFERENCE.md** - Environment variable reference
- **verify-deployment.sh** - Automated verification script
- **Backend README:** `backend/README.md`
- **Frontend README:** `frontend/README.md`

---

**Ready!** Follow this checklist step-by-step. Check off items as you complete them. 🚀

**Estimated Time:** 30-45 minutes for full deployment
