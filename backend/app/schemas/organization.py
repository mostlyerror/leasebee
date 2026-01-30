"""Organization and team management schemas."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.organization import SubscriptionPlan
from app.models.organization_member import MemberRole


# Organization Schemas
class OrganizationCreate(BaseModel):
    """Create organization request."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)


class OrganizationUpdate(BaseModel):
    """Update organization request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)


class OrganizationResponse(BaseModel):
    """Organization response schema."""

    id: UUID
    name: str
    slug: str
    plan: SubscriptionPlan
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Organization Member Schemas
class OrganizationMemberResponse(BaseModel):
    """Organization member response."""

    user_id: UUID
    user_name: str
    user_email: str
    user_avatar_url: Optional[str] = None
    role: MemberRole
    joined_at: datetime

    class Config:
        from_attributes = True


class InviteMemberRequest(BaseModel):
    """Invite member to organization request."""

    email: str
    role: MemberRole = MemberRole.MEMBER


class UpdateMemberRoleRequest(BaseModel):
    """Update member role request."""

    role: MemberRole


# User's Organizations Response
class UserOrganizationResponse(BaseModel):
    """User's organization membership response."""

    organization: OrganizationResponse
    role: MemberRole
    joined_at: datetime

    class Config:
        from_attributes = True
