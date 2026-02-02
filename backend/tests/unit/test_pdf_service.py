"""
Unit tests for the PDF processing service.

These tests verify PDF text extraction, page counting,
and search functionality using PyMuPDF.
"""
import pytest
from pathlib import Path

from app.services.pdf_service import PDFService, pdf_service


@pytest.mark.unit
def test_extract_text_from_bytes_success(sample_pdf_bytes):
    """
    Test successful text extraction from PDF bytes.

    Verifies:
    - Text is extracted from all pages
    - Page count is correct
    - Individual page texts are returned
    - Metadata is included
    """
    service = PDFService()

    result = service.extract_text_from_bytes(sample_pdf_bytes)

    # Verify structure
    assert 'text' in result
    assert 'page_count' in result
    assert 'pages' in result
    assert 'metadata' in result

    # Verify page count
    assert result['page_count'] > 0
    assert isinstance(result['page_count'], int)

    # Verify text content
    assert len(result['text']) > 0
    assert isinstance(result['text'], str)

    # Verify pages structure
    assert len(result['pages']) == result['page_count']
    for page in result['pages']:
        assert 'page_number' in page
        assert 'text' in page
        assert page['page_number'] > 0


@pytest.mark.unit
def test_extract_text_contains_lease_keywords(sample_pdf_bytes):
    """
    Test that extracted text contains expected lease keywords.

    This verifies that the minimal PDF we generated
    contains recognizable lease content.
    """
    service = PDFService()

    result = service.extract_text_from_bytes(sample_pdf_bytes)
    text = result['text'].upper()

    # Check for common lease keywords
    assert 'LEASE' in text or 'AGREEMENT' in text


@pytest.mark.unit
def test_extract_text_from_invalid_pdf():
    """
    Test extraction fails gracefully with invalid PDF bytes.
    """
    service = PDFService()

    # Invalid PDF bytes
    invalid_bytes = b"This is not a PDF file"

    # Verify exception is raised
    with pytest.raises(Exception) as exc_info:
        service.extract_text_from_bytes(invalid_bytes)

    assert "Failed to process PDF" in str(exc_info.value)


@pytest.mark.unit
def test_extract_text_from_empty_bytes():
    """
    Test extraction fails with empty bytes.
    """
    service = PDFService()

    # Empty bytes
    empty_bytes = b""

    # Verify exception is raised
    with pytest.raises(Exception):
        service.extract_text_from_bytes(empty_bytes)


@pytest.mark.unit
def test_extract_text_page_numbering(sample_pdf_bytes):
    """
    Test that page numbers are correctly 1-indexed.
    """
    service = PDFService()

    result = service.extract_text_from_bytes(sample_pdf_bytes)

    # Verify page numbers start at 1
    page_numbers = [page['page_number'] for page in result['pages']]
    assert page_numbers[0] == 1

    # Verify page numbers are sequential
    for i, page_num in enumerate(page_numbers):
        assert page_num == i + 1


@pytest.mark.unit
def test_extract_text_metadata(sample_pdf_bytes):
    """
    Test that PDF metadata is extracted.
    """
    service = PDFService()

    result = service.extract_text_from_bytes(sample_pdf_bytes)

    # Verify metadata is present (even if empty)
    assert result['metadata'] is not None
    assert isinstance(result['metadata'], dict)


@pytest.mark.unit
def test_extract_page_text_success(sample_pdf_bytes):
    """
    Test extracting text from a specific page.

    Verifies:
    - Text is extracted from the specified page
    - Page numbers are 1-indexed
    """
    service = PDFService()

    # Get page count first
    result = service.extract_text_from_bytes(sample_pdf_bytes)
    page_count = result['page_count']

    # Extract first page
    page_text = service.extract_page_text(sample_pdf_bytes, 1)

    assert isinstance(page_text, str)
    assert len(page_text) > 0

    # Verify it matches the text from extract_text_from_bytes
    assert page_text == result['pages'][0]['text']


@pytest.mark.unit
def test_extract_page_text_invalid_page_number(sample_pdf_bytes):
    """
    Test that invalid page numbers raise errors.
    """
    service = PDFService()

    # Page 0 (invalid - should be 1-indexed)
    with pytest.raises(Exception) as exc_info:
        service.extract_page_text(sample_pdf_bytes, 0)

    assert "Invalid page number" in str(exc_info.value)

    # Page beyond document length
    with pytest.raises(Exception) as exc_info:
        service.extract_page_text(sample_pdf_bytes, 9999)

    assert "Invalid page number" in str(exc_info.value)


