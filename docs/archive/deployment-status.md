# 🚀 LeaseBee Deployment Status

**Last Updated:** 2026-02-02

---

## 📊 Current Status

| Component | Status | URL | Notes |
|-----------|--------|-----|-------|
| Railway Project | ✅ Ready | [View Project](https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80) | Project ID: f849268e-7ddf-4d07-a2d7-de5a71c05b80 |
| PostgreSQL Database | ✅ Running | Internal | Auto-configured via Railway |
| Backend Service | ⏳ **PENDING** | Not deployed yet | **ACTION REQUIRED** |
| Frontend Service | ⏳ Waiting | Not deployed yet | Deploy after backend |
| Database Migrations | ⏳ Waiting | - | Run after backend deploys |
| Admin User | ⏳ Waiting | - | Create after migrations |
| CORS Configuration | ⏳ Waiting | - | Update after frontend deploys |

---

## 🔐 Credentials Ready

| Credential | Status | Value | Source |
|------------|--------|-------|--------|
| SECRET_KEY | ✅ Generated | `dh0U8CJta3rH7cks7JVrs6nR85s5IlhonG8ghogLrZk` | Freshly generated |
| ANTHROPIC_API_KEY | ✅ Ready | `sk-ant-YOUR-API-KEY...` | From local .env |
| ANTHROPIC_MODEL | ✅ Ready | `claude-sonnet-4-5-20250929` | Latest model |
| DATABASE_URL | ✅ Auto-configured | `${{Postgres.DATABASE_URL}}` | Railway reference |
| AWS_ACCESS_KEY_ID | ⚠️ **NEEDED** | Currently "test" | Need real AWS IAM key |
| AWS_SECRET_ACCESS_KEY | ⚠️ **NEEDED** | Currently "test" | Need real AWS secret |
| AWS_REGION | ✅ Ready | `us-east-1` | Standard region |
| S3_BUCKET_NAME | ⚠️ **NEEDED** | `leasebee-documents-prod` | Need to create bucket |

---

## 📋 Deployment Checklist

### Phase 1: Backend Deployment (USER ACTION REQUIRED)

- [ ] **Step 1.1:** Open Railway project dashboard
- [ ] **Step 1.2:** Click "+ New" → "GitHub Repo"
- [ ] **Step 1.3:** Select `mostlyerror/leasebee` repo
- [ ] **Step 1.4:** Select branch `feat/accuracy-improvements`
- [ ] **Step 1.5:** ⚠️ **CRITICAL:** Set Root Directory = `backend`
- [ ] **Step 1.6:** Name service: `backend`
- [ ] **Step 1.7:** Configure start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] **Step 1.8:** Add environment variables (see below)
- [ ] **Step 1.9:** Deploy service
- [ ] **Step 1.10:** Get backend URL and save it

**Environment Variables to Add:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=dh0U8CJta3rH7cks7JVrs6nR85s5IlhonG8ghogLrZk
DEBUG=false
ENVIRONMENT=production
ANTHROPIC_API_KEY=sk-ant-YOUR-API-KEY-HERE
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
AWS_ACCESS_KEY_ID=<YOUR_REAL_AWS_KEY>
AWS_SECRET_ACCESS_KEY=<YOUR_REAL_AWS_SECRET>
AWS_REGION=us-east-1
S3_BUCKET_NAME=leasebee-documents-prod
CORS_ORIGINS=http://localhost:3000
```

**🛑 CHECKPOINT:** Once backend is deployed, tell me the backend URL so I can proceed to Phase 2.

---

### Phase 2: Database Migrations (I WILL DO THIS)

- [ ] **Step 2.1:** Link Railway CLI to backend service
- [ ] **Step 2.2:** Run `railway run --service backend alembic upgrade head`
- [ ] **Step 2.3:** Verify tables created successfully
- [ ] **Step 2.4:** Confirm migrations completed

**Commands I'll run:**
```bash
cd backend
railway link
railway run --service backend alembic upgrade head
railway run --service backend python -c "from app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

---

### Phase 3: Frontend Deployment (USER ACTION REQUIRED)

- [ ] **Step 3.1:** In Railway project, click "+ New" → "GitHub Repo"
- [ ] **Step 3.2:** Select `mostlyerror/leasebee` repo (same as before)
- [ ] **Step 3.3:** Select branch `feat/accuracy-improvements`
- [ ] **Step 3.4:** ⚠️ **CRITICAL:** Set Root Directory = `frontend`
- [ ] **Step 3.5:** Name service: `frontend`
- [ ] **Step 3.6:** Configure build: `npm run build`
- [ ] **Step 3.7:** Configure start: `npm start`
- [ ] **Step 3.8:** Add environment variable: `NEXT_PUBLIC_API_URL=<backend-url-from-phase-1>`
- [ ] **Step 3.9:** Deploy service
- [ ] **Step 3.10:** Get frontend URL and save it

