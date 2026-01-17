# Lease Abstraction Frontend

Next.js frontend for the lease abstraction system.

## Quick Start

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with API URL

# Run development server
npm run dev
```

Visit http://localhost:3000

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app router
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page (dashboard)
│   │   ├── providers.tsx      # React Query provider
│   │   └── leases/[id]/       # Lease detail pages
│   ├── components/            # React components
│   │   ├── ui/               # Base UI components
│   │   ├── leases/           # Lease-related components
│   │   └── extraction/       # Extraction review components
│   ├── lib/                  # Utilities
│   │   ├── api.ts           # API client
│   │   └── utils.ts         # Helper functions
│   └── types/               # TypeScript types
├── public/                  # Static assets
└── package.json
```

## Key Components

### ExtractionReview (`components/extraction/ExtractionReview.tsx`)

Main component where users review and edit extracted data:
- Groups fields by category
- Shows confidence scores
- Displays AI reasoning and citations
- Handles saving changes
- Exports to JSON

### FieldEditor (`components/extraction/FieldEditor.tsx`)

Individual field editor:
- Type-appropriate inputs
- Confidence indicators
- Expandable reasoning/citation
- Auto-save on change

### UploadButton (`components/leases/UploadButton.tsx`)

Handles PDF upload flow:
1. File selection
2. Upload to backend
3. Trigger extraction
4. Navigate to review page

## State Management

Uses React Query (@tanstack/react-query) for:
- API data fetching
- Caching
- Background refetching
- Mutation handling

## API Integration

All API calls are in `src/lib/api.ts`:

```typescript
import { leaseApi, extractionApi } from '@/lib/api';

// Upload lease
const lease = await leaseApi.upload(file);

// Extract data
const extraction = await extractionApi.extract(leaseId);

// Update extraction
await extractionApi.update(extractionId, data);

// Export
const exported = await extractionApi.export(extractionId, options);
```

## Styling

Uses Tailwind CSS with custom configuration:

- Design system in `tailwind.config.js`
- Global styles in `src/app/globals.css`
- Component styles inline with Tailwind classes
- Utility function `cn()` for conditional classes

## TypeScript

Fully typed with TypeScript:

- Type definitions in `src/types/index.ts`
- Matches backend Pydantic schemas
- Compile-time safety

```bash
# Type check
npm run type-check
```

## Development

```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Environment Variables

Required in `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Note: Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Features

### Dashboard

- List all uploaded leases
- Status indicators
- Upload new leases
- Delete leases

### Lease Detail / Review

- View extracted data by category
- Edit any field
- See AI confidence scores
- Read AI reasoning
- View source citations
- Save changes
- Export to JSON

### Export

Generates JSON file compatible with Google Sheets import:

```json
{
  "extractions": {
    "basic_info.lease_type": "Office",
    "parties.landlord_name": "...",
    // ... all fields
  },
  "metadata": {
    "lease_id": 1,
    "extraction_id": 1,
    "lease_filename": "lease.pdf",
    "extracted_at": "2025-01-17T...",
    "model_version": "claude-3-5-sonnet..."
  }
}
```

## Deployment

See [deployment.md](../docs/deployment.md) for Vercel deployment.

Quick deploy:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel
```

## Performance

- Server-side rendering where beneficial
- Code splitting by route
- Image optimization (Next.js built-in)
- React Query caching

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### API Connection Issues

Check `NEXT_PUBLIC_API_URL` in `.env.local` and verify backend is running.

### Build Errors

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

### Type Errors

Make sure types in `src/types/index.ts` match backend schemas.

## Future Enhancements

- PDF viewer integration for citation highlighting
- Real-time collaboration
- Batch processing
- Custom field templates
- Analytics dashboard
