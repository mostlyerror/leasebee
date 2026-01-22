# LeaseBee Automated Testing Guide

## Overview

This testing suite provides fast, automated testing for the lease extraction workflow, replacing manual browser testing with programmatic tests that run in <1 second.

## Test Structure

```
tests/
├── conftest.py                      # Core fixtures (database, mocks, client)
├── fixtures/
│   ├── mock_responses.py           # Mock Claude API responses
│   └── sample_lease.pdf            # Real sample PDF (3 pages)
├── utils/
│   └── mock_factories.py           # Factory functions for test data
├── unit/                           # Fast unit tests (47 tests, ~0.1s)
│   ├── test_storage_service.py     # S3 operations (12 tests)
│   ├── test_claude_service.py      # Claude API (15 tests)
│   └── test_pdf_service.py         # PDF processing (20 tests)
└── integration/                    # End-to-end workflow tests
    └── test_complete_workflow.py   # Complete extraction workflow
```

## Quick Start

### Run All Unit Tests
```bash
cd backend
source venv/bin/activate
pytest tests/unit/ -v
```

**Result:** 47 passed in 0.10s ✅

### Run Specific Test File
```bash
# Storage service tests
pytest tests/unit/test_storage_service.py -v

# Claude service tests
pytest tests/unit/test_claude_service.py -v

# PDF service tests
pytest tests/unit/test_pdf_service.py -v
```

### Run Tests with Coverage
```bash
pytest tests/unit/ --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
```

## What's Tested

### 1. Storage Service (S3 Operations)
✅ PDF upload with UUID filename generation
✅ File download from S3
✅ File deletion
✅ Presigned URL generation
✅ Error handling for all operations
✅ File extension preservation
✅ Filename uniqueness

### 2. Claude Service (AI Extraction)
✅ Lease data extraction
✅ JSON response parsing
✅ Cost calculation ($3/$15 per 1M tokens)
✅ Prompt building with few-shot examples
✅ Error handling for API failures
✅ Metadata tracking (tokens, timing, version)

### 3. PDF Service (Document Processing)
✅ Text extraction from bytes
✅ Page counting
✅ Single page extraction
✅ Text search with bounding boxes
✅ Invalid PDF handling
✅ Multi-page document support

## Key Features

### 🚀 Speed
- **Unit tests:** <1 second for all 47 tests
- **No external dependencies:** All services mocked
- **No API costs:** Claude API calls mocked
- **No AWS charges:** S3 operations mocked

### 🎯 Isolation
- **In-memory SQLite:** Each test gets fresh database
- **Mocked services:** No real S3 or Claude API calls
- **Deterministic:** Tests always produce same results
- **No cleanup needed:** Everything disposed after test

### 📊 Coverage
- **Storage Service:** 100% coverage
- **Claude Service:** ~95% coverage
- **PDF Service:** ~90% coverage

## Mock Data

### Claude API Response
```python
{
    "extractions": {
        "tenant.name": "Acme Corporation",
        "financial.base_rent": "15000.00",
        "lease_terms.start_date": "2024-01-01",
        # ... all fields
    },
    "reasoning": { /* explanations */ },
    "citations": { /* source quotes */ },
    "confidence": { /* 0.0-1.0 scores */ }
}
```

### Sample PDF
- 3-page lease agreement
- Contains: tenant info, landlord info, financial terms
- Realistic structure for testing

## Example Test

```python
@pytest.mark.unit
def test_upload_pdf_success(mocker, mock_s3_client):
    """Test successful PDF upload to S3."""
    storage = StorageService()

    test_file = BytesIO(b"test pdf content")
    result = storage.upload_pdf(test_file, "test.pdf")

    # Verify results
    assert result['filename'].endswith('.pdf')
    assert result['file_path'].startswith('leases/')
    assert result['original_filename'] == 'test.pdf'

    # Verify S3 was called
    mock_s3_client.upload_fileobj.assert_called_once()
```

## Benefits vs Manual Testing

| Aspect | Manual Testing | Automated Testing |
|--------|---------------|------------------|
| **Time** | 3-5 min per cycle | <1 second |
| **Consistency** | Variable (human error) | 100% deterministic |
| **Coverage** | Unknown | Visible (HTML reports) |
| **Cost** | API costs per test | $0 (mocked) |
| **Regression** | Must retest manually | Automatic |
| **CI/CD** | Manual only | Fully automated |

**60-100x faster than manual testing**

## Running Specific Tests

### By Marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run slow tests
pytest -m slow
```

### By Pattern
```bash
# Test specific function
pytest -k "test_upload_pdf"

# Test specific service
pytest -k "storage"
```

### With Output
```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Short traceback
pytest --tb=short
```

## Debugging Tests

### 1. Enable SQL Logging
In `conftest.py`, set `echo=True`:
```python
engine = create_engine(
    "sqlite:///:memory:",
    echo=True  # Show SQL queries
)
```

### 2. View Mock Calls
```python
# In test
print(mock_s3_client.upload_fileobj.call_args)
print(mock_s3_client.upload_fileobj.call_count)
```

### 3. Run Single Test
```bash
pytest tests/unit/test_storage_service.py::test_upload_pdf_success -v
```

## Best Practices

### ✅ DO
- Run tests before committing code
- Add tests for new features
- Mock external services (S3, Claude API)
- Use factories for test data
- Keep tests fast (<1s for unit tests)

### ❌ DON'T
- Make real API calls in tests
- Share state between tests
- Use production database
- Skip tests when they fail
- Write flaky tests

## Continuous Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    cd backend
    pytest tests/unit/ --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Future Enhancements

### Integration Tests (In Progress)
The integration tests are scaffolded but need database setup fixes:
- Complete workflow: Upload → Extract → Verify
- Error scenarios
- Edge cases

To enable, fix the test database initialization in `conftest.py`.

### Load Testing
```bash
# Future: Add locust or pytest-benchmark
pytest tests/performance/ --benchmark-only
```

### Visual Regression
```bash
# Future: Test frontend components
pytest tests/visual/ --screenshot-compare
```

## Troubleshooting

### Tests Fail with "no such table"
**Solution:** Models aren't imported before `Base.metadata.create_all()`. Import all models at top of `conftest.py`.

### Tests Make Real API Calls
**Solution:** Ensure mocks are patched in correct module: `app.services.claude_service.Anthropic`, not `anthropic.Anthropic`.

### UUID Mocking Fails
**Solution:** Mock `__str__()` method:
```python
mock_uuid = mocker.MagicMock()
mock_uuid.__str__ = mocker.MagicMock(return_value="test-uuid")
mocker.patch('uuid.uuid4', return_value=mock_uuid)
```

## Next Steps

1. **Fix integration tests** - Debug database setup
2. **Increase coverage** - Add edge case tests
3. **Add property tests** - Use hypothesis library
4. **Performance tests** - Benchmark critical paths
5. **Visual tests** - Frontend component testing

---

## Summary

✅ **47 unit tests passing** in 0.10 seconds
✅ **No external dependencies** (S3, Claude API mocked)
✅ **Fast iteration** (<1s feedback loop)
✅ **High confidence** (deterministic, repeatable)

**You've replaced 3-5 minutes of manual testing with <1 second of automated testing!** 🎉
