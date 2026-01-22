"""
Integration tests for the complete lease extraction workflow.

This test suite replaces manual browser testing:
- Upload PDF → Extract data → Verify results

These tests execute the complete user workflow programmatically,
providing fast, reliable, automated validation.
"""
import pytest
from io import BytesIO
from pathlib import Path

from app.models.lease import LeaseStatus


@pytest.mark.integration
def test_complete_extraction_workflow(client, sample_pdf_bytes, mock_extraction_response):
    """
    Complete workflow: Upload PDF → Extract → Verify.

    Replaces manual testing:
    - Open browser → Upload file → Click extract → Wait → Verify fields

    This test covers:
    1. PDF upload with validation
    2. Lease record creation
    3. Data extraction with Claude (mocked)
    4. Extraction record creation
    5. Lease status updates
    6. Field verification
    """
    # ========================================================================
    # Step 1: Upload PDF
    # ========================================================================
    files = {
        "file": ("test_lease.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
    }
    response = client.post("/api/leases/upload", files=files)

    assert response.status_code == 201
    lease = response.json()
    lease_id = lease["id"]

    # Verify lease creation
    assert lease["status"] == "uploaded"
    assert lease["original_filename"] == "test_lease.pdf"
    assert lease["file_size"] > 0
    assert lease["page_count"] is not None
    assert "created_at" in lease

    # ========================================================================
    # Step 2: Extract data from the lease
    # ========================================================================
    response = client.post(f"/api/extractions/extract/{lease_id}")

    assert response.status_code == 201
    extraction = response.json()
    extraction_id = extraction["id"]

    # Verify extraction structure
    assert extraction["lease_id"] == lease_id
    assert "extractions" in extraction
    assert "reasoning" in extraction
    assert "citations" in extraction
    assert "confidence" in extraction

    # Verify metadata
    assert extraction["model_version"] is not None
    assert extraction["input_tokens"] > 0
    assert extraction["output_tokens"] > 0
    assert extraction["total_cost"] > 0

    # ========================================================================
    # Step 3: Verify extracted field values
    # ========================================================================
    extractions = extraction["extractions"]

    # Tenant information
    assert extractions["tenant.name"] == "Acme Corporation"
    assert extractions["tenant.city"] == "San Francisco"
    assert extractions["tenant.state"] == "CA"

    # Landlord information
    assert extractions["landlord.name"] == "Property Management LLC"

    # Property information
    assert extractions["property.address"] == "789 Office Boulevard, Suite 200"
    assert extractions["property.square_feet"] == "5000"

    # Financial terms
    assert extractions["financial.base_rent"] == "15000.00"
    assert extractions["financial.security_deposit"] == "30000.00"

    # Lease terms
    assert extractions["lease_terms.start_date"] == "2024-01-01"
    assert extractions["lease_terms.term_length"] == "36 months"

    # ========================================================================
    # Step 4: Verify lease status updated to completed
    # ========================================================================
    response = client.get(f"/api/leases/{lease_id}")

    assert response.status_code == 200
    lease = response.json()
    assert lease["status"] == "completed"
    assert lease["processed_at"] is not None

    # ========================================================================
    # Step 5: Verify extraction can be retrieved
    # ========================================================================
    response = client.get(f"/api/extractions/{extraction_id}")

    assert response.status_code == 200
    retrieved_extraction = response.json()
    assert retrieved_extraction["id"] == extraction_id
    assert retrieved_extraction["extractions"] == extractions


@pytest.mark.integration
def test_upload_invalid_file_type(client):
    """
    Test that non-PDF files are rejected.

    Replaces manual testing:
    - Try uploading .txt file → Should see error message
    """
    # Create a text file
    text_content = b"This is not a PDF file"
    files = {
        "file": ("test.txt", BytesIO(text_content), "text/plain")
    }

    response = client.post("/api/leases/upload", files=files)

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@pytest.mark.integration
def test_upload_invalid_pdf(client):
    """
    Test that invalid/corrupted PDF files are rejected.

    Replaces manual testing:
    - Try uploading corrupted PDF → Should see error message
    """
    # Create invalid PDF content
    invalid_pdf = b"Not a real PDF"
    files = {
        "file": ("invalid.pdf", BytesIO(invalid_pdf), "application/pdf")
    }

    response = client.post("/api/leases/upload", files=files)

    assert response.status_code == 400
    assert "Invalid PDF" in response.json()["detail"]


@pytest.mark.integration
def test_upload_oversized_file(client, mocker):
    """
    Test that files exceeding size limit are rejected.

    Replaces manual testing:
    - Try uploading 100MB file → Should see error message
    """
    # Mock a large file
    large_pdf_content = b"%PDF-1.4\n" + (b"x" * (51 * 1024 * 1024))  # 51MB
    files = {
        "file": ("large.pdf", BytesIO(large_pdf_content), "application/pdf")
    }

    response = client.post("/api/leases/upload", files=files)

    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]


