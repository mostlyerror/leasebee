# Current Status - Accuracy Dashboard & Data Gitignore Fix

## What was done
All 5 steps of the plan are complete:

1. **`.gitignore`** - Changed from blanket `data/` to selective ignores (`data/leases/`, `data/abstracts/`, `data/baseline_results.json`). Tracking data (accuracy_history, gold_standard, runs/) now visible to git.

2. **`backend/app/api/analytics.py`** - Added two new endpoints:
   - `GET /api/analytics/accuracy-history` - reads `data/accuracy_history.json`
   - `GET /api/analytics/accuracy-run/{run_id}` - reads from `data/runs/`

3. **`frontend/src/lib/api.ts`** - Added `analyticsApi` export with `getMetrics`, `getFieldStats`, `getInsights`, `getAccuracyHistory`, `getAccuracyRun`.

4. **`frontend/package.json`** - Installed `recharts`.

5. **`frontend/src/app/(app)/analytics/page.tsx`** - Replaced "Coming Soon" card with full Model Accuracy section: summary cards, line chart (accuracy over time), per-field horizontal bar chart, per-lease breakdown table.

## What's NOT done yet
- Haven't started backend or frontend to visually verify
- Haven't committed anything
- Pre-existing build error: `@/components/leases/LeaseList` missing (unrelated to our work)
- Pre-existing TS errors in `api.ts`: `User`, `TypeExtraction`, `FieldDefinition` not imported (unrelated)

## Files modified
- `.gitignore`
- `backend/app/api/analytics.py`
- `frontend/src/lib/api.ts`
- `frontend/package.json` + `package-lock.json`
- `frontend/src/app/(app)/analytics/page.tsx`
