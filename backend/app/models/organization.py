"""Organization model for multi-tenant support."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Organization(Base):
    """
    Organization model for multi-tenant architecture.

    Each organization represents a separate tenant with isolated data.
    """

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    plan = Column(
        SQLEnum(SubscriptionPlan),
        default=SubscriptionPlan.FREE,
        nullable=False
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    leases = relationship(
        "Lease",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, plan={self.plan})>"
