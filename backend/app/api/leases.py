"""Lease API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import os

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_optional_user, get_current_user
from app.models.lease import Lease, LeaseStatus
from app.models.user import User
from app.schemas.pydantic_schemas import LeaseResponse
from app.services.storage_service import get_storage_service, StorageService
from app.services.pdf_service import pdf_service

router = APIRouter()


@router.post("/upload", response_model=LeaseResponse, status_code=status.HTTP_201_CREATED)
async def upload_lease(
    file: UploadFile = File(...),
    organization_id: Optional[UUID] = Query(None, description="Organization ID (required if authenticated)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Upload a lease PDF file.

    If authenticated, organization_id is required and the lease will be associated with that organization.
    If not authenticated, creates a lease without organization (for backward compatibility).

    Args:
        file: PDF file to upload
        organization_id: Organization ID (required if authenticated)
        db: Database session
        current_user: Current user (optional)

    Returns:
        Created lease object

    Raises:
        HTTPException: If file validation fails or upload fails
    """
    # If authenticated, require organization_id
    if current_user and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id is required when authenticated"
        )

    # If organization_id provided, verify user has access
    if current_user and organization_id:
        from app.core.dependencies import get_organization_member
        get_organization_member(organization_id, current_user, db)
    # Validate file type
    if file.content_type not in settings.allowed_file_types_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {settings.ALLOWED_FILE_TYPES}"
        )

    # Read file
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file size
    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Validate it's a valid PDF and get page count
    try:
        pdf_info = pdf_service.extract_text_from_bytes(file_content)
        page_count = pdf_info['page_count']
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid PDF file: {str(e)}"
        )

    # Upload to storage
    try:
        # Reset file pointer
        await file.seek(0)
        storage_result = storage_service.upload_pdf(file.file, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

    # Create lease record
    lease = Lease(
        filename=storage_result['filename'],
        original_filename=storage_result['original_filename'],
        file_size=file_size,
        file_path=storage_result['file_path'],
        content_type=file.content_type,
        page_count=page_count,
        status=LeaseStatus.UPLOADED,
        organization_id=organization_id if current_user else None,
        uploaded_by=current_user.id if current_user else None,
    )

    db.add(lease)
    db.commit()
    db.refresh(lease)

    return lease


@router.get("/", response_model=List[LeaseResponse])
async def list_leases(
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[UUID] = Query(None, description="Filter by organization ID"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    List leases.

    If authenticated with organization_id, returns leases for that organization.
    If not authenticated, returns all leases (for backward compatibility).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        organization_id: Filter by organization ID
        db: Database session
        current_user: Current user (optional)

    Returns:
        List of lease objects
    """
    query = db.query(Lease)

    # If user is authenticated and organization_id is provided, filter by organization
    if current_user and organization_id:
        from app.core.dependencies import get_organization_member
        get_organization_member(organization_id, current_user, db)
        query = query.filter(Lease.organization_id == organization_id)

    leases = query.order_by(Lease.created_at.desc()).offset(skip).limit(limit).all()
    return leases


@router.get("/{lease_id}", response_model=LeaseResponse)
async def get_lease(
    lease_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get a specific lease by ID.

    If authenticated, verifies user has access to the lease's organization.

    Args:
        lease_id: Lease ID
        db: Database session
        current_user: Current user (optional)

    Returns:
        Lease object

    Raises:
        HTTPException: If lease not found or access denied
    """
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found"
        )

    # If user is authenticated and lease has organization, verify access
    if current_user and lease.organization_id:
        from app.core.dependencies import get_organization_member
        get_organization_member(lease.organization_id, current_user, db)

    return lease


@router.delete("/{lease_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lease(
    lease_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Delete a lease and its associated file.

    If authenticated, verifies user has access to the lease's organization.

    Args:
        lease_id: Lease ID
        db: Database session
        current_user: Current user (optional)

    Raises:
        HTTPException: If lease not found or access denied
    """
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found"
        )

    # If user is authenticated and lease has organization, verify access
    if current_user and lease.organization_id:
        from app.core.dependencies import get_organization_member
        get_organization_member(lease.organization_id, current_user, db)

    # Delete from storage
    try:
        storage_service.delete_pdf(lease.file_path)
    except Exception:
        pass  # Continue even if S3 deletion fails

    # Delete from database (cascade will delete related records)
    db.delete(lease)
    db.commit()

    return None


@router.get("/{lease_id}/download-url")
async def get_download_url(
    lease_id: int,
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get a presigned URL for downloading the lease PDF.

    Args:
        lease_id: Lease ID
        db: Database session

    Returns:
        Presigned URL with expiration

    Raises:
        HTTPException: If lease not found
    """
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found"
        )

    try:
        url = storage_service.get_presigned_url(lease.file_path)
        return {
            "url": url,
            "expires_in": 3600,  # 1 hour
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.get("/{lease_id}/pdf")
async def get_lease_pdf(
    lease_id: int,
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get the lease PDF file directly.
    
    This endpoint streams the PDF file content, allowing it to be displayed
    in the browser's PDF viewer.
    
    Args:
        lease_id: Lease ID
        db: Database session
        
    Returns:
        PDF file as a streaming response
        
    Raises:
        HTTPException: If lease not found or file cannot be read
    """
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found"
        )
    
    try:
        # Download PDF bytes from storage
        pdf_bytes = storage_service.download_pdf(lease.file_path)
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{lease.original_filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve PDF: {str(e)}"
        )
