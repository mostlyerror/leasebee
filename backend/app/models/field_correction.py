"""Field correction model for tracking user edits."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from sqlalchemy.orm import relationship


class FieldCorrection(Base):
    """
    Field correction model.

    Tracks user edits to extracted fields for learning and accuracy measurement.
    """

    __tablename__ = "field_corrections"

    id = Column(Integer, primary_key=True, index=True)
    extraction_id = Column(Integer, ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Field information
    field_path = Column(String, nullable=False, index=True)  # e.g., "property.address"
    original_value = Column(Text, nullable=True)  # Claude's extraction
    corrected_value = Column(Text, nullable=True)  # User's correction

    # User feedback
    correction_type = Column(String, nullable=True)  # 'accept', 'reject', or 'edit'
    notes = Column(Text, nullable=True)  # User notes/comments
    correction_reason = Column(Text, nullable=True)  # Why was it wrong? (legacy)
    correction_category = Column(String, nullable=True)  # e.g., "wrong_value", "missing", "hallucination" (legacy)

    # Original extraction metadata
    original_confidence = Column(Float, nullable=True)
    original_reasoning = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Multi-tenant field
    corrected_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    extraction = relationship("Extraction", back_populates="field_corrections")
    corrector = relationship("User", foreign_keys=[corrected_by])

    def __repr__(self):
        return f"<FieldCorrection(id={self.id}, field={self.field_path}, extraction_id={self.extraction_id})>"
