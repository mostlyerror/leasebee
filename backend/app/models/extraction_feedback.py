"""Extraction feedback model for overall quality ratings."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExtractionFeedback(Base):
    """
    Extraction feedback model.

    Stores overall user feedback on extraction quality,
    review time, and general comments.
    """

    __tablename__ = "extraction_feedback"

    id = Column(Integer, primary_key=True, index=True)
    extraction_id = Column(Integer, ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Quality rating (1-5 scale)
    quality_rating = Column(Integer, nullable=True)

    # Time tracking
    review_time_seconds = Column(Float, nullable=True)

    # Feedback
    feedback_text = Column(Text, nullable=True)
    issues = Column(Text, nullable=True)  # Specific problems encountered

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_by = Column(String, nullable=True)

    # Relationships
    extraction = relationship("Extraction", back_populates="feedback")

    def __repr__(self):
        return f"<ExtractionFeedback(id={self.id}, extraction_id={self.extraction_id}, rating={self.quality_rating})>"
