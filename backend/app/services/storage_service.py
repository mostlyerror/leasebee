"""Storage service for handling PDF file uploads to S3."""
import os
import uuid
from typing import BinaryIO
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageService:
    """Service for managing PDF file storage in S3."""

    def __init__(self):
        """Initialize S3 client."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def upload_pdf(self, file: BinaryIO, original_filename: str) -> dict:
        """
        Upload a PDF file to S3.

        Args:
            file: File object to upload
            original_filename: Original name of the file

        Returns:
            Dictionary with file metadata including:
            - filename: Generated unique filename
            - file_path: S3 key/path
            - original_filename: Original filename

        Raises:
            Exception: If upload fails
        """
        # Generate unique filename
        file_ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        s3_key = f"leases/{unique_filename}"

        try:
            # Upload to S3
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

        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")

    def download_pdf(self, file_path: str) -> bytes:
        """
        Download a PDF file from S3.

        Args:
            file_path: S3 key/path of the file

        Returns:
            File content as bytes

        Raises:
            Exception: If download fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return response['Body'].read()

        except ClientError as e:
            raise Exception(f"Failed to download file from S3: {str(e)}")

    def delete_pdf(self, file_path: str) -> bool:
        """
        Delete a PDF file from S3.

        Args:
            file_path: S3 key/path of the file

        Returns:
            True if successful

        Raises:
            Exception: If deletion fails
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True

        except ClientError as e:
            raise Exception(f"Failed to delete file from S3: {str(e)}")

    def get_presigned_url(self, file_path: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to a PDF.

        Args:
            file_path: S3 key/path of the file
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL string

        Raises:
            Exception: If URL generation fails
        """
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

        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")


# Singleton instance
storage_service = StorageService()
