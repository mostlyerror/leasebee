# 🔐 LeaseBee Environment Variables Reference

## Backend Service Variables

Copy-paste these into Railway Dashboard → Backend Service → Variables

### Database
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
```
**Note:** This special syntax tells Railway to automatically inject the PostgreSQL connection string.

---

### Security (✅ READY TO USE)
```bash
SECRET_KEY=dh0U8CJta3rH7cks7JVrs6nR85s5IlhonG8ghogLrZk
DEBUG=false
ENVIRONMENT=production
```

---

### Anthropic AI (✅ READY TO USE)
```bash
ANTHROPIC_API_KEY=sk-ant-YOUR-API-KEY-HERE
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

**Source:** Extracted from your local backend/.env file

---

### AWS S3 (⚠️ YOU NEED TO ADD THIS)
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=leasebee-documents-prod
```

**Where to get this:**
1. AWS Console → IAM → Users
2. Select user (or create new user: `leasebee-s3-access`)
3. Security Credentials → Create Access Key
4. Copy Access Key ID and Secret Access Key
5. Paste into Railway

**S3 Bucket Setup:**
1. AWS Console → S3 → Create Bucket
2. Name: `leasebee-documents-prod` (or your choice)
3. Region: `us-east-1`
4. Block all public access: ✅ Enabled
5. Versioning: ✅ Enabled (optional)
6. Encryption: AES-256

---

### CORS (🔄 UPDATE AFTER FRONTEND DEPLOYS)
```bash
# Initially:
CORS_ORIGINS=http://localhost:3000

# After frontend deploys, update to:
CORS_ORIGINS=https://your-frontend-url.up.railway.app,http://localhost:3000
```

**Note:** Comma-separated list, no spaces

---

## Frontend Service Variables

Copy-paste this into Railway Dashboard → Frontend Service → Variables

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.up.railway.app
```

**⚠️ Critical Notes:**
1. Must include `NEXT_PUBLIC_` prefix
2. Replace with actual backend URL from Railway
3. Do NOT include trailing slash
4. Must redeploy frontend after changing this

---

## Optional Variables (for later)

### Error Tracking
```bash
SENTRY_DSN=https://...@sentry.io/...
```

### Logging
```bash
LOG_LEVEL=INFO
```

### File Upload Limits
```bash
MAX_UPLOAD_SIZE_MB=50
ALLOWED_FILE_TYPES=application/pdf
```

---

## ✅ Checklist Before Deploying

### Backend:
- [ ] DATABASE_URL: `${{Postgres.DATABASE_URL}}` ✅ Auto-configured
- [ ] SECRET_KEY: `Gh2ylbO...` ✅ Generated
- [ ] ANTHROPIC_API_KEY: ❌ Need from console.anthropic.com
- [ ] AWS_ACCESS_KEY_ID: ❌ Need from AWS IAM
- [ ] AWS_SECRET_ACCESS_KEY: ❌ Need from AWS IAM
- [ ] AWS_REGION: `us-east-1` ✅ Standard
- [ ] S3_BUCKET_NAME: ❌ Need to create S3 bucket
- [ ] CORS_ORIGINS: ❌ Add after frontend deploys
- [ ] DEBUG: `false` ✅ Production setting
- [ ] ENVIRONMENT: `production` ✅ Set

### Frontend:
- [ ] NEXT_PUBLIC_API_URL: ❌ Add after backend deploys

---

## 🔍 How to Find Missing Values

### Anthropic API Key
```bash
# Login to Anthropic Console
open https://console.anthropic.com/settings/keys

# Create new key named "LeaseBee Production"
# Copy the key (starts with sk-ant-)
```

### AWS Credentials
```bash
# If you have AWS CLI configured:
cat ~/.aws/credentials

# Look for:
# [default]
# aws_access_key_id = AKIA...
# aws_secret_access_key = ...
```

### S3 Bucket Name
```bash
# If you have AWS CLI:
aws s3 ls

# Or check AWS Console:
open https://s3.console.aws.amazon.com/s3/buckets
```

---

## 🚨 Security Best Practices

1. **Never commit these values to Git**
   - Already in `.gitignore`
   - Railway encrypts at rest

2. **Rotate credentials regularly**
   - Anthropic: Every 90 days
   - AWS: Every 90 days
   - SECRET_KEY: On suspected compromise

3. **Use least privilege IAM policies**
   - S3 user should only access specific bucket
   - No admin permissions needed

4. **Monitor usage**
   - Check Anthropic usage dashboard
   - Enable AWS CloudWatch alerts
   - Set Railway budget alerts

---

## 📋 Quick Copy-Paste Template

**Backend Environment Variables:**
```ini
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=dh0U8CJta3rH7cks7JVrs6nR85s5IlhonG8ghogLrZk
DEBUG=false
ENVIRONMENT=production
ANTHROPIC_API_KEY=sk-ant-YOUR-API-KEY-HERE
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
AWS_ACCESS_KEY_ID=<YOUR_AWS_KEY_HERE>
AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_HERE>
AWS_REGION=us-east-1
S3_BUCKET_NAME=leasebee-documents-prod
CORS_ORIGINS=http://localhost:3000
```

**Frontend Environment Variables:**
```ini
NEXT_PUBLIC_API_URL=
```

---

## 🔄 Update Sequence

1. Deploy backend with initial CORS_ORIGINS=http://localhost:3000
2. Get backend URL from Railway
3. Add backend URL to frontend NEXT_PUBLIC_API_URL
4. Deploy frontend
5. Get frontend URL from Railway
6. Update backend CORS_ORIGINS with frontend URL
7. Redeploy backend

---

**Need help?** Check DEPLOY_NOW.md for step-by-step instructions!
