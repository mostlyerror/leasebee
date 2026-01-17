# 🐝 LeaseBee

*Buzzing through leases in seconds*

AI-powered lease abstraction system to automate extraction of data from commercial lease PDFs into structured formats.

## Overview

LeaseBee uses Claude AI to extract 50-100 fields from commercial lease PDFs, providing source citations and reasoning for verification. It progressively improves through human feedback.

**Target Users:** Commercial real estate teams
**Expected Time Savings:** 70-90% reduction in manual abstraction time
**Tagline:** Sweet lease extraction, no sting 🍯

## Architecture

- **Backend:** Python FastAPI with PostgreSQL
- **Frontend:** Next.js 14+ with TypeScript and shadcn/ui
- **AI:** Anthropic Claude 3.5 Sonnet
- **Storage:** S3/R2 for PDFs, PostgreSQL for metadata

## Project Structure

```
abstract2/
├── backend/           # Python FastAPI application
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── core/     # Configuration
│   └── tests/        # Backend tests
├── frontend/         # Next.js application
│   ├── src/
│   │   ├── app/     # Next.js app router
│   │   ├── components/
│   │   ├── lib/     # Utilities and API client
│   │   └── types/   # TypeScript types
│   └── public/      # Static assets
└── docs/            # Documentation
```

## Features (Phase 1 - MVP)

- ✅ PDF upload with cloud storage
- ✅ AI-powered field extraction
- ✅ Review interface for editing extracted data
- ✅ Export to Google Sheets-compatible JSON
- ✅ Basic accuracy tracking

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure your environment variables
alembic upgrade head  # Run database migrations
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local  # Configure your environment variables
npm run dev
```

### Environment Variables

**Backend (.env):**
- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: Claude API key
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: S3 credentials
- `S3_BUCKET_NAME`: S3 bucket for PDF storage
- `CORS_ORIGINS`: Allowed frontend origins

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Development Workflow

1. Make changes to backend or frontend
2. Test locally with sample lease PDFs
3. Run tests: `pytest` (backend), `npm test` (frontend)
4. Commit changes with descriptive messages
5. Deploy to staging/production

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment

**Backend:** Deploy to Railway or Render
**Frontend:** Deploy to Vercel
**Database:** PostgreSQL on Railway or managed service

See [docs/deployment.md](docs/deployment.md) for detailed instructions.

## Cost Estimates

- Claude API: ~$0.24 per lease
- Infrastructure: $15-30/month
- Storage: ~$0.02/month

## Roadmap

- [x] Phase 1: MVP (upload, extract, review, export)
- [ ] Phase 2: Citations & reasoning display
- [ ] Phase 3: Learning system with feedback
- [ ] Phase 4: Production hardening
- [ ] Phase 5: Advanced features (batch processing, templates)

## License

Proprietary

## Support

For issues or questions, contact the LeaseBee team.

---

🐝 **LeaseBee** - The bee's knees of lease abstraction
