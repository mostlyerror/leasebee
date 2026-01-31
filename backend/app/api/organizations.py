"""Organization management API endpoints."""
from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_org_admin
from app.models.user import User
from app.models.organization import Organization, SubscriptionPlan
from app.models.organization_member import OrganizationMember, MemberRole
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    UserOrganizationResponse,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a name."""
    slug = name.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    slug = f"{slug}-{str(uuid4())[:8]}"
    return slug


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new organization with the current user as admin.

    The user becomes the first admin of the organization.
    """
    # Generate slug if not provided
    slug = request.slug or generate_slug(request.name)

    # Check if slug is already taken
    existing_org = db.query(Organization).filter(Organization.slug == slug).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already exists",
        )

    # Create organization
    organization = Organization(
        name=request.name,
        slug=slug,
        plan=SubscriptionPlan.FREE,
    )
    db.add(organization)
    db.flush()

    # Add current user as admin
    membership = OrganizationMember(
        organization_id=organization.id,
        user_id=current_user.id,
        role=MemberRole.ADMIN,
    )
    db.add(membership)
    db.commit()
    db.refresh(organization)

    return OrganizationResponse.model_validate(organization)


@router.get("", response_model=List[UserOrganizationResponse])
async def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all organizations the current user is a member of.

    Returns organizations with the user's role in each.
    """
    memberships = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .all()
    )

    results = []
    for membership in memberships:
        organization = db.query(Organization).filter(Organization.id == membership.organization_id).first()
        if organization:
            results.append(
                UserOrganizationResponse(
                    organization=OrganizationResponse.model_validate(organization),
                    role=membership.role,
                    joined_at=membership.joined_at,
                )
            )

    return results


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get organization details.

    User must be a member of the organization.
    """
    # Verify membership
    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return OrganizationResponse.model_validate(organization)


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    request: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update organization details.

    Requires admin role in the organization.
    """
    # Verify admin access
    require_org_admin(organization_id, current_user, db)

    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Update fields
    if request.name is not None:
        organization.name = request.name

    if request.slug is not None:
        # Check if new slug is already taken
        existing_org = (
            db.query(Organization)
            .filter(Organization.slug == request.slug, Organization.id != organization_id)
            .first()
        )
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already exists",
            )
        organization.slug = request.slug

    db.commit()
    db.refresh(organization)

    return OrganizationResponse.model_validate(organization)


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an organization.

    Requires admin role. This will cascade delete all related data
    (members, leases, etc.) due to database constraints.
    """
    # Verify admin access
    require_org_admin(organization_id, current_user, db)

    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    db.delete(organization)
    db.commit()

    return None
