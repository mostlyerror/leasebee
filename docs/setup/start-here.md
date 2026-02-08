# 🚀 LeaseBee Deployment - START HERE

**Welcome!** This guide will help you deploy LeaseBee to Railway in ~15 minutes.

---

## ⚡ Quick Status

✅ **Ready to deploy!** All credentials are prepared, Railway project is set up, and the database is running.

**What's needed from you:**
1. Deploy backend service (5 minutes) - via Railway dashboard
2. Deploy frontend service (5 minutes) - via Railway dashboard
3. Provide AWS S3 credentials (optional, for PDF storage)

**What I'll do automatically:**
1. Run database migrations
2. Update CORS configuration
3. Create admin user account
4. Verify deployment

---

## 📖 Quick Navigation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **START_HERE.md** (this file) | Overview & quick start | Read this first |
| **DEPLOYMENT_STATUS.md** | Track deployment progress | Check current status |
| **DEPLOY_NOW.md** | Detailed step-by-step guide | Follow during deployment |
| **ENV_VARIABLES_REFERENCE.md** | All environment variables | Reference when configuring |
| **RAILWAY_COMMANDS.md** | CLI command reference | When using Railway CLI |
| **verify-deployment.sh** | Automated verification | After deployment completes |

---

## 🎯 Deployment Overview

```
┌─────────────────────────────────────────────────────────┐
│  YOU: Deploy Backend (5 min)                            │
│  - Create service via Railway dashboard                 │
│  - Add environment variables                            │
│  - Deploy and get URL                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  ME: Run Database Migrations (1 min)                    │
│  - Create all database tables                           │
│  - Verify schema                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  YOU: Deploy Frontend (5 min)                           │
│  - Create service via Railway dashboard                 │
│  - Add backend URL                                      │
│  - Deploy and get URL                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  ME: Finalize Setup (2 min)                             │
│  - Update CORS configuration                            │
│  - Create admin user                                    │
│  - Verify everything works                              │
└─────────────────────────────────────────────────────────┘
```

---

## 🏁 Step 1: Deploy Backend (DO THIS NOW)

### What You'll Do:
1. Open Railway project: https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
2. Click **"+ New"** → **"GitHub Repo"**
3. Select: `mostlyerror/leasebee` on branch `feat/accuracy-improvements`
4. **⚠️ CRITICAL:** Set **Root Directory = `backend`**
5. Configure start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (see below)
7. Deploy and wait for completion
8. Get the backend URL from Settings → Networking

