"""Few-shot example model for prompt enhancement."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON

from app.core.database import Base


class FewShotExample(Base):
    """
    Few-shot example model.

    Stores high-quality correction examples for enhancing prompts
    with few-shot learning. Used in Phase 3.
    """

    __tablename__ = "few_shot_examples"

    id = Column(Integer, primary_key=True, index=True)

    # Field information
    field_path = Column(String, nullable=False, index=True)

    # Example data
    source_text = Column(Text, nullable=False)  # PDF excerpt
    correct_value = Column(Text, nullable=False)  # Correct extraction
    reasoning = Column(Text, nullable=True)  # Why this is correct

    # Quality metrics
    quality_score = Column(Float, nullable=True)  # For ranking examples
    usage_count = Column(Integer, default=0)  # How often used in prompts

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_from_correction_id = Column(Integer, nullable=True)  # Source correction

    # Additional context
    metadata = Column(JSON, nullable=True)  # Flexible field for extra info

    def __repr__(self):
        return f"<FewShotExample(id={self.id}, field={self.field_path}, active={self.is_active})>"