@pytest.mark.integration
def test_extract_nonexistent_lease(client):
    """
    Test extraction fails gracefully for non-existent lease.

    Replaces manual testing:
    - Try extracting from lease ID 99999 → Should see error message
    """
    response = client.post("/api/extractions/extract/99999")

    assert response.status_code == 404
    assert "Lease not found" in response.json()["detail"]


@pytest.mark.integration
def test_extraction_failure_updates_status(client, sample_pdf_bytes, mocker):
    """
    Test that extraction failures update lease status to 'failed'.

    Replaces manual testing:
    - Upload PDF → Extraction fails → Check lease shows 'failed' status
    """
    # First, upload a PDF
    files = {
        "file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
    }
    response = client.post("/api/leases/upload", files=files)
    lease_id = response.json()["id"]

    # Mock Claude service to raise an exception
    mocker.patch(
        'app.services.claude_service.claude_service.extract_lease_data',
        side_effect=Exception("Claude API error")
    )

    # Try to extract (should fail)
    response = client.post(f"/api/extractions/extract/{lease_id}")

    assert response.status_code == 500
    assert "Extraction failed" in response.json()["detail"]

    # Verify lease status is 'failed'
    response = client.get(f"/api/leases/{lease_id}")
    lease = response.json()
    assert lease["status"] == "failed"
    assert lease["error_message"] is not None


@pytest.mark.integration
def test_get_lease_not_found(client):
    """
    Test getting a non-existent lease returns 404.
    """
    response = client.get("/api/leases/99999")

    assert response.status_code == 404
    assert "Lease not found" in response.json()["detail"]


