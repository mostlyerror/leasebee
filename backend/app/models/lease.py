"""Lease model for storing PDF metadata."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class LeaseStatus(str, enum.Enum):
    """Lease processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"


class Lease(Base):
    """
    Lease document model.

    Stores metadata about uploaded PDF lease documents.
    """

    __tablename__ = "leases"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_path = Column(String, nullable=False)  # S3 key or local path
    content_type = Column(String, default="application/pdf")

    # Processing status
    status = Column(SQLEnum(LeaseStatus), default=LeaseStatus.UPLOADED, index=True)
    error_message = Column(String, nullable=True)

    # Metadata
    page_count = Column(Integer, nullable=True)

    # Multi-tenant fields
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for migration compatibility
        index=True
    )
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    extractions = relationship("Extraction", back_populates="lease", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="leases")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<Lease(id={self.id}, filename={self.filename}, status={self.status})>"
