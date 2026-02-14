"""Storage service for handling PDF file uploads - supports S3 and local storage."""
import os
import uuid
from typing import BinaryIO
from pathlib import Path

from app.core.config import settings

# Determine storage backend
USE_LOCAL_STORAGE = settings.ENVIRONMENT == 'development' and settings.AWS_ACCESS_KEY_ID == 'test'

if USE_LOCAL_STORAGE:
    # Local file storage for development — project-relative so files survive reboots
    LOCAL_STORAGE_PATH = Path(__file__).resolve().parents[2] / 'uploads'
    LOCAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
else:
    # S3 storage for production
    import boto3
    from botocore.exceptions import ClientError


class StorageService:
    """Service for managing PDF file storage."""

    def __init__(self):
        """Initialize storage backend."""
        if USE_LOCAL_STORAGE:
            self.local_path = LOCAL_STORAGE_PATH
            self.bucket_name = 'local-bucket'
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            self.bucket_name = settings.S3_BUCKET_NAME

    def upload_pdf(self, file: BinaryIO, original_filename: str) -> dict:
        """
        Upload a PDF file to storage.

        Args:
            file: File object to upload
            original_filename: Original name of the file

        Returns:
            Dictionary with file metadata including:
            - filename: Generated unique filename
            - file_path: Storage key/path
            - original_filename: Original filename

        Raises:
            Exception: If upload fails
        """
        # Generate unique filename
        file_ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        if USE_LOCAL_STORAGE:
            # Local file storage
            s3_key = f"leases/{unique_filename}"
            local_file_path = self.local_path / s3_key
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                file.seek(0)
                with open(local_file_path, 'wb') as f:
                    f.write(file.read())
                
                return {
                    'filename': unique_filename,
                    'file_path': s3_key,
                    'original_filename': original_filename,
                }
            except Exception as e:
                raise Exception(f"Failed to upload file locally: {str(e)}")
        else:
            # S3 storage
            s3_key = f"leases/{unique_filename}"
            
            try:
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': 'application/pdf',
                        'ServerSideEncryption': 'AES256',
                    }
                )
                
                return {
                    'filename': unique_filename,
                    'file_path': s3_key,
                    'original_filename': original_filename,
                }
            except Exception as e:
                raise Exception(f"Failed to upload file to S3: {str(e)}")

    def download_pdf(self, file_path: str) -> bytes:
        """
        Download a PDF file from storage.

        Args:
            file_path: Storage key/path of the file

        Returns:
            File content as bytes

        Raises:
            Exception: If download fails
        """
        if USE_LOCAL_STORAGE:
            local_file_path = self.local_path / file_path
            try:
                with open(local_file_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                raise Exception(f"Failed to download file locally: {str(e)}")
        else:
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                return response['Body'].read()
            except Exception as e:
                raise Exception(f"Failed to download file from S3: {str(e)}")

    def delete_pdf(self, file_path: str) -> bool:
        """
        Delete a PDF file from storage.

        Args:
            file_path: Storage key/path of the file

        Returns:
            True if successful

        Raises:
            Exception: If deletion fails
        """
        if USE_LOCAL_STORAGE:
            local_file_path = self.local_path / file_path
            try:
                if local_file_path.exists():
                    local_file_path.unlink()
                return True
            except Exception as e:
                raise Exception(f"Failed to delete file locally: {str(e)}")
        else:
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                return True
            except Exception as e:
                raise Exception(f"Failed to delete file from S3: {str(e)}")

    def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to a PDF.

        Args:
            file_path: Storage key/path of the file
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL string

        Raises:
            Exception: If URL generation fails
        """
        if USE_LOCAL_STORAGE:
            # For local storage, return a local file URL
            local_file_path = self.local_path / file_path
            return f"file://{local_file_path}"
        else:
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_path
                    },
                    ExpiresIn=expiration
                )
                return url
            except Exception as e:
                raise Exception(f"Failed to generate presigned URL: {str(e)}")


# Singleton instance
storage_service = StorageService()
