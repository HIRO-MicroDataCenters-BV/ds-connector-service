"""Unit tests for S3DataClient."""

from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import quote

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException

from app.core.clients.read.s3_read_client import S3DataClient
from app.rest_api.serializers import DataProductDistribution


class TestS3DataClient:
    """Test cases for S3DataClient class."""

    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client for testing."""
        # Use MagicMock for most methods that return values,
        # AsyncMock only for async methods
        client = MagicMock()

        # These methods are async and return values directly
        client.head_object = AsyncMock()
        client.get_object = AsyncMock()
        client.head_bucket = AsyncMock()
        client.list_objects_v2 = AsyncMock()

        # get_paginator is NOT async and returns an object
        client.get_paginator = MagicMock()

        return client

    @pytest.fixture
    def mock_session(self, mock_s3_client):
        """Create a mock aioboto3 session."""
        session = AsyncMock()
        session.client.return_value.__aenter__.return_value = mock_s3_client
        return session

    @pytest.fixture
    def s3_config(self):
        """Default S3 configuration for testing."""
        return {
            "bucket_name": "test-bucket",
            "prefix": "data",
            "access_key_id": "test_access_key",
            "secret_access_key": "test_secret_key",
            "region_name": "us-east-1",
            "endpoint_url": "http://localhost:9000",
        }

    @pytest.fixture
    def client(self, s3_config):
        """Create an S3DataClient instance for testing."""
        return S3DataClient(**s3_config)

    @pytest.fixture
    def sample_s3_object(self):
        """Create sample S3 object metadata."""
        return {
            "ContentLength": 1024,
            "LastModified": "2023-01-01T00:00:00+00:00",
            "ETag": '"abc123"',
            "ContentType": "text/plain",
        }

    @pytest.fixture
    def sample_distribution(self):
        """Create a sample DataProductDistribution for testing."""
        return DataProductDistribution(
            title="test.txt",
            description="S3 object test.txt",
            access_url="s3://test-bucket/data/test.txt",
            byte_size=1024,
            media_type="text/plain",
            checksum="abc123",
            format="txt",
            issued="2023-01-01T00:00:00+00:00",
            modified="2023-01-01T00:00:00+00:00",
        )

    def test_init_basic(self):
        """Test basic initialization."""
        client = S3DataClient(bucket_name="test-bucket")

        assert client.bucket_name == "test-bucket"
        assert client.prefix == ""
        assert client.client_name == "S3"
        assert client.allowed_prefixes == []
        assert "region_name" in client.s3_config

    def test_init_with_full_config(self, s3_config):
        """Test initialization with full configuration."""
        client = S3DataClient(**s3_config)

        assert client.bucket_name == "test-bucket"
        assert client.prefix == "data"
        assert client.s3_config["aws_access_key_id"] == "test_access_key"
        assert client.s3_config["aws_secret_access_key"] == "test_secret_key"
        assert client.s3_config["region_name"] == "us-east-1"
        assert client.s3_config["endpoint_url"] == "http://localhost:9000"

    def test_init_with_allowed_prefixes(self):
        """Test initialization with allowed prefixes."""
        client = S3DataClient(
            bucket_name="test-bucket", allowed_prefixes=["data/", "/allowed/", "public"]
        )

        # Prefixes should be cleaned (no leading/trailing slashes)
        assert client.allowed_prefixes == ["data", "allowed", "public"]

    def test_init_with_prefix_cleaning(self):
        """Test prefix cleaning during initialization."""
        client = S3DataClient(bucket_name="test-bucket", prefix="/data/")
        assert client.prefix == "data"

    def test_resolve_s3_key_basic(self, client):
        """Test basic S3 key resolution."""
        # Test with prefix and resource path
        result = client._resolve_s3_key("folder/file.txt")
        assert result == "data/folder/file.txt"

        # Test with empty resource path
        result = client._resolve_s3_key("")
        assert result == "data"

        # Test with leading slash
        result = client._resolve_s3_key("/folder/file.txt")
        assert result == "data/folder/file.txt"

    def test_resolve_s3_key_no_prefix(self):
        """Test S3 key resolution without prefix."""
        client = S3DataClient(bucket_name="test-bucket")

        result = client._resolve_s3_key("folder/file.txt")
        assert result == "folder/file.txt"

        result = client._resolve_s3_key("")
        assert result == ""

    def test_resolve_s3_key_url_decode(self, client):
        """Test S3 key URL decoding."""
        encoded_path = quote("folder with spaces/file name.txt")
        result = client._resolve_s3_key(encoded_path)
        assert result == "data/folder with spaces/file name.txt"

    def test_resolve_s3_key_with_allowed_prefixes(self):
        """Test S3 key resolution with allowed prefixes."""
        client = S3DataClient(
            bucket_name="test-bucket",
            prefix="data",
            allowed_prefixes=["data/public", "data/shared"],
        )

        # Valid path within allowed prefix
        result = client._resolve_s3_key("public/file.txt")
        assert result == "data/public/file.txt"

        # Invalid path outside allowed prefix
        with pytest.raises(HTTPException) as exc_info:
            client._resolve_s3_key("private/file.txt")

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    def test_resolve_s3_key_empty_allowed_prefix(self):
        """Test S3 key resolution with empty allowed prefix (root access)."""
        client = S3DataClient(
            bucket_name="test-bucket",
            prefix="data",
            allowed_prefixes=["", "public"],  # Empty string means root access
        )

        # Should allow any path due to empty prefix
        result = client._resolve_s3_key("anywhere/file.txt")
        assert result == "data/anywhere/file.txt"

    def test_parse_range_header(self, client):
        """Test HTTP Range header parsing."""
        # Valid range with end
        result = client._parse_range_header("bytes=0-499")
        assert result == (0, 499)

        # Valid range without end
        result = client._parse_range_header("bytes=500-")
        assert result == (500, None)

        # Invalid range format
        result = client._parse_range_header("invalid-range")
        assert result is None

        # Empty range header
        result = client._parse_range_header("")
        assert result is None

    def test_map_s3_error(self, client):
        """Test S3 error mapping to HTTP exceptions."""
        # Test NoSuchKey error
        error = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "get_object"
        )
        http_exc = client._map_s3_error(error)
        assert http_exc.status_code == 404

        # Test NoSuchBucket error
        error = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
            "get_object",
        )
        http_exc = client._map_s3_error(error)
        assert http_exc.status_code == 404

        # Test AccessDenied error
        error = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "get_object",
        )
        http_exc = client._map_s3_error(error)
        assert http_exc.status_code == 403

        # Test InvalidRange error
        error = ClientError(
            {"Error": {"Code": "InvalidRange", "Message": "Range not satisfiable"}},
            "get_object",
        )
        http_exc = client._map_s3_error(error)
        assert http_exc.status_code == 416

        # Test generic error
        error = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Server error"}},
            "get_object",
        )
        http_exc = client._map_s3_error(error)
        assert http_exc.status_code == 500

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_stream_content_success(
        self, mock_session_class, client, mock_s3_client, sample_s3_object
    ):
        """Test successful content streaming."""
        # Setup session mock
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        # Mock S3 responses
        mock_s3_client.head_object.return_value = sample_s3_object

        # Mock stream response - use regular Mock, not AsyncMock
        mock_body = MagicMock()

        # Create async iterator class that implements __aiter__ properly
        class MockAsyncIterator:
            def __init__(self, chunks):
                self.chunks = chunks
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.chunks):
                    raise StopAsyncIteration
                chunk = self.chunks[self.index]
                self.index += 1
                return chunk

        mock_body.iter_chunks.return_value = MockAsyncIterator(
            [b"chunk1", b"chunk2", b"chunk3"]
        )
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Execute
        chunks = []
        async for chunk in client.stream_content("test.txt"):
            chunks.append(chunk)

        # Verify
        assert chunks == [b"chunk1", b"chunk2", b"chunk3"]
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket", Key="data/test.txt"
        )
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="data/test.txt"
        )

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_stream_content_with_range(
        self, mock_session_class, client, mock_s3_client, sample_s3_object
    ):
        """Test content streaming with range header."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client
        mock_s3_client.head_object.return_value = sample_s3_object

        mock_body = MagicMock()  # Use MagicMock instead of AsyncMock

        # Create async iterator class
        class MockAsyncIterator:
            def __init__(self, chunks):
                self.chunks = chunks
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.chunks):
                    raise StopAsyncIteration
                chunk = self.chunks[self.index]
                self.index += 1
                return chunk

        mock_body.iter_chunks.return_value = MockAsyncIterator([b"partial"])
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Execute
        chunks = []
        async for chunk in client.stream_content("test.txt", "bytes=0-99"):
            chunks.append(chunk)

        # Verify range parameter was set
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="data/test.txt", Range="bytes=0-99"
        )

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_stream_content_file_too_large(
        self, mock_session_class, client, mock_s3_client
    ):
        """Test streaming with file too large."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        # Mock large file
        large_file_object = {"ContentLength": 999999999999}  # Larger than MAX_FILE_SIZE
        mock_s3_client.head_object.return_value = large_file_object

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            async for _ in client.stream_content("large.txt"):
                pass

        assert exc_info.value.status_code == 413
        assert "File too large" in exc_info.value.detail

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_stream_content_s3_error(
        self, mock_session_class, client, mock_s3_client
    ):
        """Test streaming with S3 error."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        # Mock S3 error
        s3_error = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "head_object"
        )
        mock_s3_client.head_object.side_effect = s3_error

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            async for _ in client.stream_content("missing.txt"):
                pass

        assert exc_info.value.status_code == 404

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_stream_content_no_credentials(self, mock_session_class, client):
        """Test streaming with missing credentials."""
        # Setup
        mock_session_class.side_effect = NoCredentialsError()

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            async for _ in client.stream_content("test.txt"):
                pass

        assert exc_info.value.status_code == 500
        assert "S3 credentials not configured" in exc_info.value.detail

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_read_file_content_success(
        self, mock_session_class, client, mock_s3_client, sample_s3_object
    ):
        """Test successful file content reading."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        mock_s3_client.head_object.return_value = sample_s3_object

        mock_body = AsyncMock()
        mock_body.read.return_value = b"file content"
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Execute
        result = await client.read_file_content("test.txt")

        # Verify
        assert result == b"file content"
        mock_s3_client.head_object.assert_called_once()
        mock_s3_client.get_object.assert_called_once()

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_get_distribution_metadata_success(
        self, mock_session_class, client, mock_s3_client, sample_s3_object
    ):
        """Test successful metadata retrieval."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        # Add datetime object for LastModified
        from datetime import datetime, timezone

        sample_s3_object["LastModified"] = datetime(2023, 1, 1, tzinfo=timezone.utc)
        mock_s3_client.head_object.return_value = sample_s3_object

        # Execute
        result = await client.get_distribution_metadata("test.txt")

        # Verify
        assert isinstance(result, DataProductDistribution)
        assert result.title == "test.txt"
        assert result.byte_size == 1024
        assert result.media_type == "text/plain"
        assert result.checksum == "abc123"
        assert result.format == "txt"
        assert result.issued is not None and "2023-01-01" in result.issued
        assert "s3://test-bucket/data/test.txt" == result.access_url

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_list_dataproduct_distributions_success(
        self, mock_session_class, client, mock_s3_client
    ):
        """Test successful distribution listing."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        # Create mock paginator that behaves correctly
        mock_paginator = MagicMock()
        mock_s3_client.get_paginator.return_value = mock_paginator

        # Mock page iterator with sample objects
        from datetime import datetime, timezone

        mock_page = {
            "Contents": [
                {
                    "Key": "data/folder/file1.txt",
                    "Size": 100,
                    "LastModified": datetime(2023, 1, 1, tzinfo=timezone.utc),
                    "ETag": '"hash1"',
                },
                {
                    "Key": "data/folder/file2.csv",
                    "Size": 200,
                    "LastModified": datetime(2023, 1, 2, tzinfo=timezone.utc),
                    "ETag": '"hash2"',
                },
            ]
        }

        # Create proper async iterator for paginate
        class MockPageIterator:
            def __init__(self, pages):
                self.pages = pages
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.pages):
                    raise StopAsyncIteration
                page = self.pages[self.index]
                self.index += 1
                return page

        mock_paginator.paginate.return_value = MockPageIterator([mock_page])

        # Execute
        result = await client.list_dataproduct_distributions("folder")

        # Verify
        assert len(result) == 2
        assert result[0].title == "file1.txt"
        assert result[0].byte_size == 100
        assert result[1].title == "file2.csv"
        assert result[1].byte_size == 200

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_list_dataproducts_success(
        self, mock_session_class, client, mock_s3_client
    ):
        """Test successful dataproducts listing."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        # Mock list_objects_v2 response with common prefixes
        mock_response = {
            "CommonPrefixes": [
                {"Prefix": "data/dataset1/"},
                {"Prefix": "data/dataset2/"},
                {"Prefix": "data/experiments/"},
            ]
        }
        mock_s3_client.list_objects_v2.return_value = mock_response

        # Execute
        result = await client.list_dataproducts()

        # Verify
        assert result == ["dataset1", "dataset2", "experiments"]
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket", Prefix="data/", Delimiter="/"
        )

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_health_check_success(
        self, mock_session_class, client, mock_s3_client
    ):
        """Test successful health check."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        # Mock successful responses
        mock_s3_client.head_bucket.return_value = {}
        mock_s3_client.list_objects_v2.return_value = {}

        # Execute
        result = await client.health_check()

        # Verify
        assert result["client_type"] == "S3"
        assert result["status"] == "healthy"
        assert result["bucket_name"] == "test-bucket"
        assert result["prefix"] == "data"
        assert result["bucket_accessible"] is True
        assert result["prefix_accessible"] is True

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_health_check_bucket_inaccessible(
        self, mock_session_class, client, mock_s3_client
    ):
        """Test health check with inaccessible bucket."""
        # Setup
        mock_session_class.return_value = mock_session_class
        mock_session_class.client.return_value.__aenter__.return_value = mock_s3_client

        # Mock bucket access error
        s3_error = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Not found"}}, "head_bucket"
        )
        mock_s3_client.head_bucket.side_effect = s3_error

        # Execute
        result = await client.health_check()

        # Verify
        assert result["status"] == "unhealthy"
        assert result["bucket_accessible"] is False

    @patch("app.core.clients.read.s3_read_client.aioboto3.Session")
    @pytest.mark.asyncio
    async def test_health_check_no_credentials(self, mock_session_class, client):
        """Test health check with no credentials."""
        # Setup
        mock_session_class.side_effect = NoCredentialsError()

        # Execute
        result = await client.health_check()

        # Verify
        assert result["status"] == "unhealthy"
        assert result["client_type"] == "S3"
        assert "S3 credentials not configured" in result["error"]
