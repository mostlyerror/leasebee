"""
Core test fixtures for the LeaseBee test suite.

This module provides shared fixtures used across all tests:
- test_db: PostgreSQL database for realistic testing
- client: FastAPI TestClient with test database and mocked external services
- mock_s3_client: Mocked boto3 S3 client (no real S3 calls)
- mock_claude_client: Mocked Anthropic client (no real API calls)
- sample_pdf_bytes: Generated test PDF content
- mock_extraction_response: Realistic Claude extraction response
"""
import json
import os
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import database first (no external service dependencies)
from app.core.database import Base, get_db

# Import all models to register them with Base.metadata
from app.models.lease import Lease  # noqa: F401
from app.models.extraction import Extraction  # noqa: F401
from app.models.field_correction import FieldCorrection  # noqa: F401
from app.models.citation_source import CitationSource  # noqa: F401
from app.models.extraction_feedback import ExtractionFeedback  # noqa: F401
from app.models.few_shot_example import FewShotExample  # noqa: F401

# Import app - note that we'll patch external services via session-scoped fixture
from app.main import app


# ============================================================================
# Session-scoped fixtures for external service mocking
# ============================================================================

# Global mocks for external services - applied when conftest is imported
from unittest.mock import MagicMock, patch
import sys

# Create S3 mock
_mock_s3_client = MagicMock()
_mock_s3_client.upload_fileobj.return_value = None
_mock_body = MagicMock()
_mock_body.read.return_value = b'%PDF-1.4\nfake pdf content'
_mock_s3_client.get_object.return_value = {'Body': _mock_body}
_mock_s3_client.delete_object.return_value = None
_mock_s3_client.generate_presigned_url.return_value = 'https://fake-s3-url.com/test.pdf'

# Apply boto3 patch BEFORE importing app modules
_boto3_patch = patch('boto3.client', return_value=_mock_s3_client)
_boto3_patch.start()

# Now import and recreate storage service
from app.services import storage_service as _storage_module
from app.services.storage_service import StorageService
_storage_module.storage_service = StorageService()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """
    Create a PostgreSQL test database for testing.

    Uses the main database but rolls back transactions after each test
    to ensure isolation. This matches production environment.

    Yields:
        SQLAlchemy database session
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    # Use the same database as production for realistic testing
    # but we'll use transaction rollback for test isolation
    engine = create_engine(settings.DATABASE_URL, echo=False)
    
    # Create session with autocommit disabled for rollback support
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine
    )
    
    # Create connection and start transaction
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create session bound to connection
    db = TestingSessionLocal(bind=connection)
    
    try:
        yield db
    finally:
        db.close()
        # Rollback transaction to clean up test data
        transaction.rollback()
        connection.close()
        engine.dispose()


# ============================================================================
# FastAPI Test Client
# ============================================================================

@pytest.fixture
def client(test_db, mock_s3_client, mock_claude_client):
    """
    FastAPI TestClient with test database and mocked external services.

    This fixture:
    - Overrides the database dependency to use test_db
    - Automatically applies S3 and Claude mocks
    - Cleans up dependency overrides after the test

    Args:
        test_db: Test database session
        mock_s3_client: Mocked S3 client
        mock_claude_client: Mocked Claude client

    Yields:
        FastAPI TestClient instance
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up dependency overrides
    app.dependency_overrides.clear()


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture
def mock_s3_client(mocker):
    """
    Mock boto3 S3 client to avoid real AWS calls.

    Mocks:
    - upload_fileobj: Returns None (success)
    - get_object: Returns fake PDF bytes
    - delete_object: Returns None (success)
    - generate_presigned_url: Returns fake URL

    Args:
        mocker: pytest-mock fixture

    Returns:
        Mocked boto3 S3 client
    """
    mock_client = mocker.MagicMock()

    # Mock upload_fileobj
    mock_client.upload_fileobj.return_value = None

    # Mock get_object
    fake_pdf_content = b'%PDF-1.4\n%fake pdf content for testing'
    mock_body = mocker.MagicMock()
    mock_body.read.return_value = fake_pdf_content
    mock_client.get_object.return_value = {'Body': mock_body}

    # Mock delete_object
    mock_client.delete_object.return_value = None

    # Mock generate_presigned_url
    mock_client.generate_presigned_url.return_value = "https://fake-s3-url.com/test.pdf"

    # Patch boto3.client
    mocker.patch('boto3.client', return_value=mock_client)
    
    # For integration tests: recreate the storage_service singleton with mock
    # Import here to avoid circular imports
    try:
        from app.services import storage_service as storage_module
        from app.services.storage_service import StorageService
        from app.core.config import settings
        
        # Create new instance with mocked boto3
        storage_module.storage_service = StorageService()
    except Exception:
        # Unit tests handle their own mocking
        pass

    return mock_client


