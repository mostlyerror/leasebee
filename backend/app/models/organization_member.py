"""OrganizationMember model for team management."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class MemberRole(str, enum.Enum):
    """Organization member roles."""
    ADMIN = "admin"  # Full access, billing, team management
    MEMBER = "member"  # Upload, review, view all org leases
    VIEWER = "viewer"  # View only, cannot upload/review


class OrganizationMember(Base):
    """
    OrganizationMember model for managing team access.

    Links users to organizations with specific roles.
    """

    __tablename__ = "organization_members"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    role = Column(SQLEnum(MemberRole), default=MemberRole.MEMBER, nullable=False)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")

    def __repr__(self):
        return f"<OrganizationMember(org_id={self.organization_id}, user_id={self.user_id}, role={self.role})>"