@pytest.mark.integration
def test_list_leases(client, sample_pdf_bytes):
    """
    Test listing leases returns uploaded leases.

    Replaces manual testing:
    - Upload multiple PDFs → Check they appear in list
    """
    # Upload multiple leases
    for i in range(3):
        files = {
            "file": (f"test_{i}.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
        }
        client.post("/api/leases/upload", files=files)

    # List leases
    response = client.get("/api/leases/")

    assert response.status_code == 200
    leases = response.json()
    assert len(leases) >= 3

    # Verify latest lease is first (descending order)
    assert leases[0]["original_filename"] == "test_2.pdf"


@pytest.mark.integration
def test_delete_lease(client, sample_pdf_bytes):
    """
    Test deleting a lease removes it from the database.

    Replaces manual testing:
    - Upload PDF → Delete it → Verify it's gone
    """
    # Upload a lease
    files = {
        "file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
    }
    response = client.post("/api/leases/upload", files=files)
    lease_id = response.json()["id"]

    # Delete the lease
    response = client.delete(f"/api/leases/{lease_id}")

    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/leases/{lease_id}")
    assert response.status_code == 404


@pytest.mark.integration
def test_get_download_url(client, sample_pdf_bytes):
    """
    Test getting a presigned download URL for a lease.
    """
    # Upload a lease
    files = {
        "file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
    }
    response = client.post("/api/leases/upload", files=files)
    lease_id = response.json()["id"]

    # Get download URL
    response = client.get(f"/api/leases/{lease_id}/download-url")

    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "expires_in" in data
    assert data["expires_in"] == 3600


@pytest.mark.integration
def test_get_lease_extractions(client, sample_pdf_bytes, mock_extraction_response):
    """
    Test getting all extractions for a lease.
    """
    # Upload and extract
    files = {
        "file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
    }
    response = client.post("/api/leases/upload", files=files)
    lease_id = response.json()["id"]

    client.post(f"/api/extractions/extract/{lease_id}")

    # Get extractions for this lease
    response = client.get(f"/api/extractions/lease/{lease_id}")

    assert response.status_code == 200
    extractions = response.json()
    assert len(extractions) == 1
    assert extractions[0]["lease_id"] == lease_id


@pytest.mark.integration
def test_update_extraction(client, sample_pdf_bytes, mock_extraction_response):
    """
    Test updating extraction data after user review.

    Replaces manual testing:
    - Extract data → Edit field → Save → Verify changes
    """
    # Upload and extract
    files = {
        "file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
    }
    response = client.post("/api/leases/upload", files=files)
    lease_id = response.json()["id"]

    response = client.post(f"/api/extractions/extract/{lease_id}")
    extraction_id = response.json()["id"]

    # Update the extraction
    update_data = {
        "extractions": {
            "tenant.name": "Updated Corporation Name",
            "financial.base_rent": "20000.00",
        }
    }

    response = client.patch(
        f"/api/extractions/{extraction_id}",
        json=update_data
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["extractions"]["tenant.name"] == "Updated Corporation Name"
    assert updated["extractions"]["financial.base_rent"] == "20000.00"

    # Verify lease status changed to reviewed
    response = client.get(f"/api/leases/{lease_id}")
    lease = response.json()
    assert lease["status"] == "reviewed"


@pytest.mark.integration
def test_export_extraction(client, sample_pdf_bytes, mock_extraction_response):
    """
    Test exporting extraction data.
    """
    # Upload and extract
    files = {
        "file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
    }
    response = client.post("/api/leases/upload", files=files)
    lease_id = response.json()["id"]

    response = client.post(f"/api/extractions/extract/{lease_id}")
    extraction_id = response.json()["id"]

    # Export with citations and reasoning
    export_request = {
        "include_citations": True,
        "include_reasoning": True,
    }

    response = client.post(
        f"/api/extractions/{extraction_id}/export",
        json=export_request
    )

    assert response.status_code == 200
    export_data = response.json()
    assert "data" in export_data
    assert "metadata" in export_data
    assert "extractions" in export_data["data"]
    assert "citations" in export_data["data"]
    assert "reasoning" in export_data["data"]


@pytest.mark.integration
def test_get_field_schema(client):
    """
    Test getting the field schema definition.
    """
    response = client.get("/api/extractions/schema/fields")

    assert response.status_code == 200
    schema = response.json()
    assert "fields" in schema
    assert "categories" in schema
    assert len(schema["fields"]) > 0
    assert len(schema["categories"]) > 0


@pytest.mark.integration
@pytest.mark.slow
def test_real_pdf_extraction(client):
    """
    Test extraction with the actual sample lease PDF.

    This test uses the real generated PDF file instead of minimal bytes.
    Marked as 'slow' since it processes a real PDF.
    """
    # Load the real sample PDF
    pdf_path = Path(__file__).parent.parent / "fixtures" / "sample_lease.pdf"

    if not pdf_path.exists():
        pytest.skip("Sample lease PDF not found")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Upload the real PDF
    files = {
        "file": ("sample_lease.pdf", BytesIO(pdf_bytes), "application/pdf")
    }
    response = client.post("/api/leases/upload", files=files)

    assert response.status_code == 201
    lease = response.json()
    assert lease["page_count"] == 3  # Our sample has 3 pages

    # Extract data
    lease_id = lease["id"]
    response = client.post(f"/api/extractions/extract/{lease_id}")

    assert response.status_code == 201
    extraction = response.json()
    assert extraction["extractions"] is not None
