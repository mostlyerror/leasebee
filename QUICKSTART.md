# 🐝 LeaseBee Quick Start Guide

Get LeaseBee buzzing in 10 minutes!

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- AWS S3 bucket (or use localstack for local dev)

## Setup Steps

### 1. Database

Create PostgreSQL database:

```bash
psql -U postgres
CREATE DATABASE lease_abstraction;
\q
```

### 2. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

Edit `.env` - **minimum required**:

```bash
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/lease_abstraction
ANTHROPIC_API_KEY=your_anthropic_api_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=your-bucket-name
SECRET_KEY=any-random-string-for-dev
```

Run migrations and start:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Backend running at http://localhost:8000

### 3. Frontend

Open new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
```

Edit `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start frontend:

```bash
npm run dev
```

Frontend running at http://localhost:3000

## First Use

1. Open http://localhost:3000
2. Click "Upload Lease"
3. Select a PDF lease document
4. Wait for extraction (30-90 seconds)
5. Review and edit extracted data
6. Click "Export JSON" to download

## What Just Happened?

1. PDF uploaded to S3
2. Claude AI extracted 40+ fields
3. Data saved to PostgreSQL
4. You can review/edit in the UI
5. Export to JSON for Google Sheets

## Cost Per Lease

- Claude API: ~$0.24
- S3 Storage: ~$0.0001
- **Total: ~$0.24 per lease**

## Next Steps

- Read [docs/setup.md](docs/setup.md) for detailed setup
- Customize fields in `backend/app/schemas/field_schema.py`
- Check [docs/deployment.md](docs/deployment.md) for production

## Troubleshooting

### Backend won't start

- Check DATABASE_URL is correct
- Verify PostgreSQL is running: `pg_isready`
- Make sure virtual environment is activated

### Frontend can't connect

- Verify backend is running at http://localhost:8000/health
- Check NEXT_PUBLIC_API_URL in `.env.local`

### Extraction fails

- Verify ANTHROPIC_API_KEY is valid
- Check you have API credits
- Look at backend terminal for error messages

### S3 upload fails

- Verify AWS credentials
- Check bucket exists and permissions are correct
- For local dev, consider using localstack

## Support

- API Docs: http://localhost:8000/docs
- Backend logs: Terminal running uvicorn
- Frontend logs: Terminal running npm + browser console

## Production Ready?

This is Phase 1 (MVP). Before production:

- [ ] Set up production database (Railway/Supabase)
- [ ] Deploy backend (Railway/Render)
- [ ] Deploy frontend (Vercel)
- [ ] Add authentication (Phase 4)
- [ ] Set up monitoring (Sentry)
- [ ] Configure backups
- [ ] Review security checklist

See [docs/deployment.md](docs/deployment.md) for production deployment.

---

🐝 **LeaseBee** - Sweet lease extraction, no sting!