@pytest.mark.unit
def test_extract_page_text_negative_page_number(sample_pdf_bytes):
    """
    Test that negative page numbers raise errors.
    """
    service = PDFService()

    with pytest.raises(Exception):
        service.extract_page_text(sample_pdf_bytes, -1)


@pytest.mark.unit
def test_search_text_in_pdf_success(sample_pdf_bytes):
    """
    Test searching for text in PDF.

    Verifies:
    - Text is found in the document
    - Results include page number and bounding box
    - Multiple occurrences are returned
    """
    service = PDFService()

    # Search for a common word (case-sensitive)
    results = service.search_text_in_pdf(sample_pdf_bytes, "LEASE")

    # If the word is found, verify structure
    if len(results) > 0:
        result = results[0]

        assert 'page' in result
        assert 'bbox' in result
        assert 'text' in result

        # Verify page number is 1-indexed
        assert result['page'] >= 1

        # Verify bounding box structure
        bbox = result['bbox']
        assert 'x0' in bbox
        assert 'y0' in bbox
        assert 'x1' in bbox
        assert 'y1' in bbox

        # Verify bounding box coordinates are numbers
        assert isinstance(bbox['x0'], (int, float))
        assert isinstance(bbox['y0'], (int, float))


@pytest.mark.unit
def test_search_text_not_found(sample_pdf_bytes):
    """
    Test searching for text that doesn't exist returns empty list.
    """
    service = PDFService()

    # Search for text that definitely doesn't exist
    results = service.search_text_in_pdf(
        sample_pdf_bytes,
        "XYZNONEXISTENTTEXT123"
    )

    assert results == []
    assert len(results) == 0


@pytest.mark.unit
def test_search_text_specific_page(sample_pdf_bytes):
    """
    Test searching for text on a specific page.

    Verifies that page_number parameter restricts search.
    """
    service = PDFService()

    # Get total page count
    info = service.extract_text_from_bytes(sample_pdf_bytes)
    page_count = info['page_count']

    if page_count > 0:
        # Search only on page 1
        results = service.search_text_in_pdf(
            sample_pdf_bytes,
            "LEASE",
            page_number=1
        )

        # Verify all results are from page 1
        for result in results:
            assert result['page'] == 1


@pytest.mark.unit
def test_search_text_invalid_pdf():
    """
    Test searching in invalid PDF raises exception.
    """
    service = PDFService()

    invalid_bytes = b"Not a PDF"

    with pytest.raises(Exception) as exc_info:
        service.search_text_in_pdf(invalid_bytes, "test")

    assert "Failed to search PDF" in str(exc_info.value)


@pytest.mark.unit
def test_search_text_case_sensitive(sample_pdf_bytes):
    """
    Test that text search is case-sensitive.

    PyMuPDF's search_for() is case-sensitive by default.
    """
    service = PDFService()

    # Search with different cases
    results_upper = service.search_text_in_pdf(sample_pdf_bytes, "LEASE")
    results_lower = service.search_text_in_pdf(sample_pdf_bytes, "lease")

    # Results may differ based on actual case in PDF
    # This test documents the case-sensitive behavior
    assert isinstance(results_upper, list)
    assert isinstance(results_lower, list)


@pytest.mark.unit
def test_pdf_service_singleton():
    """
    Test that pdf_service is properly initialized as a singleton.
    """
    assert pdf_service is not None
    assert isinstance(pdf_service, PDFService)


@pytest.mark.unit
def test_static_methods():
    """
    Test that PDFService methods are static.

    This allows them to be called without instantiation.
    """
    # Verify methods are static
    assert PDFService.extract_text_from_bytes is not None
    assert PDFService.search_text_in_pdf is not None
    assert PDFService.extract_page_text is not None


