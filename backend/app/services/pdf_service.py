"""PDF processing service using PyMuPDF."""
import fitz  # PyMuPDF
from typing import Dict, List, Optional


class PDFService:
    """Service for PDF text extraction and processing."""

    @staticmethod
    def extract_text_from_bytes(pdf_bytes: bytes) -> Dict:
        """
        Extract text and metadata from PDF bytes.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            Dictionary with:
            - text: Full text content
            - page_count: Number of pages
            - pages: List of page texts
            - metadata: PDF metadata

        Raises:
            Exception: If PDF processing fails
        """
        try:
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            # Extract metadata
            metadata = pdf_document.metadata
            page_count = pdf_document.page_count

            # Extract text from all pages
            full_text = ""
            pages = []

            for page_num in range(page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                full_text += page_text + "\n\n"
                pages.append({
                    'page_number': page_num + 1,
                    'text': page_text
                })

            pdf_document.close()

            return {
                'text': full_text,
                'page_count': page_count,
                'pages': pages,
                'metadata': metadata,
            }

        except Exception as e:
            raise Exception(f"Failed to process PDF: {str(e)}")

    @staticmethod
    def search_text_in_pdf(
        pdf_bytes: bytes,
        search_text: str,
        page_number: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for text in PDF and return locations with bounding boxes.

        Args:
            pdf_bytes: PDF file content as bytes
            search_text: Text to search for
            page_number: Optional specific page number to search (1-indexed)

        Returns:
            List of dictionaries with:
            - page: Page number (1-indexed)
            - bbox: Bounding box coordinates
            - text: Matched text
        """
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            results = []

            # Determine page range
            if page_number is not None:
                start_page = page_number - 1
                end_page = page_number
            else:
                start_page = 0
                end_page = pdf_document.page_count

            # Search each page
            for page_num in range(start_page, end_page):
                page = pdf_document[page_num]
                text_instances = page.search_for(search_text)

                for inst in text_instances:
                    results.append({
                        'page': page_num + 1,
                        'bbox': {
                            'x0': inst.x0,
                            'y0': inst.y0,
                            'x1': inst.x1,
                            'y1': inst.y1,
                        },
                        'text': search_text,
                    })

            pdf_document.close()
            return results

        except Exception as e:
            raise Exception(f"Failed to search PDF: {str(e)}")

    @staticmethod
    def extract_page_text(pdf_bytes: bytes, page_number: int) -> str:
        """
        Extract text from a specific page.

        Args:
            pdf_bytes: PDF file content as bytes
            page_number: Page number (1-indexed)

        Returns:
            Text content of the page
        """
        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            if page_number < 1 or page_number > pdf_document.page_count:
                raise ValueError(f"Invalid page number: {page_number}")

            page = pdf_document[page_number - 1]
            text = page.get_text()
            pdf_document.close()

            return text

        except Exception as e:
            raise Exception(f"Failed to extract page text: {str(e)}")

    @staticmethod
    def enrich_citations_with_bounding_boxes(
        pdf_bytes: bytes,
        citations: Dict[str, Dict]
    ) -> Dict[str, Dict]:
        """
        Enrich citation dictionary with bounding box coordinates.

        Args:
            pdf_bytes: PDF file content as bytes
            citations: Dictionary of citations with format:
                {
                    "field_path": {
                        "page": int,
                        "quote": str
                    }
                }

        Returns:
            Enhanced citations dictionary with bounding_box added:
                {
                    "field_path": {
                        "page": int,
                        "quote": str,
                        "bounding_box": {"x0": float, "y0": float, "x1": float, "y1": float}
                    }
                }
        """
        if not citations:
            return citations

        try:
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            enriched_citations = {}

            for field_path, citation in citations.items():
                enriched_citation = citation.copy()

                if not citation or 'page' not in citation or 'quote' not in citation:
                    enriched_citations[field_path] = enriched_citation
                    continue

                page_num = citation['page']
                quote = citation['quote']

                # Validate page number
                if page_num < 1 or page_num > pdf_document.page_count:
                    enriched_citations[field_path] = enriched_citation
                    continue

                # Search for the quote on the specified page
                page = pdf_document[page_num - 1]

                # Try exact match first
                text_instances = page.search_for(quote)

                # If no exact match, try searching for first few words
                if not text_instances and len(quote) > 20:
                    # Try first 20 characters
                    text_instances = page.search_for(quote[:20])

                # Use the first match if found
                if text_instances:
                    bbox = text_instances[0]
                    enriched_citation['bounding_box'] = {
                        'x0': bbox.x0,
                        'y0': bbox.y0,
                        'x1': bbox.x1,
                        'y1': bbox.y1,
                    }

                enriched_citations[field_path] = enriched_citation

            pdf_document.close()
            return enriched_citations

        except Exception as e:
            # If enrichment fails, return original citations
            print(f"Warning: Failed to enrich citations with bounding boxes: {str(e)}")
            return citations


# Singleton instance
pdf_service = PDFService()
