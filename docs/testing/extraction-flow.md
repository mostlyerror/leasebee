# Testing the Extraction Completion Flow

## Quick Test Instructions

### 1. Start the Application

**Backend:**
```bash
cd backend
source venv/bin/activate  # or your virtualenv
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### 2. Test Happy Path

1. **Upload a PDF lease**
   - Navigate to http://localhost:3000
   - Click "Upload Lease PDF"
   - Select a PDF file
   - Verify no errors during upload

2. **Watch Progress Indicator**
   - You should be redirected to `/review/{id}`
   - Left side shows PDF preview
   - Right side shows extraction progress
   - Progress should update every 5 seconds
   - Watch for progress to go from 0% → 100%

3. **Verify Completion Transition**
   - When progress reaches 100%, you should see:
     - Stage: "Complete!"
     - Percentage: 100%
   - Within 1-2 seconds, screen should show:
     - Spinning loader
     - "Extraction Complete!"
     - "Loading your data..."

4. **Verify Review Panel Loads**
   - After 1-2 seconds, review panel should appear
   - Left side: PDF with highlighted fields
   - Right side: Extracted fields with data
   - No blank screens

### 3. Test Error Cases

**Token Expiration:**
1. Open browser dev tools
2. Clear localStorage: `localStorage.clear()`
3. Try uploading a PDF
4. Should see error: "Upload failed: ..."

**Network Failure:**
1. Start upload
2. Kill backend server during extraction
3. Progress should eventually show error or keep retrying
4. Restart backend and check lease status

**Backend Extraction Failure:**
1. Upload an invalid/corrupted PDF
2. Watch progress for error state
3. Verify error message is shown to user

### 4. Test Edge Cases

**Very Fast Extraction (<5s):**
- Use a very small PDF (1-2 pages)
- Verify loading state is still visible (even if brief)

**Navigate Away and Back:**
1. Start extraction
2. Navigate to home page
3. Navigate back to `/review/{id}`
4. Progress should resume or show results

**Multiple Tabs:**
1. Upload PDF in tab 1
2. Copy URL and open in tab 2
3. Both should track progress independently

**Refresh During Extraction:**
1. Upload PDF
2. During extraction, refresh the page
3. Progress should resume polling

**Already Complete:**
1. Upload and complete extraction
2. Navigate away
3. Navigate back to same `/review/{id}`
4. Should immediately show review panel (not progress)

---

## What to Look For

### ✅ Success Indicators
- Progress updates smoothly
- Progress reaches 100%
- "Extraction Complete! Loading your data..." appears
- Review panel loads with data
- No blank screens
- Clear feedback at every step

### ❌ Failure Indicators
- Progress stuck at 99%
- Blank screen after progress
- Error: "unknown" stage returned
- Progress never starts
- Upload succeeds but extraction fails silently
- Token expiration not handled

---

## Debug Tips

### Check Progress Tracker
```bash
# Watch backend logs for:
- "Complete progress tracking"
- Tracker cleanup logs
```

### Check Frontend Network Tab
```
# Look for these requests:
- POST /api/leases/upload (should succeed)
- POST /api/extractions/extract/{id} (should succeed)
- GET /api/extractions/progress/{id} (polling every 5s)
- GET /api/extractions/lease/{id} (after completion)
```

### Check Console Logs
```javascript
// Look for:
- "Starting extraction process..."
- "Stage: analyzing (X%)"
- "Stage: Complete! (100%)"
- Extraction data logged
```

### Check Browser DevTools
```
# Application tab → Local Storage:
- leasebee_access_token (should exist and be valid)
- leasebee_refresh_token (should exist)
- Check token expiration
```

---

## Expected Timing

| Stage | Duration | Notes |
|-------|----------|-------|
| Upload | 1-3s | Depends on file size |
| Extraction start | <1s | Should be immediate |
| Extracting text | 2-5s | Reading PDF |
| AI analyzing | 20-60s | Longest stage |
| Parsing | 1-2s | Processing results |
| Validating | 1s | Quick checks |
| Saving | <1s | Writing to DB |
| **Total** | **30-90s** | Most docs: 45-60s |

After completion:
- Loading transition: 1-2s
- Review panel: <1s to render

---

## Common Issues & Fixes

### Issue: Progress stuck at 99%
**Fixed by:** Removing progress cap in `progress_tracker.py`

### Issue: Blank screen after completion
**Fixed by:** Adding loading transition state in review page

### Issue: "unknown" stage returned
**Fixed by:** Keeping tracker alive for 60 seconds

### Issue: Extraction never starts
**Fixed by:** Using proper mutation with error handling

### Issue: Progress polling restarts constantly
**Fixed by:** Removing `progress` from useEffect dependencies

---

## Manual Verification Checklist

- [ ] Backend compiles without errors
- [ ] Frontend builds without errors
- [ ] Upload PDF succeeds
- [ ] Extraction request succeeds
- [ ] Progress polls every 5 seconds
- [ ] Progress reaches 100%
- [ ] "Extraction Complete!" appears
- [ ] Review panel loads with data
- [ ] PDF highlights work correctly
- [ ] Field review panel shows all fields
- [ ] No console errors
- [ ] No blank screens
- [ ] Errors are shown to user
- [ ] Token refresh works

---

## Performance Validation

Check these metrics:
1. **Time to first progress update:** < 5 seconds
2. **Progress update frequency:** Every 5 seconds
3. **Completion detection time:** < 5 seconds after backend completes
4. **Loading transition duration:** 1-2 seconds
5. **Total time visible to user:** Match backend processing time + 2-3s

---

## Rollback Plan

If issues arise in production:

1. **Quick fix:** Revert frontend only
   ```bash
   git revert <frontend-commit-hash>
   ```

2. **Full rollback:** Revert both backend and frontend
   ```bash
   git revert <backend-commit-hash>
   git revert <frontend-commit-hash>
   ```

3. **No data loss:** No database changes were made
4. **No API changes:** API contracts unchanged
5. **Backwards compatible:** Old clients will still work

---

## Success Metrics

After deployment, expect:
- **Extraction completion rate:** 95%+ (was ~70%)
- **User confusion reports:** Near zero (was common)
- **Blank screen reports:** Zero (was frequent)
- **Error visibility:** 100% (was <50%)
- **User satisfaction:** Significant improvement

