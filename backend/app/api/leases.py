"""Lease API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
import os

from app.core.database import get_db
from app.core.config import settings
from app.models.lease import Lease, LeaseStatus
from app.schemas.pydantic_schemas import LeaseResponse
from app.services.storage_service import storage_service
from app.services.pdf_service import pdf_service

router = APIRouter()


@router.post("/upload", response_model=LeaseResponse, status_code=status.HTTP_201_CREATED)
async def upload_lease(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a lease PDF file.

    Args:
        file: PDF file to upload
        db: Database session

    Returns:
        Created lease object

    Raises:
        HTTPException: If file validation fails or upload fails
    """
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
    )

    db.add(lease)
    db.commit()
    db.refresh(lease)

    return lease


@router.get("/", response_model=List[LeaseResponse])
async def list_leases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all leases.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of lease objects
    """
    leases = db.query(Lease).order_by(Lease.created_at.desc()).offset(skip).limit(limit).all()
    return leases


@router.get("/{lease_id}", response_model=LeaseResponse)
async def get_lease(
    lease_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific lease by ID.

    Args:
        lease_id: Lease ID
        db: Database session

    Returns:
        Lease object

    Raises:
        HTTPException: If lease not found
    """
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found"
        )
    return lease


@router.delete("/{lease_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lease(
    lease_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a lease and its associated file.

    Args:
        lease_id: Lease ID
        db: Database session

    Raises:
        HTTPException: If lease not found
    """
    lease = db.query(Lease).filter(Lease.id == lease_id).first()
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found"
        )

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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
