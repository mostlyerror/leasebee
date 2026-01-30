# Quick Start: Accuracy Testing

This guide will help you quickly measure extraction accuracy improvements.

---

## Prerequisites

1. **API Key**: Ensure `ANTHROPIC_API_KEY` is set in your environment
2. **Database**: Migrations applied (run `alembic upgrade head` if needed)
3. **Test PDFs**: 5-20 sample lease PDFs

---

## Step 1: Prepare Test Data (30-60 minutes)

### A. Add Your Test PDFs
```bash
# Copy your sample lease PDFs to the test directory
cp ~/path/to/your/leases/*.pdf backend/tests/fixtures/test_leases/
```

### B. Create Manual "Gold Standard" Extractions

Edit `/backend/tests/fixtures/test_leases/gold_standard.json`:

```json
{
  "leases": [
    {
      "lease_id": "your_lease_001",
      "filename": "your_actual_filename.pdf",
      "description": "Brief description of this lease",
      "gold_standard": {
        "basic_info.lease_type": "Office",
        "parties.landlord_name": "ABC Properties LLC",
        "parties.tenant_name": "XYZ Company Inc",
        "property.address": "123 Main St, San Francisco, CA 94105",
        "property.rentable_area": "5000",
        "dates.commencement_date": "2024-01-15",
        "dates.expiration_date": "2029-01-14",
        "rent.base_rent_monthly": "15000.00",
        ...
      }
    }
  ]
}
```

**Important Format Rules:**
- Dates: `"YYYY-MM-DD"` (ISO format)
- Currency: `"15000.00"` (numeric with 2 decimals, no $ or commas)
- Areas: `"5000"` (numeric only, no "SF")
- Percentages: `"0.125"` (decimal, not "12.5%")
- Nulls: Use `null` (not `""` or `"N/A"`)

---

## Step 2: Run Baseline Test (5-10 minutes)

```bash
cd backend

# Activate virtual environment if needed
source venv/bin/activate  # or: .venv/bin/activate

# Install test dependencies
pip install pytest

# Run accuracy test
pytest tests/accuracy/test_extraction_accuracy.py::TestExtractionAccuracy::test_baseline_accuracy -v -s
```

**What This Does:**
- Extracts each test PDF using the improved system
- Compares results with your gold standard
- Saves detailed results to `tests/accuracy/baseline_results.json`

---

## Step 3: Generate Report (30 seconds)

```bash
cd backend/tests/accuracy

# Generate human-readable report
python accuracy_report.py baseline_results.json baseline_report.txt

# View the report
cat baseline_report.txt
```

**Report Includes:**
- Overall accuracy percentage
- Per-lease breakdown
- Accuracy by field category (dates, rent, property, etc.)
- Top 10 most problematic fields
- Confidence score analysis
- Cost analysis

---

## Step 4: Review Results

### Understanding the Output

#### Overall Accuracy
```
Overall Accuracy:  78.50%
Total Fields:      200
Correct:           157
Incorrect:         28
Missing:           15
```

**Target**: 75-85% overall accuracy

#### Field Category Accuracy
```
ACCURACY BY FIELD CATEGORY
Category                       Correct      Total    Accuracy
dates                               18         20      90.00%
rent                                16         20      80.00%
parties                             19         20      95.00%
property                            17         20      85.00%
```

**Look For**:
- Categories below 70% need attention
- Dates, currency, areas should be 85%+

#### Problematic Fields
```
TOP 10 MOST PROBLEMATIC FIELDS
1. rent.rent_escalations
   Errors: 8
   Examples:
     - test_lease_001: incorrect
       Expected: 3% annually beginning year 2
       Got: 3 percent annual increase starting year two
```

**Action**:
- Review extraction reasoning for these fields
- Check if validation warnings indicate format issues
- Consider adding field-specific examples

#### Cost Analysis
```
Total Cost:                $1.6524
Average Cost per Lease:    $0.3305
Cost per Accurate Field:   $0.0105
```

**Expected**:
- Single-pass: ~$0.24 per lease
- Multi-pass: ~$0.30-0.35 per lease
- Cost per accurate field: ~$0.01

---

## Step 5: Investigate Issues (If Needed)

### Check Individual Field Results

Open `baseline_results.json` and look for:

```json
{
  "lease_id": "test_lease_001",
  "metrics": {
    "field_results": {
      "dates.commencement_date": {
        "status": "correct",
        "expected": "2024-01-15",
        "actual": "2024-01-15",
        "confidence": 0.98,
        "reason": "Exact match"
      },
      "rent.base_rent_monthly": {
        "status": "incorrect",
        "expected": "15000.00",
        "actual": "15000",
        "confidence": 0.95,
        "reason": "Numeric mismatch (diff: 0.0, expected: 15000.00, got: 15000)"
      }
    }
  }
}
```

