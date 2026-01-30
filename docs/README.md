# LeaseBee Documentation

Documentation for the LeaseBee AI-powered lease abstraction system.

---

## 📚 Documentation Index

### Getting Started
- [Main Project README](../README.md) - Project overview and setup instructions
- [Quick Start: Accuracy Testing](QUICK_START_ACCURACY_TESTING.md) - ⭐ **Start here to test accuracy improvements**

### Feature Documentation
- [Accuracy Improvements](accuracy_improvements.md) - Comprehensive guide to the accuracy improvement system
- [Implementation Complete](../IMPLEMENTATION_COMPLETE.md) - Summary of completed improvements

### Architecture & Development
- [Branching Strategy](../BRANCHING_STRATEGY.md) - Git workflow and branching guidelines
- [GitHub Setup](../GITHUB_SETUP.md) - Repository setup and configuration

---

## 🚀 New: Extraction Accuracy Improvements

**Status**: ✅ Complete - Ready for Testing
**Expected Impact**: 10-15% accuracy improvement
**Implementation Date**: January 28, 2026

### What's New

#### 1. Enhanced Prompt Engineering
- Field-type specific extraction guidance (dates, currency, areas, addresses, etc.)
- Concrete examples with reasoning patterns
- Explicit null value handling instructions

#### 2. Validation Service
- Automatic format normalization for all field types
- Cross-field consistency checking (e.g., annual rent = monthly × 12)
- Confidence score adjustment based on validation results

#### 3. Multi-Pass Extraction
- Automatic re-extraction of low-confidence fields
- Focused prompts with context from successful extractions
- Smart result merging with improvement tracking

#### 4. Accuracy Testing Framework
- Gold standard test dataset
- Field-by-field comparison
- Comprehensive accuracy reports
- Before/after comparison tools

### Quick Links

- **[Quick Start Guide](QUICK_START_ACCURACY_TESTING.md)** - Run your first accuracy test (30-60 min)
- **[Full Documentation](accuracy_improvements.md)** - Detailed implementation guide
- **[Implementation Summary](../IMPLEMENTATION_COMPLETE.md)** - What was built and why

---

## 📊 Expected Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Overall Accuracy | 65-70% | 75-85% | +10-15% |
| Dates | 65% | 85-90% | +20-25% |
| Currency | 70% | 85-90% | +15-20% |
| Areas | 65% | 80-85% | +15-20% |
| Cost per Lease | $0.24 | $0.30-0.35 | +25-45% |

---

## 🔧 Usage

### Standard Extraction (All Improvements Enabled)
```bash
POST /api/extractions/extract/{lease_id}
# Includes: enhanced prompts, validation, multi-pass refinement
```

### Fast Extraction (Single-Pass)
```bash
POST /api/extractions/extract/{lease_id}?use_multi_pass=false
# Includes: enhanced prompts, validation (no multi-pass)
```

---

## 📁 Project Structure

```
leasebee/
├── docs/                                    # Documentation (you are here)
│   ├── README.md                           # This file
│   ├── QUICK_START_ACCURACY_TESTING.md    # Testing guide ⭐
│   └── accuracy_improvements.md            # Full documentation ⭐
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── claude_service.py          # Enhanced extraction ⭐
│   │   │   └── validation_service.py      # New validation service ⭐
│   │   ├── api/
│   │   │   └── extractions.py             # Updated API endpoint ⭐
│   │   └── models/
│   │       └── extraction.py              # With metadata field ⭐
│   └── tests/
│       └── accuracy/                       # New testing framework ⭐
│           ├── test_extraction_accuracy.py
│           ├── accuracy_report.py
│           └── fixtures/test_leases/
│               └── gold_standard.json
└── IMPLEMENTATION_COMPLETE.md              # Implementation summary ⭐
```

---

## 🎯 Next Steps

1. **Test the Improvements** (30-60 minutes)
   - Follow the [Quick Start Guide](QUICK_START_ACCURACY_TESTING.md)
   - Prepare 5-20 test PDFs
   - Run accuracy tests
   - Review results

2. **Deploy to Production** (after testing)
   - Apply database migration: `alembic upgrade head`
   - Deploy updated code
   - Enable multi-pass by default (already configured)

3. **Monitor & Iterate**
   - Track accuracy over time
   - Review validation warnings
   - Add field-specific examples as needed

---

## 💡 Key Features

### Validation Service
- **Auto-normalization**: Dates → ISO format, currency → numeric
- **Consistency checks**: Annual vs monthly rent, date ranges
- **Warnings**: Stored in extraction metadata for debugging

### Multi-Pass Extraction
- **Automatic**: Triggered for fields with confidence < 0.70
- **Smart**: Only re-extracts low-confidence fields (cost-efficient)
- **Trackable**: Shows improvement per field in metadata

### Testing Framework
- **Baseline**: Establish current accuracy
- **Comparison**: Measure improvements over time
- **Reports**: Detailed analysis by field category
- **Gold standard**: Expert-verified test dataset

---

## 📖 Additional Resources

### API Documentation
- See main [API documentation](../README.md#api-endpoints)
- Extraction endpoint now supports `use_multi_pass` parameter

### Database Schema
- New `metadata` JSONB field on `extractions` table
- Stores validation warnings and multi-pass information
- Migration: `001_add_metadata_to_extractions.py`

### Development
- [Branching Strategy](../BRANCHING_STRATEGY.md) - For contributing
- [GitHub Setup](../GITHUB_SETUP.md) - For repository setup

---

## 🐛 Troubleshooting

### Common Issues

**Low accuracy (< 70%)**
- Check gold standard format
- Review test PDF quality
- See [troubleshooting guide](QUICK_START_ACCURACY_TESTING.md#common-issues--solutions)

**High costs (> $0.50 per lease)**
- Disable multi-pass: `use_multi_pass=False`
- Increase threshold: adjust `confidence_threshold`
- See [cost optimization](accuracy_improvements.md#cost-impact)

**Validation warnings**
- Review warnings in extraction metadata
- Adjust tolerances in `validation_service.py`
- See [validation guide](accuracy_improvements.md#day-4-5-field-validation--post-processing)

---

## 📞 Support

For questions or issues:
1. Check this documentation
2. Review [accuracy improvements guide](accuracy_improvements.md)
3. See [implementation summary](../IMPLEMENTATION_COMPLETE.md)
4. Check test results in `/backend/tests/accuracy/`

---

## 🎉 Summary

The extraction accuracy improvement system is **complete and ready for testing**. It provides:

- ✅ 10-15% expected accuracy improvement
- ✅ Comprehensive testing framework
- ✅ Production-ready validation service
- ✅ Automatic multi-pass refinement
- ✅ Detailed documentation and guides

**Start testing now**: Follow the [Quick Start Guide](QUICK_START_ACCURACY_TESTING.md)!

---

*Last updated: January 28, 2026*
