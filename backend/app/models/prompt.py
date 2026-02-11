"""Prompt template model for versioned prompt management."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean

from app.core.database import Base


class PromptTemplate(Base):
    """
    Prompt template model.

    Stores versioned prompts for Claude extraction.
    Only one template can be active at a time.
    """

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Version info
    version = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Prompt sections
    system_prompt = Column(Text, nullable=False)
    field_type_guidance = Column(Text, nullable=False)
    extraction_examples = Column(Text, nullable=False)
    null_value_guidance = Column(Text, nullable=False)

    # Status
    is_active = Column(Boolean, default=False, index=True)

    # Metrics
    usage_count = Column(Integer, default=0)
    avg_confidence = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, version={self.version}, active={self.is_active})>"