**Environment Variable:**
```bash
NEXT_PUBLIC_API_URL=<backend-url-from-phase-1>
```

**Example:**
```bash
NEXT_PUBLIC_API_URL=https://backend-production-xyz.up.railway.app
```

**🛑 CHECKPOINT:** Once frontend is deployed, tell me the frontend URL so I can proceed to Phase 4.

---

### Phase 4: CORS Update (I WILL DO THIS)

- [ ] **Step 4.1:** Update backend CORS_ORIGINS variable
- [ ] **Step 4.2:** Add frontend URL to allowed origins
- [ ] **Step 4.3:** Redeploy backend service
- [ ] **Step 4.4:** Verify CORS headers in browser

**I'll update CORS_ORIGINS to:**
```bash
CORS_ORIGINS=<frontend-url>,http://localhost:3000
```

---

### Phase 5: Admin User Creation (I WILL DO THIS)

- [ ] **Step 5.1:** Run admin user creation script
- [ ] **Step 5.2:** Verify user created successfully
- [ ] **Step 5.3:** Verify organization created
- [ ] **Step 5.4:** Confirm user added to organization

**I'll run:**
```bash
railway run --service backend python scripts/create_admin_user.py
```

**Admin credentials created:**
- Email: `admin@leasebee.com`
- Password: `changeme123`
- Organization: `LeaseBee Admin`

---

### Phase 6: Verification (I WILL DO THIS)

- [ ] **Step 6.1:** Check backend health endpoint
- [ ] **Step 6.2:** Check frontend loads
- [ ] **Step 6.3:** Verify CORS configuration
- [ ] **Step 6.4:** Test database connection
- [ ] **Step 6.5:** Verify auth endpoints respond
- [ ] **Step 6.6:** Run automated verification script

**I'll run:**
```bash
./verify-deployment.sh
```

---

## 🎯 Quick Actions

### What You Need to Do Right Now:

1. **Get AWS Credentials** (if you don't have them):
   - Go to AWS Console → IAM → Users
   - Create user: `leasebee-s3-access`
   - Attach policy: `AmazonS3FullAccess` (or custom policy)
   - Generate access keys
   - Save Access Key ID and Secret Access Key

2. **Create S3 Bucket** (if you don't have one):
   - Go to AWS Console → S3
   - Create bucket: `leasebee-documents-prod`
   - Region: `us-east-1`
   - Block all public access: ✅ Enabled
   - Versioning: ✅ Enabled (optional)

3. **Deploy Backend Service**:
   - Open: https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
   - Follow Phase 1 checklist above
   - Copy backend URL when deployment completes
   - **Tell me the backend URL**

---

## 📞 Communication Protocol

### When Backend is Deployed:
Tell me: "Backend is deployed at [URL]"

### When Frontend is Deployed:
Tell me: "Frontend is deployed at [URL]"

### If You Encounter Errors:
Share the error message and deployment logs

---

## 🐛 Common Issues & Solutions

### Issue: "Root directory not set"
**Solution:** Must set root directory via web dashboard on first deployment

### Issue: "Environment variable not working"
**Solution:** Check spelling, ensure no extra spaces, redeploy service

### Issue: "AWS credentials invalid"
**Solution:** Verify you're using real AWS IAM credentials (not "test")

### Issue: "CORS errors in browser"
**Solution:** Wait for Phase 4 when I update CORS configuration

### Issue: "Database connection failed"
**Solution:** Verify `DATABASE_URL=${{Postgres.DATABASE_URL}}` exactly

---

## 📚 Reference Documents

- **Detailed Guide:** See `DEPLOY_NOW.md`
- **Environment Variables:** See `ENV_VARIABLES_REFERENCE.md`
- **Quick Reference:** See `QUICK_DEPLOY_REFERENCE.md`
- **Deployment Checklist:** See `DEPLOYMENT_CHECKLIST.md`

---

## 🎉 Success Criteria

Deployment is complete when:

1. ✅ Backend responds to `/health` endpoint with `{"status": "healthy"}`
2. ✅ Frontend loads in browser without errors
3. ✅ Database has all tables created
4. ✅ CORS allows frontend to call backend
5. ✅ Admin user can log in successfully
6. ✅ Lease upload works (if AWS S3 configured)
7. ✅ Extraction works with Anthropic API

---

## 📊 Progress Tracker

**Overall Progress:** 30% Complete

- ✅ Railway project setup (10%)
- ✅ PostgreSQL database (10%)
- ✅ Credentials prepared (10%)
- ⏳ Backend deployment (20%) - **NEXT STEP**
- ⏳ Database migrations (10%)
- ⏳ Frontend deployment (20%)
- ⏳ CORS update (5%)
- ⏳ Admin user (5%)
- ⏳ Verification (10%)

---

**READY TO PROCEED:** Start with Phase 1 (Backend Deployment) above! 🚀
