"""Extraction model for storing Claude's extracted data."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class Extraction(Base):
    """
    Extraction result model.

    Stores the structured data extracted from a lease by Claude,
    including reasoning, citations, and confidence scores.
    """

    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, index=True)
    lease_id = Column(Integer, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False, index=True)

    # Extracted data (JSONB for flexibility)
    extractions = Column(JSON, nullable=False)  # {"field_path": "value"}
    reasoning = Column(JSON, nullable=True)     # {"field_path": "explanation"}
    citations = Column(JSON, nullable=True)     # {"field_path": {"page": N, "quote": "..."}}
    confidence = Column(JSON, nullable=True)    # {"field_path": 0.95}

    # Model metadata
    model_version = Column(String, nullable=False)  # e.g., "claude-3-5-sonnet-20241022"
    prompt_version = Column(String, nullable=True)  # For tracking prompt iterations
    extraction_metadata = Column(JSON, nullable=True)  # {"validation_warnings": {...}, "multi_pass": true, etc.}

    # Token usage and cost
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)  # in USD

    # Processing metadata
    processing_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    lease = relationship("Lease", back_populates="extractions")
    field_corrections = relationship("FieldCorrection", back_populates="extraction", cascade="all, delete-orphan")
    citation_sources = relationship("CitationSource", back_populates="extraction", cascade="all, delete-orphan")
    feedback = relationship("ExtractionFeedback", back_populates="extraction", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Extraction(id={self.id}, lease_id={self.lease_id}, model={self.model_version})>"
