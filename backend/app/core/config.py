"""Application configuration settings."""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "LeaseBee API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str

    # Authentication
    JWT_SECRET_KEY: str | None = None  # Falls back to SECRET_KEY if not set
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str

    # Anthropic API
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: str = "application/pdf"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Parse allowed file types."""
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]

    @property
    def jwt_secret(self) -> str:
        """Get JWT secret key, falling back to SECRET_KEY."""
        return self.JWT_SECRET_KEY or self.SECRET_KEY

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
