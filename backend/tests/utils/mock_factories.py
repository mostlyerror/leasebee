"""
Factory functions for creating test objects.

These factories reduce code duplication across tests by providing
standardized ways to create database objects with sensible defaults
that can be overridden as needed.
"""
from datetime import datetime
from typing import Optional

from app.models.lease import Lease, LeaseStatus
from app.models.extraction import Extraction


def create_mock_lease(
    db,
    filename: str = "test-lease.pdf",
    original_filename: str = "test.pdf",
    file_size: int = 1024,
    file_path: str = "test-uuid-12345678.pdf",
    status: LeaseStatus = LeaseStatus.UPLOADED,
    page_count: Optional[int] = 3,
    **kwargs
) -> Lease:
    """
    Create a mock Lease object in the database.

    Args:
        db: Database session
        filename: Stored filename (usually UUID-based)
        original_filename: User's original filename
        file_size: File size in bytes
        file_path: S3 key or local path
        status: Lease processing status
        page_count: Number of pages in PDF
        **kwargs: Additional fields to override

    Returns:
        Created Lease object

    Example:
        lease = create_mock_lease(
            db,
            status=LeaseStatus.COMPLETED,
            page_count=10
        )
    """
    lease_data = {
        "filename": filename,
        "original_filename": original_filename,
        "file_size": file_size,
        "file_path": file_path,
        "content_type": "application/pdf",
        "status": status,
        "page_count": page_count,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # Override with any provided kwargs
    lease_data.update(kwargs)

    lease = Lease(**lease_data)
    db.add(lease)
    db.commit()
    db.refresh(lease)

    return lease


def create_mock_extraction(
    db,
    lease_id: int,
    extractions: Optional[dict] = None,
    reasoning: Optional[dict] = None,
    citations: Optional[dict] = None,
    confidence: Optional[dict] = None,
    model_version: str = "claude-3-5-sonnet-20241022",
    input_tokens: int = 5000,
    output_tokens: int = 2000,
    **kwargs
) -> Extraction:
    """
    Create a mock Extraction object in the database.

    Args:
        db: Database session
        lease_id: ID of associated lease
        extractions: Extracted field values
        reasoning: Reasoning for each extraction
        citations: Source citations for each extraction
        confidence: Confidence scores for each extraction
        model_version: Claude model version used
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        **kwargs: Additional fields to override

    Returns:
        Created Extraction object

    Example:
        extraction = create_mock_extraction(
            db,
            lease_id=1,
            extractions={"tenant.name": "Acme Corp"},
            input_tokens=3000
        )
    """
    # Default minimal extraction data
    if extractions is None:
        extractions = {
            "tenant.name": "Acme Corporation",
            "landlord.name": "Property Management LLC",
            "financial.base_rent": "15000.00",
            "lease_terms.start_date": "2024-01-01",
        }

    if reasoning is None:
        reasoning = {
            "tenant.name": "Found in lease header",
            "financial.base_rent": "Stated in Section 4.1",
        }

    if citations is None:
        citations = {
            "tenant.name": {
                "page": 1,
                "quote": "This Lease Agreement is entered into by Acme Corporation",
            },
            "financial.base_rent": {
                "page": 2,
                "quote": "Base Rent of $15,000.00 per month",
            },
        }

    if confidence is None:
        confidence = {
            "tenant.name": 0.98,
            "landlord.name": 0.97,
            "financial.base_rent": 0.99,
            "lease_terms.start_date": 0.99,
        }

    # Calculate cost (example pricing)
    input_cost = (input_tokens / 1_000_000) * 3.0  # $3 per 1M input tokens
    output_cost = (output_tokens / 1_000_000) * 15.0  # $15 per 1M output tokens
    total_cost = input_cost + output_cost

    extraction_data = {
        "lease_id": lease_id,
        "extractions": extractions,
        "reasoning": reasoning,
        "citations": citations,
        "confidence": confidence,
        "model_version": model_version,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_cost": total_cost,
        "processing_time_seconds": 5.2,
        "created_at": datetime.utcnow(),
    }

    # Override with any provided kwargs
    extraction_data.update(kwargs)

    extraction = Extraction(**extraction_data)
    db.add(extraction)
    db.commit()
    db.refresh(extraction)

    return extraction


def create_complete_workflow(db, **kwargs):
    """
    Create a complete lease + extraction workflow.

    This creates a lease with COMPLETED status and associated extraction,
    useful for testing scenarios where extraction has already been done.

    Args:
        db: Database session
        **kwargs: Fields to override in lease or extraction

    Returns:
        tuple: (lease, extraction)

    Example:
        lease, extraction = create_complete_workflow(
            db,
            original_filename="my-lease.pdf"
        )
    """
    # Separate kwargs for lease and extraction
    lease_kwargs = {}
    extraction_kwargs = {}

    lease_fields = {
        'filename', 'original_filename', 'file_size', 'file_path',
        'status', 'page_count', 'uploaded_by'
    }

    for key, value in kwargs.items():
        if key in lease_fields:
            lease_kwargs[key] = value
        else:
            extraction_kwargs[key] = value

    # Create lease with COMPLETED status
    lease = create_mock_lease(
        db,
        status=LeaseStatus.COMPLETED,
        processed_at=datetime.utcnow(),
        **lease_kwargs
    )

    # Create associated extraction
    extraction = create_mock_extraction(
        db,
        lease_id=lease.id,
        **extraction_kwargs
    )

    return lease, extraction


def create_failed_lease(db, error_message: str = "Extraction failed", **kwargs):
    """
    Create a lease with FAILED status.

    Args:
        db: Database session
        error_message: Error message describing the failure
        **kwargs: Additional fields to override

    Returns:
        Lease object with FAILED status

    Example:
        lease = create_failed_lease(
            db,
            error_message="Invalid PDF format"
        )
    """
    return create_mock_lease(
        db,
        status=LeaseStatus.FAILED,
        error_message=error_message,
        **kwargs
    )


def create_processing_lease(db, **kwargs):
    """
    Create a lease with PROCESSING status.

    Args:
        db: Database session
        **kwargs: Additional fields to override

    Returns:
        Lease object with PROCESSING status

    Example:
        lease = create_processing_lease(db)
    """
    return create_mock_lease(
        db,
        status=LeaseStatus.PROCESSING,
        **kwargs
    )
