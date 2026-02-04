# ⚡ Quick Deploy Reference Card

One-page reference for Railway deployment. Keep this open while deploying.

---

## 🎯 Current Status
- ✅ Railway project: leasebee
- ✅ PostgreSQL: Running
- ✅ CLI: Authenticated
- ❌ Backend: Not deployed
- ❌ Frontend: Not deployed

---

## 🔗 Essential URLs

| Resource | URL |
|----------|-----|
| Railway Project | https://railway.com/project/f849268e-7ddf-4d07-a2d7-de5a71c05b80 |
| GitHub Repo | https://github.com/mostlyerror/leasebee |
| Branch | feat/accuracy-improvements |
| Anthropic Console | https://console.anthropic.com/settings/keys |
| AWS S3 Console | https://s3.console.aws.amazon.com/ |
| AWS IAM Console | https://console.aws.amazon.com/iam/ |

---

## 🚀 Deployment Order

```
1. Deploy Backend    → Get backend URL
2. Run Migrations    → Create database tables
3. Deploy Frontend   → Get frontend URL
4. Update CORS       → Add frontend URL to backend
5. Create Admin User → Enable first login
6. Verify & Test     → End-to-end testing
```

---

## 🔧 Backend Service Config

**Service Creation (Web Dashboard):**
- **Root Directory:** `backend` ⚠️
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Environment Variables:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=Gh2ylbOzErSpJhk22pZzqx5MBhWUBEzaUTdBi1deaE0
DEBUG=false
ENVIRONMENT=production
ANTHROPIC_API_KEY=<get-from-console.anthropic.com>
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
AWS_ACCESS_KEY_ID=<get-from-aws-iam>
AWS_SECRET_ACCESS_KEY=<get-from-aws-iam>
AWS_REGION=us-east-1
S3_BUCKET_NAME=leasebee-documents-prod
CORS_ORIGINS=http://localhost:3000
```

**After Deploy:**
```bash
# Get backend URL
railway status --service backend

# Run migrations
railway run --service backend alembic upgrade head

# Test health
curl https://<backend-url>/health
```

---

## 🎨 Frontend Service Config

**Service Creation (Web Dashboard):**
- **Root Directory:** `frontend` ⚠️
- **Build Command:** `npm run build`
- **Start Command:** `npm start`

**Environment Variables:**
```bash
NEXT_PUBLIC_API_URL=<backend-url-from-above>
```

**After Deploy:**
```bash
# Get frontend URL
railway status --service frontend

# Test homepage
curl -I https://<frontend-url>
```

---

## 🔄 Update CORS (After Frontend Deploy)

```bash
# Go to backend service → Variables
CORS_ORIGINS=https://<frontend-url>,http://localhost:3000
```

**Then redeploy backend.**

---

## 👤 Create Admin User

```bash
railway run --service backend python

# In Python shell:
from app.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

org = Organization(id=uuid.uuid4(), name="Admin Org", slug="admin-org", plan="FREE")
db.add(org)
db.commit()
db.refresh(org)

user = User(id=uuid.uuid4(), email="admin@leasebee.com", name="Admin", hashed_password=pwd_context.hash("ChangeMe123!"), is_active=True)
db.add(user)
db.commit()
db.refresh(user)

print(f"Org: {org.id}")
print(f"User: {user.id}")

# Exit Python (Ctrl+D)

# Add user to org
railway run --service backend psql $DATABASE_URL -c "INSERT INTO organization_members (organization_id, user_id, role) VALUES ('<org-id>', '<user-id>', 'ADMIN');"
```

---

## ✅ Verification Commands

```bash
# Health check
curl https://<backend-url>/health

# Frontend status
curl -I https://<frontend-url>

# View backend logs
railway logs --service backend

# View frontend logs
railway logs --service frontend

# Run verification script
./verify-deployment.sh

# Check Railway status
railway status
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend won't start | Check logs: `railway logs --service backend` |
| CORS errors | Update CORS_ORIGINS, redeploy backend |
| Frontend 502/503 | Check build logs, verify NEXT_PUBLIC_API_URL |
| Database errors | Verify DATABASE_URL, run migrations |
| S3 upload fails | Check AWS credentials, bucket name |
| API extraction fails | Verify ANTHROPIC_API_KEY |

---

## 📊 Expected Responses

**Backend Health:**
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "connected"
}
```

**Frontend Homepage:**
```
HTTP/1.1 200 OK
```

**Auth Endpoints (no data):**
```
HTTP/1.1 422 Unprocessable Entity
```

---

## 🔑 Required Credentials

Track your credentials here:

```
✅ SECRET_KEY: Gh2ylbOzErSpJhk22pZzqx5MBhWUBEzaUTdBi1deaE0
⬜ ANTHROPIC_API_KEY: _________________________
⬜ AWS_ACCESS_KEY_ID: _________________________
⬜ AWS_SECRET_ACCESS_KEY: _____________________
⬜ S3_BUCKET_NAME: leasebee-documents-prod
```

---

## 📝 Deployment Notes

Track URLs and important info:

```
Backend URL: _____________________________________
Frontend URL: ____________________________________
Admin Email: admin@leasebee.com
Admin Password: ChangeMe123!
Deployment Date: _________________________________
```

---

## ⏱️ Timeline Estimate

- Backend setup: 10 min
- Migrations: 2 min
- Frontend setup: 10 min
- CORS update: 3 min
- Admin user: 5 min
- Verification: 10 min
- **Total: ~40 minutes**

---

## 🎯 Success Criteria

- [ ] Backend health returns 200
- [ ] Frontend loads without errors
- [ ] CORS configured correctly
- [ ] Database tables created
- [ ] Admin user can login
- [ ] API docs accessible at /docs
- [ ] No error logs

---

## 📞 Need Help?

- **Logs:** `railway logs --service <name>`
- **Status:** `railway status`
- **Variables:** `railway variables --service <name>`
- **Shell:** `railway run --service <name> bash`
- **Full Guide:** See DEPLOY_NOW.md
- **Checklist:** See DEPLOYMENT_CHECKLIST.md

---

**Tip:** Open this file side-by-side with Railway dashboard for easy reference! 🚀
