# Project Structure

Complete file structure of the Lease Abstraction System.

```
abstract2/
│
├── README.md                          # Project overview and architecture
├── QUICKSTART.md                      # 10-minute setup guide
├── PROJECT_SUMMARY.md                 # Complete implementation summary
├── STRUCTURE.md                       # This file
├── .gitignore                         # Git ignore rules
│
├── backend/                           # Python FastAPI application
│   ├── README.md                      # Backend documentation
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment template
│   ├── alembic.ini                    # Alembic configuration
│   │
│   ├── alembic/                       # Database migrations
│   │   ├── env.py                     # Migration environment
│   │   ├── script.py.mako             # Migration template
│   │   └── versions/                  # Migration files (generated)
│   │
│   └── app/                           # Application code
│       ├── __init__.py
│       ├── main.py                    # FastAPI app entry point
│       │
│       ├── api/                       # API endpoints
│       │   ├── __init__.py
│       │   ├── health.py              # Health check endpoint
│       │   ├── leases.py              # Lease management endpoints
│       │   └── extractions.py         # Extraction endpoints
│       │
│       ├── core/                      # Configuration & database
│       │   ├── __init__.py
│       │   ├── config.py              # Settings from environment
│       │   └── database.py            # SQLAlchemy setup
│       │
│       ├── models/                    # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   ├── lease.py               # Lease PDF metadata
│       │   ├── extraction.py          # Extracted data
│       │   ├── field_correction.py    # User corrections
│       │   ├── citation_source.py     # PDF citations
│       │   ├── few_shot_example.py    # Learning examples
│       │   └── extraction_feedback.py # Quality ratings
│       │
│       ├── schemas/                   # Pydantic & field schemas
│       │   ├── __init__.py
│       │   ├── field_schema.py        # 40+ lease fields definition
│       │   └── pydantic_schemas.py    # API request/response schemas
│       │
│       └── services/                  # Business logic services
│           ├── __init__.py
│           ├── claude_service.py      # AI extraction with Claude
│           ├── storage_service.py     # S3 file management
│           └── pdf_service.py         # PDF text extraction
│
├── frontend/                          # Next.js React application
│   ├── README.md                      # Frontend documentation
│   ├── package.json                   # Node.js dependencies
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── next.config.js                 # Next.js configuration
│   ├── tailwind.config.js             # Tailwind CSS configuration
│   ├── postcss.config.js              # PostCSS configuration
│   ├── .env.example                   # Environment template
│   │
│   ├── public/                        # Static assets
│   │
│   └── src/                           # Application source
│       ├── app/                       # Next.js app router
│       │   ├── globals.css            # Global styles
│       │   ├── layout.tsx             # Root layout with navigation
│       │   ├── page.tsx               # Home page (dashboard)
│       │   ├── providers.tsx          # React Query provider
│       │   └── leases/
│       │       └── [id]/
│       │           └── page.tsx       # Lease detail & review page
│       │
│       ├── components/                # React components
│       │   ├── ui/                    # Base UI components
│       │   │   ├── button.tsx         # Button component
│       │   │   └── card.tsx           # Card component
│       │   │
│       │   ├── leases/                # Lease-related components
│       │   │   ├── LeaseList.tsx      # List of leases
│       │   │   └── UploadButton.tsx   # PDF upload button
│       │   │
│       │   └── extraction/            # Extraction review components
│       │       ├── ExtractionReview.tsx  # Main review interface
│       │       └── FieldEditor.tsx       # Individual field editor
│       │
│       ├── lib/                       # Utilities and helpers
│       │   ├── api.ts                 # API client (axios)
│       │   └── utils.ts               # Helper functions
│       │
│       └── types/                     # TypeScript type definitions
│           └── index.ts               # All type definitions
│
└── docs/                              # Documentation
    ├── setup.md                       # Development setup guide
    └── deployment.md                  # Production deployment guide
```

## File Count Summary

- **Total files**: 47
- **Python files**: 16
- **TypeScript/TSX files**: 12
- **Configuration files**: 10
- **Documentation files**: 9

## Lines of Code

