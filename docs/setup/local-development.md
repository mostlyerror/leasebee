# Development Setup Guide

Step-by-step guide to set up the Lease Abstraction System for local development.

## Prerequisites

Install the following:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** and npm - [Download](https://nodejs.org/)
- **PostgreSQL 14+** - [Download](https://www.postgresql.org/download/)
- **Git** - [Download](https://git-scm.com/downloads)

## Initial Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd abstract2
```

### 2. Set Up PostgreSQL Database

Create a new database:

```bash
# Using psql
psql -U postgres
CREATE DATABASE lease_abstraction;
\q
```

Or use a GUI tool like pgAdmin, TablePlus, or Postico.

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

Edit `.env` and configure:

```bash
# Database - update with your local PostgreSQL credentials
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/lease_abstraction

# Anthropic API
ANTHROPIC_API_KEY=your_api_key_here  # Get from https://console.anthropic.com/

# AWS S3 (for local dev, you can use localstack or real S3)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=lease-abstraction-dev

# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:3000

# API Settings
MAX_UPLOAD_SIZE_MB=50
ALLOWED_FILE_TYPES=application/pdf
```

Run database migrations:

```bash
# Make sure you're in the backend directory
alembic upgrade head
```

Start the backend server:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

API documentation: http://localhost:8000/docs

### 4. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
```

Edit `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the frontend dev server:

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Testing the Setup

### 1. Check Backend Health

Visit http://localhost:8000/health

You should see:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "database": "healthy"
}
```

### 2. Check Frontend

Visit http://localhost:3000

You should see the Lease Dashboard.

### 3. Test Upload (Optional)

If you have a test PDF:
1. Click "Upload Lease"
2. Select a PDF file
3. Wait for extraction to complete
4. Review the extracted data

## Development Workflow

### Backend Development

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run server with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest

# Create new migration after model changes
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend Development

```bash
# Run dev server
npm run dev

# Type check
npm run type-check

# Build for production (test)
npm run build
npm start
```

## Alternative: Using Docker (Optional)

If you prefer Docker:

```bash
# Create docker-compose.yml (example)
version: '3.8'
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: lease_abstraction
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/lease_abstraction
    depends_on:
      - db
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

Then run:
```bash
docker-compose up
```

## Common Issues

### Database Connection Error

**Error:** `FATAL: password authentication failed`

**Solution:**
- Check DATABASE_URL in `.env`
- Verify PostgreSQL is running: `pg_isready`
- Check PostgreSQL logs

### Port Already in Use

**Error:** `Address already in use: 8000` or `3000`

**Solution:**
```bash
# Find process using port
lsof -i :8000  # or :3000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
- Make sure you're in the correct directory
- Virtual environment is activated
- Dependencies are installed: `pip install -r requirements.txt`

### Anthropic API Error

**Error:** `Invalid API key`

**Solution:**
- Get API key from https://console.anthropic.com/
- Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
- Restart the backend server

### Frontend Build Error

**Error:** `Cannot find module '@/...'`

**Solution:**
- Check tsconfig.json paths configuration
- Delete `.next` folder and node_modules
- Reinstall: `npm install`
- Rebuild: `npm run dev`

## Environment Variables Reference

### Backend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://user:pass@localhost:5432/db |
| ANTHROPIC_API_KEY | Claude API key | sk-ant-... |
| AWS_ACCESS_KEY_ID | AWS access key | AKIA... |
| AWS_SECRET_ACCESS_KEY | AWS secret key | secret |
| S3_BUCKET_NAME | S3 bucket name | lease-pdfs |
| ENVIRONMENT | Environment name | development |
| DEBUG | Debug mode | true |
| SECRET_KEY | App secret key | random-string |
| CORS_ORIGINS | Allowed origins | http://localhost:3000 |

### Frontend (.env.local)

| Variable | Description | Example |
|----------|-------------|---------|
| NEXT_PUBLIC_API_URL | Backend API URL | http://localhost:8000 |

## Next Steps

1. Read the [Architecture Overview](../README.md)
2. Review the [API Documentation](http://localhost:8000/docs)
3. Check the [Field Schema](../backend/app/schemas/field_schema.py)
4. Try uploading a test lease PDF
5. Explore the code and start developing!

## Getting Help

- Check existing issues in the repository
- Review error logs: backend terminal and frontend terminal
- Use the API docs: http://localhost:8000/docs
- Check PostgreSQL logs for database issues
