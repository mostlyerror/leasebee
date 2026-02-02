"""Team management API endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_org_admin, get_organization_member
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, MemberRole
from app.schemas.organization import (
    OrganizationMemberResponse,
    InviteMemberRequest,
    UpdateMemberRoleRequest,
)

router = APIRouter(prefix="/organizations/{organization_id}/members", tags=["Team Management"])


@router.get("", response_model=List[OrganizationMemberResponse])
async def list_organization_members(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all members of an organization.

    User must be a member of the organization.
    """
    # Verify user is a member
    get_organization_member(organization_id, current_user, db)

    # Get all members
    memberships = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.organization_id == organization_id)
        .all()
    )

    results = []
    for membership in memberships:
        user = db.query(User).filter(User.id == membership.user_id).first()
        if user:
            results.append(
                OrganizationMemberResponse(
                    user_id=user.id,
                    user_name=user.name,
                    user_email=user.email,
                    user_avatar_url=user.avatar_url,
                    role=membership.role,
                    joined_at=membership.joined_at,
                )
            )

    return results


@router.post("", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    organization_id: UUID,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Invite a member to the organization.

    Requires admin role. In a production system, this would send an email invitation.
    For now, it directly adds the user if they exist, or creates a pending invitation.
    """
    # Verify admin access
    require_org_admin(organization_id, current_user, db)

    # Check if organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. User must sign up first before being invited.",
        )

    # Check if user is already a member
    existing_member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization",
        )

    # Add user as member
    membership = OrganizationMember(
        organization_id=organization_id,
        user_id=user.id,
        role=request.role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return OrganizationMemberResponse(
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        user_avatar_url=user.avatar_url,
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.put("/{user_id}", response_model=OrganizationMemberResponse)
async def update_member_role(
    organization_id: UUID,
    user_id: UUID,
    request: UpdateMemberRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a member's role in the organization.

    Requires admin role. Cannot change your own role.
    """
    # Verify admin access
    require_org_admin(organization_id, current_user, db)

    # Cannot change own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    # Get membership
    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # Get user info
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update role
    membership.role = request.role
    db.commit()
    db.refresh(membership)

    return OrganizationMemberResponse(
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        user_avatar_url=user.avatar_url,
        role=membership.role,
        joined_at=membership.joined_at,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    organization_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a member from the organization.

    Requires admin role. Cannot remove yourself if you're the last admin.
    """
    # Verify admin access
    require_org_admin(organization_id, current_user, db)

    # Get membership
    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # If removing self, check if there are other admins
    if user_id == current_user.id:
        admin_count = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.role == MemberRole.ADMIN,
            )
            .count()
        )

        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove yourself as the last admin. Transfer admin role first or delete the organization.",
            )

    db.delete(membership)
    db.commit()

    return None