- **Total**: ~3,250 lines
- **Backend**: ~1,800 lines
- **Frontend**: ~1,450 lines

## Key Files by Purpose

### Configuration
- `backend/.env.example` - Backend environment template
- `frontend/.env.example` - Frontend environment template
- `backend/alembic.ini` - Database migration config
- `frontend/next.config.js` - Next.js config
- `frontend/tailwind.config.js` - Styling config

### Database
- `backend/app/core/database.py` - Database connection
- `backend/app/models/*.py` - 6 database models
- `backend/alembic/` - Migration system

### API
- `backend/app/main.py` - FastAPI application
- `backend/app/api/*.py` - 3 endpoint routers
- `backend/app/schemas/pydantic_schemas.py` - Request/response schemas

### Business Logic
- `backend/app/services/claude_service.py` - AI extraction (200 lines)
- `backend/app/services/storage_service.py` - S3 management
- `backend/app/services/pdf_service.py` - PDF processing
- `backend/app/schemas/field_schema.py` - Field definitions (300+ lines)

### Frontend Pages
- `frontend/src/app/page.tsx` - Dashboard
- `frontend/src/app/leases/[id]/page.tsx` - Review page
- `frontend/src/app/layout.tsx` - App layout

### Frontend Components
- `frontend/src/components/extraction/ExtractionReview.tsx` - Main review UI (150 lines)
- `frontend/src/components/extraction/FieldEditor.tsx` - Field editing
- `frontend/src/components/leases/UploadButton.tsx` - Upload flow
- `frontend/src/components/leases/LeaseList.tsx` - Lease listing

### API Client
- `frontend/src/lib/api.ts` - All API calls (150 lines)
- `frontend/src/types/index.ts` - TypeScript types

### Documentation
- `README.md` - Project overview
- `QUICKSTART.md` - Quick setup
- `PROJECT_SUMMARY.md` - Complete summary
- `docs/setup.md` - Detailed setup
- `docs/deployment.md` - Deployment guide
- `backend/README.md` - Backend docs
- `frontend/README.md` - Frontend docs

## Critical Paths

### Upload Flow
1. `UploadButton.tsx` →
2. `api/leases.py:upload_lease()` →
3. `storage_service.py:upload_pdf()` → S3

### Extraction Flow
1. `api/extractions.py:extract_lease_data()` →
2. `storage_service.py:download_pdf()` →
3. `claude_service.py:extract_lease_data()` →
4. Anthropic API →
5. Save to database

### Review Flow
1. `page.tsx` (lease detail) →
2. `ExtractionReview.tsx` →
3. `FieldEditor.tsx` →
4. `api.ts:update()` →
5. `api/extractions.py:update_extraction()`

### Export Flow
1. `ExtractionReview.tsx` →
2. `api.ts:export()` →
3. `api/extractions.py:export_extraction()` →
4. JSON download

## Dependencies

### Backend (Python)
- fastapi - Web framework
- sqlalchemy - ORM
- alembic - Migrations
- anthropic - Claude API
- boto3 - AWS S3
- PyMuPDF - PDF processing
- pydantic - Validation

### Frontend (Node.js)
- next - React framework
- react-query - Server state
- axios - HTTP client
- react-hook-form - Forms
- tailwindcss - Styling
- typescript - Type safety

## Database Tables

1. `leases` - PDF metadata
2. `extractions` - Extracted data
3. `field_corrections` - User edits
4. `citation_sources` - PDF locations
5. `few_shot_examples` - Training data
6. `extraction_feedback` - Quality ratings

## API Routes

**Leases**: `/api/leases/`
**Extractions**: `/api/extractions/`
**Health**: `/health`
**Docs**: `/docs` (Swagger UI)

## Environment Variables

**Backend** (10 required):
- DATABASE_URL
- ANTHROPIC_API_KEY
- AWS credentials (3)
- SECRET_KEY
- CORS_ORIGINS
- App settings (3)

**Frontend** (1 required):
- NEXT_PUBLIC_API_URL

---

For detailed setup instructions, see [QUICKSTART.md](QUICKSTART.md)
