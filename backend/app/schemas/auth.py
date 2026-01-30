"""Authentication schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# Request Schemas
class UserSignupRequest(BaseModel):
    """User signup request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    organization_name: Optional[str] = Field(None, min_length=1, max_length=255)


class UserLoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


# Response Schemas
class TokenResponse(BaseModel):
    """Token response with access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithTokenResponse(BaseModel):
    """User response with tokens."""

    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
