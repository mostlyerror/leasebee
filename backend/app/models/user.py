"""User model for authentication and authorization."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class User(Base):
    """
    User model for authentication.

    Stores user account information for multi-tenant access.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)

    # Authentication - will be populated in Phase 2
    hashed_password = Column(String, nullable=True)
    is_active = Column(String, default=True)
    is_verified = Column(String, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization_memberships = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
