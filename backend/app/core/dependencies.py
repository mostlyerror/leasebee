"""FastAPI dependencies for authentication and authorization."""
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import decode_token
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, MemberRole

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: Bearer token credentials
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (alias for get_current_user for clarity)."""
    return current_user


def get_organization_member(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    """
    Verify user is a member of the organization and return membership.

    Args:
        organization_id: Organization UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        OrganizationMember object

    Raises:
        HTTPException: If user is not a member of the organization
    """
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    return member


def require_org_admin(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    """
    Verify user is an admin of the organization.

    Args:
        organization_id: Organization UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        OrganizationMember object

    Raises:
        HTTPException: If user is not an admin of the organization
    """
    member = get_organization_member(organization_id, current_user, db)

    if member.role != MemberRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return member


def require_org_member_or_admin(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    """
    Verify user is a member or admin of the organization (can upload/review).

    Args:
        organization_id: Organization UUID
        current_user: Current authenticated user
        db: Database session

    Returns:
        OrganizationMember object

    Raises:
        HTTPException: If user is a viewer only
    """
    member = get_organization_member(organization_id, current_user, db)

    if member.role == MemberRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Member or Admin access required",
        )

    return member


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user if authenticated, or None if not.

    Useful for endpoints that work both authenticated and unauthenticated.

    Args:
        credentials: Optional bearer token credentials
        db: Database session

    Returns:
        User object or None
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)

        if payload is None or payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == UUID(user_id)).first()
        return user if user and user.is_active else None
    except Exception:
        return None
