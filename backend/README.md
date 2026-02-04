# Lease Abstraction Backend

FastAPI backend for the lease abstraction system.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── leases.py     # Lease upload/management
│   │   ├── extractions.py # Extraction endpoints
│   │   └── health.py     # Health check
│   ├── models/           # SQLAlchemy models
│   │   ├── lease.py
│   │   ├── extraction.py
│   │   └── ...
│   ├── schemas/          # Pydantic schemas & field definitions
│   │   ├── field_schema.py     # Lease field definitions
│   │   └── pydantic_schemas.py # Request/response schemas
│   ├── services/         # Business logic
│   │   ├── claude_service.py   # AI extraction
│   │   ├── storage_service.py  # S3 uploads
│   │   └── pdf_service.py      # PDF processing
│   ├── core/             # Configuration
│   │   ├── config.py     # Settings
│   │   └── database.py   # DB connection
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── tests/                # Tests
└── requirements.txt      # Dependencies
```

## Key Components

### Field Schema (`app/schemas/field_schema.py`)

Defines all fields to extract from leases. This is the single source of truth for:
- What data to extract
- Field types and validation
- UI generation
- Export format

To add new fields, edit `LEASE_FIELDS` list.

### Claude Service (`app/services/claude_service.py`)

Handles all AI extraction:
- Builds prompts from field schema
- Calls Anthropic API
- Parses structured responses
- Tracks costs and performance

### Storage Service (`app/services/storage_service.py`)

Manages PDF files in S3:
- Upload with encryption
- Download for processing
- Generate presigned URLs
- Delete on cleanup

## API Endpoints

### Leases

- `POST /api/leases/upload` - Upload PDF
- `GET /api/leases/` - List leases
- `GET /api/leases/{id}` - Get lease
- `DELETE /api/leases/{id}` - Delete lease
- `GET /api/leases/{id}/download-url` - Get download URL

### Extractions

- `POST /api/extractions/extract/{lease_id}` - Extract data
- `GET /api/extractions/lease/{lease_id}` - Get extractions
- `GET /api/extractions/{id}` - Get extraction
- `PATCH /api/extractions/{id}` - Update extraction
- `POST /api/extractions/{id}/corrections` - Add correction
- `POST /api/extractions/{id}/export` - Export data
- `GET /api/extractions/schema/fields` - Get field schema

## Database

Uses PostgreSQL with SQLAlchemy ORM.

### Models

- `Lease` - PDF metadata
- `Extraction` - AI-extracted data
- `FieldCorrection` - User corrections (for learning)
- `CitationSource` - PDF source locations
- `FewShotExample` - Examples for prompts
- `ExtractionFeedback` - Quality ratings

### Migrations

```bash
# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_claude_service.py
```

## Configuration

All configuration is in `app/core/config.py` and loaded from environment variables.

See `.env.example` for required variables.

## Development

```bash
# Activate virtual environment
source venv/bin/activate

# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload --log-level debug

# Format code (if using black)
black app/

# Type check (if using mypy)
mypy app/
```

## Production

See [deployment.md](../docs/deployment.md) for production deployment guide.

Key differences:
- Set `DEBUG=false`
- Use strong `SECRET_KEY`
- Enable HTTPS
- Configure proper `CORS_ORIGINS`
- Use production database
- Monitor costs and errors

## Production Deployment

**Ready to deploy? Check out [DEPLOYMENT.md](./DEPLOYMENT.md)** for the complete Railway deployment guide.

### Railway Deployment (Recommended)

LeaseBee is **100% Railway-ready** with zero code changes needed!

**Quick Deploy:**
1. Create Railway account at railway.app
2. Deploy backend service (FastAPI/Python)
3. Deploy frontend service (Next.js)
4. Add managed PostgreSQL database
5. Configure environment variables
6. Run: `railway run --service backend alembic upgrade head`

**Cost:** ~$20-30/month for both services + database

### Deployment Helper Scripts

```bash
# Generate SECRET_KEY for backend
python scripts/generate_secret_key.py

# Create admin user after deployment
railway run --service backend python scripts/create_admin_user.py

# Verify deployment is working
./scripts/verify_deployment.sh https://your-backend.railway.app https://your-frontend.railway.app
```

### What's Included

- ✅ Step-by-step deployment instructions
- ✅ Environment variable templates
- ✅ Database migration commands
- ✅ AWS S3 setup guide
- ✅ CORS configuration
- ✅ Custom domain setup (optional)
- ✅ Troubleshooting guide
- ✅ Monitoring and maintenance tips