@pytest.fixture
def mock_claude_client(mocker, mock_extraction_response):
    """
    Mock Anthropic Claude API client to avoid real API calls.

    This fixture creates a realistic mock that returns a complete
    extraction response with all expected fields.

    Args:
        mocker: pytest-mock fixture
        mock_extraction_response: Mock extraction data

    Returns:
        Mocked Anthropic client
    """
    # Create mock response object
    mock_response = mocker.MagicMock()

    # Mock the content attribute (list of content blocks)
    mock_content_block = mocker.MagicMock()
    mock_content_block.text = json.dumps(mock_extraction_response)
    mock_response.content = [mock_content_block]

    # Mock usage tokens
    mock_usage = mocker.MagicMock()
    mock_usage.input_tokens = 5000
    mock_usage.output_tokens = 2000
    mock_response.usage = mock_usage

    # Mock model version
    mock_response.model = "claude-3-5-sonnet-20241022"

    # Create mock client
    mock_client = mocker.MagicMock()
    mock_client.messages.create.return_value = mock_response

    # Patch Anthropic client in the service module
    mocker.patch('app.services.claude_service.Anthropic', return_value=mock_client)

    return mock_client


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_pdf_bytes():
    """
    Generate minimal valid PDF bytes for testing.

    Creates a simple PDF with fake lease content.
    For more realistic testing, use the actual sample_lease.pdf file.

    Returns:
        bytes: Minimal valid PDF content
    """
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 85
>>
stream
BT
/F1 12 Tf
100 700 Td
(LEASE AGREEMENT) Tj
0 -20 Td
(Tenant: Acme Corporation) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
451
%%EOF
"""
    return pdf_content


@pytest.fixture
def mock_extraction_response():
    """
    Realistic mock extraction response from Claude API.

    This represents the JSON structure that Claude returns
    after extracting data from a lease document.

    Returns:
        dict: Complete extraction response with all expected fields
    """
    return {
        "extractions": {
            # Tenant Information
            "tenant.name": "Acme Corporation",
            "tenant.address": "123 Business Park, Suite 100",
            "tenant.city": "San Francisco",
            "tenant.state": "CA",
            "tenant.zip": "94105",

            # Landlord Information
            "landlord.name": "Property Management LLC",
            "landlord.address": "456 Commercial Plaza",
            "landlord.city": "San Francisco",
            "landlord.state": "CA",
            "landlord.zip": "94102",

            # Property Information
            "property.address": "789 Office Boulevard, Suite 200",
            "property.city": "San Francisco",
            "property.state": "CA",
            "property.zip": "94103",
            "property.square_feet": "5000",
            "property.type": "Office",

            # Financial Terms
            "financial.base_rent": "15000.00",
            "financial.rent_frequency": "Monthly",
            "financial.security_deposit": "30000.00",
            "financial.rent_escalation": "3% annually",

            # Lease Terms
            "lease_terms.start_date": "2024-01-01",
            "lease_terms.end_date": "2026-12-31",
            "lease_terms.term_length": "36 months",
            "lease_terms.renewal_option": "Two 12-month options",

            # Special Provisions
            "special_provisions.parking_spaces": "10",
            "special_provisions.utilities_included": "Water and sewer",
            "special_provisions.maintenance_responsibility": "Landlord handles exterior, tenant handles interior",
        },
        "reasoning": {
            "tenant.name": "Found in header section of first page",
            "financial.base_rent": "Explicitly stated in Section 4: Rent",
            "lease_terms.start_date": "Commencement date in Section 2",
            "lease_terms.end_date": "Expiration date calculated from 36-month term",
        },
        "citations": {
            "tenant.name": {
                "page": 1,
                "quote": "This Lease Agreement is entered into by and between Property Management LLC ('Landlord') and Acme Corporation ('Tenant')"
            },
            "financial.base_rent": {
                "page": 2,
                "quote": "Tenant shall pay Base Rent of Fifteen Thousand Dollars ($15,000.00) per month"
            },
            "lease_terms.start_date": {
                "page": 1,
                "quote": "The Lease Term shall commence on January 1, 2024"
            },
        },
        "confidence": {
            "tenant.name": 0.98,
            "tenant.address": 0.95,
            "landlord.name": 0.97,
            "property.address": 0.99,
            "financial.base_rent": 0.99,
            "lease_terms.start_date": 0.99,
            "lease_terms.end_date": 0.95,
            "property.square_feet": 0.92,
        }
    }


@pytest.fixture
def sample_lease_pdf_path():
    """
    Path to the sample lease PDF file in fixtures directory.

    Returns:
        Path: Path to sample_lease.pdf
    """
    fixtures_dir = Path(__file__).parent / "fixtures"
    return fixtures_dir / "sample_lease.pdf"


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_uuid(mocker):
    """
    Mock UUID generation for predictable filenames in tests.

    Returns:
        str: Fixed UUID string for testing
    """
    fixed_uuid = "test-uuid-12345678"
    mocker.patch('uuid.uuid4', return_value=mocker.MagicMock(hex=fixed_uuid))
    return fixed_uuid


@pytest.fixture(autouse=True)
def set_test_env_vars(monkeypatch):
    """
    Automatically set test environment variables for all tests.

    This fixture runs automatically before each test to ensure
    test-specific configuration is used.
    
    Note: DATABASE_URL uses production database but transactions are rolled back
    after each test for isolation.
    """
    # Set test environment variables (keep existing DATABASE_URL from .env)
    monkeypatch.setenv("AWS_S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("ENVIRONMENT", "test")


# ============================================================================
# Async Fixtures (if needed for async tests)
# ============================================================================

@pytest.fixture
async def async_client(test_db, mock_s3_client, mock_claude_client):
    """
    Async FastAPI TestClient for async endpoint testing.

    Similar to the sync client fixture but for async tests.
    Currently not used, but available for future async testing needs.
    """
    from httpx import AsyncClient

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
