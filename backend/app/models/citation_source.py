"""Citation source model for linking fields to PDF locations."""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class CitationSource(Base):
    """
    Citation source model.

    Links extracted fields to specific locations in the source PDF.
    Stores page numbers, bounding boxes, and source text for verification.
    """

    __tablename__ = "citation_sources"

    id = Column(Integer, primary_key=True, index=True)
    extraction_id = Column(Integer, ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Field reference
    field_path = Column(String, nullable=False, index=True)

    # PDF location
    page_number = Column(Integer, nullable=False)
    bounding_box = Column(JSON, nullable=True)  # {"x0": 0, "y0": 0, "x1": 100, "y1": 100}

    # Source text
    source_text = Column(Text, nullable=False)  # Exact quote from PDF
    context_text = Column(Text, nullable=True)  # Surrounding text for context

    # Relationships
    extraction = relationship("Extraction", back_populates="citation_sources")

    def __repr__(self):
        return f"<CitationSource(id={self.id}, field={self.field_path}, page={self.page_number})>"