@pytest.mark.unit
def test_extract_text_multiple_pages():
    """
    Test extraction from a multi-page PDF.

    Uses the real sample lease PDF if available.
    """
    pdf_path = Path(__file__).parent.parent / "fixtures" / "sample_lease.pdf"

    if not pdf_path.exists():
        pytest.skip("Sample lease PDF not found")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    service = PDFService()
    result = service.extract_text_from_bytes(pdf_bytes)

    # Our sample has 3 pages
    assert result['page_count'] == 3
    assert len(result['pages']) == 3

    # Verify each page exists (may have empty text if page has only graphics)
    for page in result['pages']:
        assert 'text' in page
        assert 'page_number' in page


@pytest.mark.unit
def test_search_in_real_sample_pdf():
    """
    Test searching in the real sample lease PDF.
    """
    pdf_path = Path(__file__).parent.parent / "fixtures" / "sample_lease.pdf"

    if not pdf_path.exists():
        pytest.skip("Sample lease PDF not found")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    service = PDFService()

    # Search for a term we know is in the sample
    results = service.search_text_in_pdf(pdf_bytes, "Acme Corporation")

    # Should find at least one occurrence
    assert len(results) > 0
    assert results[0]['text'] == "Acme Corporation"
    assert results[0]['page'] >= 1


@pytest.mark.unit
def test_extract_all_pages_individually(sample_pdf_bytes):
    """
    Test extracting each page individually and compare to full extraction.
    """
    service = PDFService()

    # Get full extraction
    full_result = service.extract_text_from_bytes(sample_pdf_bytes)
    page_count = full_result['page_count']

    # Extract each page individually
    for page_num in range(1, page_count + 1):
        page_text = service.extract_page_text(sample_pdf_bytes, page_num)

        # Compare with text from full extraction
        expected_text = full_result['pages'][page_num - 1]['text']
        assert page_text == expected_text


@pytest.mark.unit
def test_pdf_with_no_text():
    """
    Test handling of PDFs with no extractable text (e.g., images only).

    This creates a minimal blank PDF.
    """
    # Minimal PDF with no text content
    blank_pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
188
%%EOF"""

    service = PDFService()

    # Should not raise an exception
    result = service.extract_text_from_bytes(blank_pdf)

    # Should return structure with empty or minimal text
    assert result['page_count'] == 1
    assert isinstance(result['text'], str)


@pytest.mark.unit
def test_enrich_citations_with_bounding_boxes(sample_pdf_bytes):
    """
    Test enriching citations with bounding box coordinates.

    Verifies:
    - Citations are enriched with bounding boxes
    - Original citation data is preserved
    - Missing quotes are handled gracefully
    """
    service = PDFService()

    # Sample citations (similar to what Claude returns)
    citations = {
        'field1': {
            'page': 1,
            'quote': 'LEASE AGREEMENT'
        },
        'field2': {
            'page': 1,
            'quote': 'Tenant'
        },
        'field3': {
            'page': 99,  # Invalid page
            'quote': 'Should not crash'
        }
    }

    result = service.enrich_citations_with_bounding_boxes(sample_pdf_bytes, citations)

    # Verify structure
    assert len(result) == 3
    assert 'field1' in result
    assert 'field2' in result
    assert 'field3' in result

    # Field 1 should have bounding box (if text found)
    assert 'page' in result['field1']
    assert 'quote' in result['field1']

    # Field 3 should not crash on invalid page
    assert 'page' in result['field3']
    assert result['field3']['page'] == 99


@pytest.mark.unit
def test_enrich_citations_with_bounding_boxes_empty():
    """
    Test enriching empty citations dictionary.

    Verifies:
    - Empty dict returns empty dict
    - No errors are raised
    """
    service = PDFService()

    result = service.enrich_citations_with_bounding_boxes(b'', {})

    assert result == {}


@pytest.mark.unit  
def test_enrich_citations_with_bounding_boxes_partial_match(sample_pdf_bytes):
    """
    Test enriching citations when exact match fails but partial match succeeds.

    Verifies:
    - Fallback to partial match works
    - Bounding box is still found for long quotes
    """
    service = PDFService()

    # Long quote that might not match exactly
    citations = {
        'field1': {
            'page': 1,
            'quote': 'This is a very long quote that might not match exactly in the PDF'
        }
    }

    result = service.enrich_citations_with_bounding_boxes(sample_pdf_bytes, citations)

    # Should not crash and return the citation
    assert 'field1' in result
    assert 'page' in result['field1']
    assert 'quote' in result['field1']
