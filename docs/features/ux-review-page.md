# Lease Review Page - UX Improvements

## High Impact Improvements

### 1. **Keyboard Shortcuts**
Currently requires clicking Accept/Reject for each of 40+ fields. Add:
- `J/K` - Navigate to next/previous field
- `A` or `Space` - Accept current field
- `R` or `X` - Reject current field
- `E` - Start editing current field
- `Esc` - Cancel edit/close expanded details

### 2. **Smart Default: "Accept High Confidence"**
Add a button to "Accept All High Confidence (≥90%)" - this could auto-accept 80% of fields, leaving users to review only the uncertain ones. Much faster than Accept All → fix a few.

### 3. **Filter/Focus Mode**
Add tabs or filter buttons:
- "All Fields" (current view)
- "Needs Attention" (confidence < 70% or empty values)
- "Unreviewed" (no Accept/Reject decision yet)
- "Edited" (fields where user made changes)

This lets users focus on what matters instead of scrolling through 40 fields.

### 4. **Progress Indicator**
Replace the simple "X/Y reviewed" counter with:
- Visual progress bar
- Category-level completion (e.g., "Parties: 5/5 ✓, Financial: 3/8 ⚠️")
- Highlight unreviewed fields in yellow/orange

### 5. **Sticky Action Bar**
The "Submit Review" button is only at the top. When scrolling through fields, users lose context. Add:
- Floating action button in bottom-right with progress ring
- Or sticky footer showing progress + Submit button
- Include "X fields remaining" reminder

## Medium Impact Improvements

### 6. **Field Navigation Controls**
Add Previous/Next buttons at the top of the field panel:
```
[← Previous]  [Next →]  [Skip to Next Unreviewed]
```

### 7. **Collapsible Categories**
The category headers (Parties, Financial, etc.) could be collapsible accordions:
- Click to expand/collapse entire category
- Show completion status per category: "Financial (3/8 reviewed)"
- Start with low-confidence categories expanded

### 8. **Visual Confidence Hierarchy**
Currently all fields are visually equal. Improvements:
- Sort fields by confidence (low → high) within each category
- Add warning icon for < 50% confidence fields
- Dim or de-emphasize 95%+ confidence fields (likely correct)

### 9. **Undo/Redo**
Add undo/redo for Accept/Reject decisions:
- `Cmd+Z` / `Ctrl+Z` to undo
- Show toast: "Accepted 'Lease Term' (Undo)"
- Small undo button next to each reviewed field

### 10. **Better Empty State Handling** ✅ IMPLEMENTED
Fields with "Not found" (null/undefined values) need special treatment:
- Visual indicator: "Field not found in document"
- Quick action: "Mark as N/A" vs "This should exist"
- Different from low-confidence extractions

## Lower Impact / Nice-to-Haves

### 11. **Autosave Draft**
Currently lose all progress if page crashes. Save feedback to localStorage as users review.

### 12. **Citation Quick Preview**
Instead of expanding to see source quote:
- Show truncated quote below value (first 50 chars)
- Or tooltip on hover showing quote
- Current expand feels like too many clicks

### 13. **Bulk Edit Mode**
For similar fields (e.g., multiple rent amounts), allow:
- Select multiple fields (checkboxes)
- Apply same action to all selected
- Useful for patterns like "all dates are wrong"

### 14. **Required Field Indicators**
Schema has `required` boolean. Use it:
- Red asterisk (*) for required fields
- Warning if trying to submit with required field rejected/empty
- Priority sort: required fields first

### 15. **Mobile Layout**
50/50 split doesn't work on mobile. Detect narrow screens and:
- Stack PDF on top, fields below
- Or add toggle to switch between PDF/Fields view
- Currently probably unusable on phone

## Quick Wins (Easy to Implement)

1. **Remove duplicate Submit button** - The one at bottom of FieldReviewPanel doesn't work
2. **Add visual separator** - Horizontal line or spacing between field categories
3. **Hover state on rows** - Make it more obvious the row is clickable (already done with bg-gray-50)
4. **Show accepted/rejected count in categories** - "Parties (3 accepted, 1 rejected)"
5. **Add "Review Later" action** - Skip field without accepting/rejecting

## Most Impactful Quick Implementation

**"Accept All High Confidence + Focus on Low Confidence"**

Add two buttons in the header:
1. "Accept High Confidence (≥90%)" - Auto-accepts ~70-80% of fields
2. "Show Only Needs Review" - Filters to confidence < 90%

This would reduce a 40-field review from ~5 minutes of clicking to ~1 minute of reviewing the uncertain fields.

---

*Generated: 2026-02-02*