### Environment Variables to Copy-Paste:

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=dh0U8CJta3rH7cks7JVrs6nR85s5IlhonG8ghogLrZk
DEBUG=false
ENVIRONMENT=production
ANTHROPIC_API_KEY=sk-ant-YOUR-API-KEY-HERE
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
AWS_ACCESS_KEY_ID=<YOUR_AWS_KEY_OR_LEAVE_BLANK>
AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_OR_LEAVE_BLANK>
AWS_REGION=us-east-1
S3_BUCKET_NAME=leasebee-documents-prod
CORS_ORIGINS=http://localhost:3000
```

> **Note on AWS:** If you don't have AWS credentials yet, you can deploy without them. PDF uploads will fail until you add real credentials later.

### ✅ Checkpoint
**Once backend is deployed, tell me:** "Backend deployed at [URL]"

---

## 🏁 Step 2: I Run Migrations

**No action needed from you.** I'll run:
```bash
railway run --service backend alembic upgrade head
```

This creates all database tables (users, organizations, leases, etc.)

---

## 🏁 Step 3: Deploy Frontend

### What You'll Do:
1. In same Railway project, click **"+ New"** → **"GitHub Repo"**
2. Select: `mostlyerror/leasebee` on branch `feat/accuracy-improvements`
3. **⚠️ CRITICAL:** Set **Root Directory = `frontend`**
4. Add environment variable: `NEXT_PUBLIC_API_URL=<backend-url-from-step-1>`
5. Deploy and wait for completion
6. Get the frontend URL from Settings → Networking

### Environment Variable:
```bash
NEXT_PUBLIC_API_URL=<paste-backend-url-here>
```

**Example:**
```bash
NEXT_PUBLIC_API_URL=https://backend-production-xyz.up.railway.app
```

### ✅ Checkpoint
**Once frontend is deployed, tell me:** "Frontend deployed at [URL]"

---

## 🏁 Step 4: I Finalize Setup

**No action needed from you.** I'll:
1. Update backend CORS_ORIGINS to include frontend URL
2. Create admin user: `admin@leasebee.com` / `changeme123`
3. Run verification tests
4. Confirm everything works

---

## 🎉 Done! Test Your Deployment

1. Open your frontend URL in a browser
2. Log in with: `admin@leasebee.com` / `changeme123`
3. **IMPORTANT:** Change the password immediately
4. Try uploading a test lease document
5. Verify extraction works

---

## ⚠️ AWS S3 Setup (Optional)

If you skipped AWS credentials and want to enable PDF uploads:

### Create S3 Bucket
1. Go to AWS Console → S3
2. Create bucket: `leasebee-documents-prod`
3. Region: `us-east-1`
4. Block public access: ✅ Enabled

### Create IAM User
1. Go to AWS Console → IAM → Users
2. Create user: `leasebee-s3-access`
3. Attach policy: `AmazonS3FullAccess`
4. Create access keys
5. Copy Access Key ID and Secret Access Key

### Add to Railway
1. Go to backend service → Variables
2. Update:
   ```bash
   AWS_ACCESS_KEY_ID=<your-access-key-id>
   AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
   ```
3. Backend will auto-redeploy

---

## 🐛 Troubleshooting

### Backend won't deploy
- Check deployment logs in Railway
- Verify all environment variables are set
- Ensure root directory is set to `backend`

### Frontend can't reach backend
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend CORS_ORIGINS includes frontend URL
- Ensure backend `/health` endpoint responds

### CORS errors in browser
- Wait for me to update CORS in Step 4
- Or manually add frontend URL to backend CORS_ORIGINS

### Need more help?
- Check `DEPLOY_NOW.md` for detailed instructions
- Review deployment logs in Railway
- Ask me for help with specific error messages

---

## 📚 Additional Resources

### Documentation
- **Detailed Guide:** `DEPLOY_NOW.md`
- **Environment Vars:** `ENV_VARIABLES_REFERENCE.md`
- **Track Progress:** `DEPLOYMENT_STATUS.md`
- **CLI Commands:** `RAILWAY_COMMANDS.md`

### Scripts
- **Verification:** `./verify-deployment.sh`
- **Create Admin:** `scripts/create_admin_user.py`

### Links
- **Railway Project:** https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80
- **GitHub Repo:** https://github.com/mostlyerror/leasebee
- **Railway Docs:** https://docs.railway.app/

---

## 💡 Pro Tips

1. **Copy environment variables carefully** - Extra spaces or missing characters cause issues
2. **Root directory is critical** - Must be set via web dashboard on first deploy
3. **CORS takes time** - I'll update it after frontend deploys, don't worry about initial errors
4. **Change admin password** - First thing after logging in
5. **Monitor logs** - Use `railway logs --service backend` to watch for issues

---

## 🎯 Success Criteria

Your deployment is successful when:

- ✅ Backend `/health` endpoint returns `{"status": "healthy"}`
- ✅ Frontend loads without errors
- ✅ You can log in with admin credentials
- ✅ Dashboard displays correctly
- ✅ (Optional) PDF uploads work if AWS configured

---

## 🚀 Ready?

**Start with Step 1 above!** Open the Railway project and deploy the backend service.

Once backend is deployed and you have the URL, come back and tell me so I can run the migrations and continue with the process.

**Railway Project:** https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80

---

**Questions?** Just ask! I'm here to help. 🤖