### Check Validation Warnings

Look in the database or logs for validation warnings:
- Format normalization issues
- Cross-field inconsistencies
- Range violations

### Review Multi-Pass Results

Check if multi-pass refinement helped:
```json
{
  "metadata": {
    "multi_pass": true,
    "refined_fields": ["rent.rent_escalations", "dates.rent_commencement_date"],
    "refinement_improvements": {
      "rent.rent_escalations": {
        "initial_confidence": 0.65,
        "focused_confidence": 0.88,
        "improvement": 0.23
      }
    }
  }
}
```

---

## Common Issues & Solutions

### Issue: Low Overall Accuracy (< 70%)

**Possible Causes:**
1. Gold standard format doesn't match extraction format
   - **Solution**: Review format rules (dates as YYYY-MM-DD, currency as numeric)
2. PDFs are poor quality (scanned, handwritten)
   - **Solution**: Test with cleaner PDFs first
3. Lease structures are non-standard
   - **Solution**: Add field-specific examples to prompt

### Issue: High Cost (> $0.50 per lease)

**Possible Causes:**
1. Too many fields triggering multi-pass
   - **Solution**: Increase confidence threshold or disable multi-pass
2. Large PDF file sizes
   - **Solution**: Optimize PDFs, remove unnecessary pages

### Issue: Specific Field Type Always Wrong

**Examples:**
- Dates always in wrong format → Check date parsing in validation_service.py
- Currency always missing decimals → Review currency normalization
- Addresses include suite in main field → Check address validation warnings

**Solution**:
1. Review `_get_field_type_guidance()` in claude_service.py
2. Add more specific examples
3. Adjust validation rules

---

## Next Actions Based on Results

### If Accuracy is 75-85%+ ✅
**Success!** You've achieved the target improvement.

**Next Steps:**
1. Deploy to production with `use_multi_pass=True`
2. Monitor ongoing accuracy with real leases
3. Build analytics dashboard (Week 2-3 plan)

### If Accuracy is 70-75% ⚠️
**Good progress**, but room for improvement.

**Next Steps:**
1. Review problematic fields
2. Add field-specific few-shot examples
3. Adjust confidence threshold for multi-pass
4. Consider field-specific extractors for complex terms

### If Accuracy is < 70% ❌
**Needs investigation**.

**Next Steps:**
1. Verify gold standard format is correct
2. Check test PDFs are readable and standard format
3. Review extraction reasoning in results
4. Consider document preprocessing (OCR, cleaning)

---

## Measuring Improvement Over Time

### Compare Baseline to Improved

After making changes, run tests again:

```bash
# Run with improvements
pytest tests/accuracy/test_extraction_accuracy.py -v -s

# This creates a new results file with timestamp
# Rename it for comparison
mv tests/accuracy/baseline_results.json tests/accuracy/improved_results.json

# Run original baseline again if needed
# (Make sure to revert changes temporarily)

# Compare
python accuracy_report.py --compare \
  baseline_results.json \
  improved_results.json \
  comparison_report.txt
```

### Comparison Report Shows:
```
BASELINE vs IMPROVED COMPARISON
Metric                         Baseline        Improved          Change
Overall Accuracy                  68.50%          81.00%        +12.50%
Correct Fields                       137             162            +25
Total Cost                      $1.2000         $1.6500        +37.50%

Accuracy Improvement: 12.50 percentage points
Cost Increase: $0.45 (37.50%)
ROI: 27.78 accuracy points per dollar spent
```

---

## Tips for Success

1. **Start Small**: Test with 5 leases first, then expand to 20
2. **Use Clean PDFs**: Born-digital PDFs work better than scanned documents
3. **Diverse Test Set**: Include different lease types (office, retail, industrial)
4. **Accurate Gold Standard**: Double-check your manual extractions
5. **Review Reasoning**: Extraction reasoning helps understand why fields were missed
6. **Monitor Costs**: Track token usage to understand cost drivers

---

## Support

If you encounter issues:

1. **Check logs** for error messages
2. **Review validation warnings** in extraction metadata
3. **Examine extraction reasoning** for problematic fields
4. **Verify API key** is valid and has credits
5. **Consult main documentation**: `/docs/accuracy_improvements.md`

---

**Ready to Start?** Go to Step 1 and prepare your test data!
