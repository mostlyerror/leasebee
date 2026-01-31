"""
Unit tests for the storage service (S3 operations).

These tests verify S3 interactions with mocked boto3 client,
ensuring no actual AWS API calls are made during testing.
"""
import pytest
from io import BytesIO
from botocore.exceptions import ClientError

from app.services.storage_service import StorageService, S3StorageBackend


def _create_test_storage_service():
    """Helper to create storage service with mocked S3 backend for testing."""
    backend = S3StorageBackend(
        bucket_name='test-bucket',
        aws_access_key_id='test-key',
        aws_secret_access_key='test-secret',
        region_name='us-east-1'
    )
    return StorageService(backend)


@pytest.mark.unit
def test_upload_pdf_success(mocker, mock_s3_client):
    """
    Test successful PDF upload to S3.

    Verifies:
    - Unique filename generation with UUID
    - Correct S3 key format (leases/{uuid}.pdf)
    - upload_fileobj called with correct parameters
    - Return value contains expected metadata
    """
    # Mock UUID for predictable filenames
    mock_uuid = mocker.MagicMock()
    mock_uuid.__str__ = mocker.MagicMock(return_value="test-uuid-12345")
    mocker.patch('uuid.uuid4', return_value=mock_uuid)

    # Create storage service with S3 backend
    storage = _create_test_storage_service()

    # Create test file
    test_file = BytesIO(b"test pdf content")
    original_filename = "test_document.pdf"

    # Upload file
    result = storage.upload_pdf(test_file, original_filename)

    # Verify return value
    assert result['filename'] == "test-uuid-12345.pdf"
    assert result['file_path'] == "leases/test-uuid-12345.pdf"
    assert result['original_filename'] == original_filename

    # Verify S3 upload was called correctly
    mock_s3_client.upload_fileobj.assert_called_once()
    call_args = mock_s3_client.upload_fileobj.call_args

    assert call_args[0][0] == test_file  # file object
    assert call_args[0][2] == "leases/test-uuid-12345.pdf"  # S3 key

    # Verify ExtraArgs
    extra_args = call_args[1]['ExtraArgs']
    assert extra_args['ContentType'] == 'application/pdf'
    assert extra_args['ServerSideEncryption'] == 'AES256'


