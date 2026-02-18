"""Unit tests for S3WriteClient."""

from typing import Any, Dict, cast

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException

from app.core.clients.write.s3_write_client import S3WriteClient


class TestS3WriteClient:
    """Test cases for S3WriteClient class."""

    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client for testing."""
        client = MagicMock()

        # These methods are async
        client.put_object = AsyncMock()
        client.head_bucket = AsyncMock()
        client.delete_object = AsyncMock()
        client.create_multipart_upload = AsyncMock()
        client.upload_part = AsyncMock()
        client.complete_multipart_upload = AsyncMock()
        client.abort_multipart_upload = AsyncMock()

        return client

    @pytest.fixture
    def mock_session(self, mock_s3_client):
        """Create a mock aioboto3 session."""
        session = MagicMock()
        # Mock the async context manager for session.client()
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__.return_value = mock_s3_client
        async_context_manager.__aexit__.return_value = None
        session.client.return_value = async_context_manager
        return session

    @pytest.fixture
    def s3_config(self):
        """Default S3 configuration for testing."""
        return {
            "bucket_name": "test-bucket",
            "prefix": "uploads",
            "access_key_id": "test_access_key",
            "secret_access_key": "test_secret_key",
            "region_name": "us-east-1",
            "endpoint_url": "https://s3.amazonaws.com",
        }

    @pytest.fixture
    def write_client(self, s3_config):
        """Create S3WriteClient instance for testing."""
        return S3WriteClient(**s3_config)

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return b"Hello, S3! This is test content for S3 writing."

    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return {
            "content_type": "text/plain",
            "tags": {"source": "test", "type": "sample"},
            "meta_original_filename": "test.txt",
            "meta_upload_source": "unit_test",
            "cache_control": "max-age=3600",
        }

    @pytest.mark.asyncio
    async def test_write_file_content_success(
        self,
        write_client,
        mock_session,
        mock_s3_client,
        sample_content,
        sample_metadata,
    ):
        """Test successful file write to S3."""
        resource_path = "test_files/sample.txt"

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            result = await write_client.write_file_content(
                resource_path=resource_path,
                content=sample_content,
                metadata=sample_metadata,
            )

        # Verify S3 put_object was called with correct parameters
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args[1]

        assert call_args["Bucket"] == "test-bucket"
        assert call_args["Key"] == "uploads/test_files/sample.txt"
        assert call_args["Body"] == sample_content
        assert call_args["ContentType"] == "text/plain"
        assert call_args["CacheControl"] == "max-age=3600"
        assert "original_filename" in call_args["Metadata"]
        assert call_args["Tagging"] == "source=test&type=sample"

        # Verify return result
        assert result["bucket"] == "test-bucket"
        assert result["key"] == "uploads/test_files/sample.txt"
        assert result["size"] == len(sample_content)
        assert result["client"] == "S3Write"
        assert "checksum" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_write_file_content_no_prefix(
        self, mock_session, mock_s3_client, sample_content
    ):
        """Test file write without prefix."""
        # Create client without prefix
        write_client = S3WriteClient(
            bucket_name="test-bucket",
            access_key_id="test_key",
            secret_access_key="test_secret",
        )

        resource_path = "direct_file.txt"

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            await write_client.write_file_content(
                resource_path=resource_path, content=sample_content
            )

        # Verify S3 key has no prefix
        call_args = mock_s3_client.put_object.call_args[1]
        assert call_args["Key"] == "direct_file.txt"

    @pytest.mark.asyncio
    async def test_write_file_content_allowed_prefixes_success(
        self, mock_session, mock_s3_client, sample_content
    ):
        """Test write with allowed prefixes - success case."""
        write_client = S3WriteClient(
            bucket_name="test-bucket",
            prefix="data",
            allowed_prefixes=["data/uploads", "data/temp"],
        )

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            await write_client.write_file_content(
                resource_path="uploads/test.txt", content=sample_content
            )

        # Should succeed
        mock_s3_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_file_content_allowed_prefixes_denied(
        self, write_client, sample_content
    ):
        """Test write with allowed prefixes - access denied."""
        # Set allowed prefixes that don't match our path
        write_client.allowed_prefixes = ["uploads/restricted"]

        with pytest.raises(HTTPException) as exc_info:
            await write_client.write_file_content(
                resource_path="test_files/sample.txt", content=sample_content
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_write_file_content_file_size_limit(self, write_client):
        """Test file size limit enforcement."""
        with patch("app.core.clients.write.s3_write_client.MAX_FILE_SIZE", 100):
            large_content = b"x" * 200  # 200 bytes - exceeds limit

            with pytest.raises(HTTPException) as exc_info:
                await write_client.write_file_content(
                    resource_path="large_file.txt", content=large_content
                )

            assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_write_file_content_s3_client_error(
        self, write_client, mock_session, mock_s3_client, sample_content
    ):
        """Test handling of S3 client errors."""
        # Mock S3 client error
        error_response = {"Error": {"Code": "NoSuchBucket"}}
        mock_s3_client.put_object.side_effect = ClientError(error_response, "PutObject")

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await write_client.write_file_content(
                    resource_path="test.txt", content=sample_content
                )

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_write_file_content_access_denied(
        self, write_client, mock_session, mock_s3_client, sample_content
    ):
        """Test S3 access denied error."""
        error_response = {"Error": {"Code": "AccessDenied"}}
        mock_s3_client.put_object.side_effect = ClientError(error_response, "PutObject")

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await write_client.write_file_content(
                    resource_path="test.txt", content=sample_content
                )

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_write_file_content_no_credentials(
        self, write_client, mock_session, mock_s3_client, sample_content
    ):
        """Test S3 no credentials error."""
        mock_s3_client.put_object.side_effect = NoCredentialsError()

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await write_client.write_file_content(
                    resource_path="test.txt", content=sample_content
                )

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_write_stream_success(
        self, write_client, mock_session, mock_s3_client, sample_metadata
    ):
        """Test successful stream write to S3."""
        resource_path = "stream_files/sample_stream.txt"

        # Mock multipart upload responses
        mock_s3_client.create_multipart_upload.return_value = {
            "UploadId": "test-upload-id"
        }
        mock_s3_client.upload_part.return_value = {"ETag": '"test-etag"'}

        # Create async generator for content chunks
        async def content_stream():
            # Create chunks larger than MIN_PART_SIZE for multipart upload
            large_chunk = b"x" * (6 * 1024 * 1024)  # 6MB chunk
            yield large_chunk
            yield b"Final chunk"

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            result = await write_client.write_stream(
                resource_path=resource_path,
                content_stream=content_stream(),
                metadata=sample_metadata,
            )

        # Verify multipart upload flow
        mock_s3_client.create_multipart_upload.assert_called_once()
        mock_s3_client.upload_part.assert_called()
        mock_s3_client.complete_multipart_upload.assert_called_once()

        # Verify return result
        assert result["bucket"] == "test-bucket"
        assert result["key"] == "uploads/stream_files/sample_stream.txt"
        assert result["client"] == "S3Write"
        assert "parts_count" in result
        assert result["parts_count"] == 2  # Two parts uploaded

    @pytest.mark.asyncio
    async def test_write_stream_small_file_single_part(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test stream write with small file (single part)."""
        # Mock multipart upload responses
        mock_s3_client.create_multipart_upload.return_value = {
            "UploadId": "test-upload-id"
        }
        mock_s3_client.upload_part.return_value = {"ETag": '"test-etag"'}

        # Create small content stream
        async def small_content_stream():
            yield b"Small content chunk 1"
            yield b"Small content chunk 2"

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            result = await write_client.write_stream(
                resource_path="small_file.txt", content_stream=small_content_stream()
            )

        # Should still complete multipart upload with single part
        mock_s3_client.create_multipart_upload.assert_called_once()
        mock_s3_client.upload_part.assert_called_once()
        mock_s3_client.complete_multipart_upload.assert_called_once()
        assert result["parts_count"] == 1

    @pytest.mark.asyncio
    async def test_write_stream_empty_stream(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test write_stream with empty stream."""
        mock_s3_client.reset_mock()  # Reset mock call counts
        mock_s3_client.create_multipart_upload.return_value = {
            "UploadId": "test-upload-id"
        }

        async def empty_stream():
            return
            yield  # Never reached

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await write_client.write_stream(
                    resource_path="empty.txt", content_stream=empty_stream()
                )

        assert exc_info.value.status_code == 400
        assert "No data received" in exc_info.value.detail
        # Should abort multipart upload (called twice - once in specific error,
        # once in general handler)
        assert mock_s3_client.abort_multipart_upload.call_count == 2

    @pytest.mark.asyncio
    async def test_write_stream_size_limit_exceeded(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test stream write with size limit exceeded."""
        mock_s3_client.reset_mock()  # Reset mock call counts
        mock_s3_client.create_multipart_upload.return_value = {
            "UploadId": "test-upload-id"
        }

        with patch("app.core.clients.write.s3_write_client.MAX_FILE_SIZE", 100):

            async def large_stream():
                # Generate chunks that exceed limit
                for i in range(10):
                    yield b"x" * 20  # 20 bytes each, total 200 bytes

            with patch(
                "app.core.clients.write.s3_write_client.aioboto3.Session",
                return_value=mock_session,
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await write_client.write_stream(
                        resource_path="large_stream.txt", content_stream=large_stream()
                    )

                assert exc_info.value.status_code == 413
                # Should abort multipart upload (called twice - once in
                # specific error, once in general handler)
                assert mock_s3_client.abort_multipart_upload.call_count == 2

    @pytest.mark.asyncio
    async def test_write_stream_upload_part_error(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test stream write with upload part error."""
        mock_s3_client.create_multipart_upload.return_value = {
            "UploadId": "test-upload-id"
        }
        mock_s3_client.upload_part.side_effect = ClientError(
            {"Error": {"Code": "InternalError"}}, "UploadPart"
        )

        async def content_stream():
            yield b"x" * (6 * 1024 * 1024)  # 6MB chunk

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await write_client.write_stream(
                    resource_path="error_test.txt", content_stream=content_stream()
                )

            assert exc_info.value.status_code == 500
            # Should attempt to abort multipart upload
            mock_s3_client.abort_multipart_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test successful health check."""
        # Mock successful head_bucket and put/delete operations
        mock_s3_client.head_bucket.return_value = {}
        mock_s3_client.put_object.return_value = {}
        mock_s3_client.delete_object.return_value = {}

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            result = await write_client.health_check()

        assert result["status"] == "healthy"
        assert result["client"] == "S3Write"
        assert result["bucket"] == "test-bucket"
        assert result["writable"] is True
        assert "timestamp" in result

        # Verify test operations
        mock_s3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")
        mock_s3_client.put_object.assert_called_once()
        mock_s3_client.delete_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_bucket_not_found(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test health check with bucket not found."""
        error_response = {"Error": {"Code": "NoSuchBucket"}}
        mock_s3_client.head_bucket.side_effect = ClientError(
            error_response, "HeadBucket"
        )

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            result = await write_client.health_check()

        assert result["status"] == "unhealthy"
        assert result["client"] == "S3Write"
        assert "does not exist" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_access_denied(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test health check with access denied."""
        error_response = {"Error": {"Code": "AccessDenied"}}
        mock_s3_client.head_bucket.side_effect = ClientError(
            error_response, "HeadBucket"
        )

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            result = await write_client.health_check()

        assert result["status"] == "unhealthy"
        assert result["client"] == "S3Write"
        assert "Access denied" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_write_permission_denied(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test health check when bucket exists but write permission denied."""
        # Head bucket succeeds but put_object fails
        mock_s3_client.head_bucket.return_value = {}
        error_response = {"Error": {"Code": "AccessDenied"}}
        mock_s3_client.put_object.side_effect = ClientError(error_response, "PutObject")

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            result = await write_client.health_check()

        assert result["status"] == "unhealthy"
        assert result["client"] == "S3Write"
        assert "Cannot write" in result["error"]

    @pytest.mark.asyncio
    async def test_health_check_no_credentials(
        self, write_client, mock_session, mock_s3_client
    ):
        """Test health check with no credentials."""
        mock_s3_client.head_bucket.side_effect = NoCredentialsError()

        with patch(
            "app.core.clients.write.s3_write_client.aioboto3.Session",
            return_value=mock_session,
        ):
            result = await write_client.health_check()

        assert result["status"] == "unhealthy"
        assert result["client"] == "S3Write"
        assert "credentials not found" in result["error"]

    def test_client_initialization(self):
        """Test client initialization with various parameters."""
        # Test minimal initialization
        client = S3WriteClient(bucket_name="test-bucket")
        assert client.bucket_name == "test-bucket"
        assert client.prefix == ""
        assert client.client_name == "S3Write"
        assert client.allowed_prefixes == []

        # Test full initialization
        client = S3WriteClient(
            bucket_name="test-bucket",
            prefix="data/uploads/",
            access_key_id="key",
            secret_access_key="secret",
            session_token="token",
            region_name="eu-west-1",
            endpoint_url="https://custom.endpoint.com",
            allowed_prefixes=["data/uploads/public", "data/uploads/temp"],
        )
        assert client.prefix == "data/uploads"  # Trailing slash removed
        assert len(client.allowed_prefixes) == 2
        assert client.s3_config["aws_access_key_id"] == "key"
        assert client.s3_config["endpoint_url"] == "https://custom.endpoint.com"

    def test_resolve_s3_key(self, write_client):
        """Test S3 key resolution."""
        # Test normal path
        key = write_client._resolve_s3_key("test/file.txt")
        assert key == "uploads/test/file.txt"

        # Test path with leading/trailing slashes
        key = write_client._resolve_s3_key("/test/file.txt/")
        assert key == "uploads/test/file.txt"

        # Test with no prefix client
        no_prefix_client = S3WriteClient(bucket_name="test")
        key = no_prefix_client._resolve_s3_key("direct.txt")
        assert key == "direct.txt"

    def test_calculate_checksum(self, write_client):
        """Test checksum calculation."""
        content = b"test content"
        checksum = write_client._calculate_checksum(content)

        # Verify it's a valid MD5 hash
        assert len(checksum) == 32
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_apply_metadata(self, write_client, sample_metadata):
        """Test metadata application to upload parameters."""
        upload_params = {"Bucket": "test", "Key": "test"}
        write_client._apply_metadata(upload_params, sample_metadata)

        # Check content type
        assert upload_params["ContentType"] == "text/plain"

        # Check cache control
        assert upload_params["CacheControl"] == "max-age=3600"

        # Check custom metadata (meta_ prefix removed)
        metadata = cast(Dict[str, Any], upload_params.get("Metadata", {}))
        assert "original_filename" in metadata
        assert metadata["upload_source"] == "unit_test"

        # Check tags
        assert upload_params["Tagging"] == "source=test&type=sample"
