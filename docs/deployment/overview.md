# Deployment Guide

This guide covers deploying the Lease Abstraction System to production.

## Prerequisites

- PostgreSQL database (Railway, Supabase, or managed service)
- AWS S3 bucket (or Cloudflare R2)
- Anthropic API key
- Railway account (for backend) or similar
- Vercel account (for frontend)

## Backend Deployment (Railway)

### 1. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Create a new project
3. Add a PostgreSQL database service
4. Add a new service from GitHub repo

### 2. Environment Variables

Add these environment variables to your Railway service:

```
DATABASE_URL=<provided by Railway PostgreSQL>
ANTHROPIC_API_KEY=<your key>
AWS_ACCESS_KEY_ID=<your key>
AWS_SECRET_ACCESS_KEY=<your secret>
AWS_REGION=us-east-1
S3_BUCKET_NAME=<your bucket>
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate random key>
CORS_ORIGINS=https://your-frontend-domain.vercel.app
MAX_UPLOAD_SIZE_MB=50
ALLOWED_FILE_TYPES=application/pdf
```

### 3. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Build Configuration

Railway will auto-detect Python and use:
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 5. Run Migrations

After first deployment, run migrations:

```bash
railway run alembic upgrade head
```

## Frontend Deployment (Vercel)

### 1. Create Vercel Project

1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Select the `frontend` directory as the root

### 2. Environment Variables

Add to Vercel project settings:

```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 3. Build Settings

Vercel auto-detects Next.js. Verify:
- Framework: Next.js
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `.next`

### 4. Deploy

Push to main branch to trigger deployment.

## AWS S3 Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://lease-abstraction-pdfs --region us-east-1
```

### 2. Enable Encryption

```bash
aws s3api put-bucket-encryption \
  --bucket lease-abstraction-pdfs \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### 3. Create IAM User

1. Create user with programmatic access
2. Attach policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::lease-abstraction-pdfs/*"
    }
  ]
}
```

3. Save access key ID and secret access key

## Database Migrations

### Initial Migration

After deploying for the first time:

```bash
# From backend directory
alembic upgrade head
```

### Future Migrations

After model changes:

```bash
# Generate migration
alembic revision --autogenerate -m "Description of changes"

# Review migration file in alembic/versions/
# Then apply
alembic upgrade head
```

## Health Checks

### Backend Health

```bash
curl https://your-backend.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production",
  "database": "healthy"
}
```

### Frontend

```bash
curl https://your-frontend.vercel.app
```

## Monitoring

### Railway Logs

View backend logs in Railway dashboard or CLI:

```bash
railway logs
```

### Vercel Logs

View frontend logs in Vercel dashboard.

### Database Monitoring

Monitor PostgreSQL through Railway dashboard:
- Connection count
- Query performance
- Storage usage

## Backup Strategy

### Database Backups

Railway PostgreSQL includes automatic daily backups.

Manual backup:
```bash
railway run pg_dump > backup.sql
```

### S3 Backups

Enable versioning on S3 bucket:

```bash
aws s3api put-bucket-versioning \
  --bucket lease-abstraction-pdfs \
  --versioning-configuration Status=Enabled
```

## Scaling Considerations

### Backend Scaling

Railway auto-scales based on traffic. Monitor:
- Response times
- Memory usage
- CPU usage

### Database Scaling

Upgrade PostgreSQL plan as needed:
- More connections
- Higher storage
- Better performance

### Cost Optimization

1. Monitor Anthropic API costs in dashboard
2. Set up CloudWatch alarms for S3 costs
3. Review Railway usage monthly
4. Optimize expensive queries

## Security Checklist

- [ ] Environment variables properly set
- [ ] CORS configured correctly
- [ ] S3 bucket not publicly accessible
- [ ] Database uses SSL connections
- [ ] API key rotation policy
- [ ] Regular dependency updates
- [ ] Error logging (no sensitive data)
- [ ] Rate limiting enabled (future)

## Troubleshooting

### Common Issues

**Database connection failed:**
- Check DATABASE_URL is correct
- Verify Railway PostgreSQL is running
- Check connection limits

**S3 upload failed:**
- Verify AWS credentials
- Check bucket permissions
- Confirm bucket exists in correct region

**Claude API errors:**
- Verify API key is valid
- Check account has credits
- Monitor rate limits

**Frontend can't reach backend:**
- Verify NEXT_PUBLIC_API_URL is correct
- Check CORS_ORIGINS includes frontend URL
- Confirm backend is deployed and healthy

## Rollback Procedure

### Backend Rollback

In Railway dashboard:
1. Go to Deployments
2. Find previous working deployment
3. Click "Rollback to this version"

### Frontend Rollback

In Vercel dashboard:
1. Go to Deployments
2. Find previous working deployment
3. Click "Promote to Production"

### Database Rollback

```bash
# Downgrade one migration
alembic downgrade -1

# Or downgrade to specific version
alembic downgrade <revision>
```

## Support

For deployment issues:
- Check Railway/Vercel status pages
- Review application logs
- Contact support if infrastructure issues
