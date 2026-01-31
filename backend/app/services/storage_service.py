"""Storage service for handling PDF file uploads - supports S3 and local storage."""
import os
import uuid
from typing import BinaryIO
from pathlib import Path
from abc import ABC, abstractmethod

from app.core.config import settings


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def upload_pdf(self, file: BinaryIO, original_filename: str) -> dict:
        """Upload a PDF file to storage."""
        pass
    
    @abstractmethod
    def download_pdf(self, file_path: str) -> bytes:
        """Download a PDF file from storage."""
        pass
    
    @abstractmethod
    def delete_pdf(self, file_path: str) -> bool:
        """Delete a PDF file from storage."""
        pass
    
    @abstractmethod
    def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for temporary access to a PDF."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local file storage backend for development."""
    
    def __init__(self, storage_path: Path = Path('/tmp/leasebee_uploads')):
        """Initialize local storage backend.
        
        Args:
            storage_path: Path to local storage directory
        """
        self.local_path = storage_path
        self.local_path.mkdir(parents=True, exist_ok=True)
        self.bucket_name = 'local-bucket'
    
    def upload_pdf(self, file: BinaryIO, original_filename: str) -> dict:
        """Upload a PDF file to local storage."""
        file_ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
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
    
    def download_pdf(self, file_path: str) -> bytes:
        """Download a PDF file from local storage."""
        local_file_path = self.local_path / file_path
        try:
            with open(local_file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to download file locally: {str(e)}")
    
    def delete_pdf(self, file_path: str) -> bool:
        """Delete a PDF file from local storage."""
        local_file_path = self.local_path / file_path
        try:
            if local_file_path.exists():
                local_file_path.unlink()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file locally: {str(e)}")
    
    def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """Generate a file URL for local storage."""
        local_file_path = self.local_path / file_path
        return f"file://{local_file_path}"


class S3StorageBackend(StorageBackend):
    """S3 storage backend for production."""
    
    def __init__(self, bucket_name: str, aws_access_key_id: str, 
                 aws_secret_access_key: str, region_name: str):
        """Initialize S3 storage backend.
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region name
        """
        import boto3
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )
        self.bucket_name = bucket_name
    
    def upload_pdf(self, file: BinaryIO, original_filename: str) -> dict:
        """Upload a PDF file to S3."""
        file_ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
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
        """Download a PDF file from S3."""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return response['Body'].read()
        except Exception as e:
            raise Exception(f"Failed to download file from S3: {str(e)}")
    
    def delete_pdf(self, file_path: str) -> bool:
        """Delete a PDF file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file from S3: {str(e)}")
    
    def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for S3."""
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


class StorageService:
    """Service for managing PDF file storage."""

    def __init__(self, backend: StorageBackend):
        """Initialize storage service with a backend.
        
        Args:
            backend: Storage backend implementation
        """
        self.backend = backend

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
        return self.backend.upload_pdf(file, original_filename)

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
        return self.backend.download_pdf(file_path)

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
        return self.backend.delete_pdf(file_path)

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
        return self.backend.get_presigned_url(file_path, expiration)


def create_storage_service() -> StorageService:
    """Factory function to create a storage service with the appropriate backend.
    
    Returns:
        StorageService configured with either local or S3 backend
    """
    use_local = settings.ENVIRONMENT == 'development' and settings.AWS_ACCESS_KEY_ID == 'test'
    
    if use_local:
        backend = LocalStorageBackend()
    else:
        backend = S3StorageBackend(
            bucket_name=settings.S3_BUCKET_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
    
    return StorageService(backend)


# Singleton instance - created using factory
storage_service = create_storage_service()