@pytest.mark.unit
def test_upload_pdf_failure(mocker, mock_s3_client):
    """
    Test PDF upload failure handling.

    Verifies that ClientError exceptions are properly caught
    and re-raised with descriptive messages.
    """
    # Make upload_fileobj raise an error
    mock_s3_client.upload_fileobj.side_effect = ClientError(
        {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
        'upload_fileobj'
    )

    storage = _create_test_storage_service()
    test_file = BytesIO(b"test content")

    # Verify exception is raised
    with pytest.raises(Exception) as exc_info:
        storage.upload_pdf(test_file, "test.pdf")

    assert "Failed to upload file to S3" in str(exc_info.value)


@pytest.mark.unit
def test_upload_pdf_preserves_extension(mocker, mock_s3_client):
    """
    Test that file extensions are preserved during upload.

    Verifies different file extensions (.pdf, .PDF) are maintained.
    """
    mock_uuid = mocker.MagicMock()
    mock_uuid.__str__ = mocker.MagicMock(return_value="abc123")
    mocker.patch('uuid.uuid4', return_value=mock_uuid)

    storage = _create_test_storage_service()

    # Test .pdf extension
    test_file = BytesIO(b"content")
    result = storage.upload_pdf(test_file, "document.pdf")
    assert result['filename'] == "abc123.pdf"

    # Test .PDF extension (uppercase)
    test_file = BytesIO(b"content")
    result = storage.upload_pdf(test_file, "DOCUMENT.PDF")
    assert result['filename'] == "abc123.PDF"


@pytest.mark.unit
def test_download_pdf_success(mock_s3_client):
    """
    Test successful PDF download from S3.

    Verifies:
    - get_object called with correct parameters
    - File content is correctly retrieved
    """
    storage = _create_test_storage_service()
    file_path = "leases/test-file.pdf"

    # Download file
    content = storage.download_pdf(file_path)

    # Verify return value
    assert content == b'%PDF-1.4\n%fake pdf content for testing'

    # Verify S3 get_object was called correctly
    mock_s3_client.get_object.assert_called_once_with(
        Bucket=storage.bucket_name,
        Key=file_path
    )


@pytest.mark.unit
def test_download_pdf_failure(mock_s3_client):
    """
    Test PDF download failure handling.

    Verifies that missing files raise appropriate exceptions.
    """
    # Make get_object raise an error
    mock_s3_client.get_object.side_effect = ClientError(
        {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
        'get_object'
    )

    storage = _create_test_storage_service()

    # Verify exception is raised
    with pytest.raises(Exception) as exc_info:
        storage.download_pdf("leases/nonexistent.pdf")

    assert "Failed to download file from S3" in str(exc_info.value)


@pytest.mark.unit
def test_delete_pdf_success(mock_s3_client):
    """
    Test successful PDF deletion from S3.

    Verifies:
    - delete_object called with correct parameters
    - Returns True on success
    """
    storage = _create_test_storage_service()
    file_path = "leases/test-file.pdf"

    # Delete file
    result = storage.delete_pdf(file_path)

    # Verify return value
    assert result is True

    # Verify S3 delete_object was called correctly
    mock_s3_client.delete_object.assert_called_once_with(
        Bucket=storage.bucket_name,
        Key=file_path
    )


@pytest.mark.unit
def test_delete_pdf_failure(mock_s3_client):
    """
    Test PDF deletion failure handling.
    """
    # Make delete_object raise an error
    mock_s3_client.delete_object.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
        'delete_object'
    )

    storage = _create_test_storage_service()

    # Verify exception is raised
    with pytest.raises(Exception) as exc_info:
        storage.delete_pdf("leases/test.pdf")

    assert "Failed to delete file from S3" in str(exc_info.value)


@pytest.mark.unit
def test_get_presigned_url_success(mock_s3_client):
    """
    Test presigned URL generation.

    Verifies:
    - generate_presigned_url called with correct parameters
    - Default expiration is 3600 seconds
    - Custom expiration can be specified
    """
    storage = _create_test_storage_service()
    file_path = "leases/test-file.pdf"

    # Test default expiration
    url = storage.get_presigned_url(file_path)

    assert url == "https://fake-s3-url.com/test.pdf"
    mock_s3_client.generate_presigned_url.assert_called_once_with(
        'get_object',
        Params={
            'Bucket': storage.bucket_name,
            'Key': file_path
        },
        ExpiresIn=3600
    )

    # Reset mock
    mock_s3_client.reset_mock()

    # Test custom expiration
    url = storage.get_presigned_url(file_path, expiration=7200)

    mock_s3_client.generate_presigned_url.assert_called_once_with(
        'get_object',
        Params={
            'Bucket': storage.bucket_name,
            'Key': file_path
        },
        ExpiresIn=7200
    )


@pytest.mark.unit
def test_get_presigned_url_failure(mock_s3_client):
    """
    Test presigned URL generation failure handling.
    """
    # Make generate_presigned_url raise an error
    mock_s3_client.generate_presigned_url.side_effect = ClientError(
        {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
        'generate_presigned_url'
    )

    storage = _create_test_storage_service()

    # Verify exception is raised
    with pytest.raises(Exception) as exc_info:
        storage.get_presigned_url("leases/test.pdf")

    assert "Failed to generate presigned URL" in str(exc_info.value)


@pytest.mark.unit
def test_storage_service_singleton():
    """
    Test that storage_service is properly initialized as a singleton.
    """
    from app.services.storage_service import storage_service

    assert storage_service is not None
    assert isinstance(storage_service, StorageService)
    assert hasattr(storage_service, 'backend')
    # Backend should have either local_path or s3_client depending on config
    assert hasattr(storage_service.backend, 'upload_pdf')


@pytest.mark.unit
def test_filename_uniqueness(mocker, mock_s3_client):
    """
    Test that each upload generates a unique filename.

    Verifies UUID generation ensures no filename collisions.
    """
    # Create multiple unique UUIDs
    mock_uuids = []
    for i in range(3):
        mock = mocker.MagicMock()
        mock.__str__ = mocker.MagicMock(return_value=f"uuid-{i}")
        mock_uuids.append(mock)

    uuid_call_count = [0]

    def uuid_side_effect():
        result = mock_uuids[uuid_call_count[0]]
        uuid_call_count[0] += 1
        return result

    mocker.patch('uuid.uuid4', side_effect=uuid_side_effect)

    storage = _create_test_storage_service()

    # Upload three files
    filenames = []
    for i in range(3):
        test_file = BytesIO(b"content")
        result = storage.upload_pdf(test_file, f"test{i}.pdf")
        filenames.append(result['filename'])

    # Verify all filenames are unique
    assert len(set(filenames)) == 3
    assert filenames[0] == "uuid-0.pdf"
    assert filenames[1] == "uuid-1.pdf"
    assert filenames[2] == "uuid-2.pdf"


@pytest.mark.unit
def test_s3_key_format(mocker, mock_s3_client):
    """
    Test that S3 keys follow the correct format: leases/{uuid}{ext}.

    This ensures consistent file organization in S3.
    """
    mock_uuid = mocker.MagicMock()
    mock_uuid.__str__ = mocker.MagicMock(return_value="test-123")
    mocker.patch('uuid.uuid4', return_value=mock_uuid)

    storage = _create_test_storage_service()
    test_file = BytesIO(b"content")

    result = storage.upload_pdf(test_file, "document.pdf")

    # Verify S3 key format
    assert result['file_path'].startswith("leases/")
    assert result['file_path'] == "leases/test-123.pdf"

    # Verify the actual upload call used this key
    call_args = mock_s3_client.upload_fileobj.call_args
    assert call_args[0][2] == "leases/test-123.pdf"
