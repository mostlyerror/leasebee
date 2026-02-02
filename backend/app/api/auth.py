"""Authentication API endpoints."""
from datetime import timedelta
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.models.organization import Organization, SubscriptionPlan
from app.models.organization_member import OrganizationMember, MemberRole
from app.schemas.auth import (
    UserSignupRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    UserWithTokenResponse,
    UserResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a name."""
    slug = name.lower().replace(" ", "-")
    # Remove special characters
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Add random suffix to ensure uniqueness
    slug = f"{slug}-{str(uuid4())[:8]}"
    return slug


@router.post("/signup", response_model=UserWithTokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: UserSignupRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user and optionally create an organization.

    If organization_name is provided, creates a new organization with the user as admin.
    Otherwise, user is created without an organization (must be invited to one).
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    hashed_password = get_password_hash(request.password)
    user = User(
        email=request.email,
        name=request.name,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False,  # Would implement email verification in production
    )
    db.add(user)
    db.flush()  # Get user.id without committing

    # Create organization if requested
    if request.organization_name:
        org_slug = generate_slug(request.organization_name)
        organization = Organization(
            name=request.organization_name,
            slug=org_slug,
            plan=SubscriptionPlan.FREE,
        )
        db.add(organization)
        db.flush()

        # Add user as admin of the organization
        membership = OrganizationMember(
            organization_id=organization.id,
            user_id=user.id,
            role=MemberRole.ADMIN,
        )
        db.add(membership)

    db.commit()
    db.refresh(user)

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return UserWithTokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=UserWithTokenResponse)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user and return tokens."""
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return UserWithTokenResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token."""
    # Decode refresh token
    payload = decode_token(request.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify user exists and is active
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Generate new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout user.

    Note: With JWT, actual logout happens client-side by discarding tokens.
    This endpoint is for compatibility and could be extended to maintain
    a token blacklist in production.
    """
    return {"message": "Successfully logged out"}
