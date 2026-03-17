"""Unit tests for LocalFileSystemWriteClient."""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.core.clients.write.local_file_system_write import LocalFileSystemWriteClient


class TestLocalFileSystemWriteClient:
    """Test cases for LocalFileSystemWriteClient class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def write_client(self, temp_dir):
        """Create LocalFileSystemWriteClient instance for testing."""
        # Mock FS_BASE_PATH to use our temp directory
        with patch(
            "app.core.clients.write.local_file_system_write.FS_BASE_PATH", str(temp_dir)
        ):
            return LocalFileSystemWriteClient(
                base_path=str(temp_dir), allowed_paths=[]  # No restrictions for testing
            )

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return b"Hello, World! This is test content for file writing."

    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return {
            "content_type": "text/plain",
            "tags": {"source": "test", "type": "sample"},
            "meta_original_filename": "test.txt",
            "meta_upload_source": "unit_test",
        }

    @pytest.mark.asyncio
    async def test_write_file_content_success(
        self, write_client, temp_dir, sample_content, sample_metadata
    ):
        """Test successful file write."""
        resource_path = "test_files/sample.txt"

        result = await write_client.write_file_content(
            resource_path=resource_path,
            content=sample_content,
            metadata=sample_metadata,
        )

        # Verify the file was created
        expected_path = temp_dir / resource_path
        assert expected_path.exists()

        # Verify content
        assert expected_path.read_bytes() == sample_content

        # Verify return result
        assert result["path"] == str(expected_path)
        assert result["size"] == len(sample_content)
        assert result["client"] == "FileSystemWrite"
        assert "checksum" in result
        assert "timestamp" in result

        # Verify checksum
        expected_checksum = hashlib.md5(sample_content).hexdigest()
        assert result["checksum"] == expected_checksum

    @pytest.mark.asyncio
    async def test_write_file_content_creates_directories(
        self, write_client, temp_dir, sample_content
    ):
        """Test that write_file_content creates necessary directories."""
        resource_path = "deep/nested/path/test.txt"

        await write_client.write_file_content(
            resource_path=resource_path, content=sample_content
        )

        # Verify directory structure was created
        expected_path = temp_dir / resource_path
        assert expected_path.exists()
        assert expected_path.parent.exists()
        assert expected_path.read_bytes() == sample_content

    @pytest.mark.asyncio
    async def test_write_file_content_invalid_path(self, write_client, sample_content):
        """Test write with invalid/restricted path."""
        resource_path = "../../../etc/passwd"  # Path traversal attempt

        with pytest.raises(HTTPException) as exc_info:
            await write_client.write_file_content(
                resource_path=resource_path, content=sample_content
            )

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_write_file_content_file_size_limit(self, temp_dir):
        """Test file size limit enforcement."""
        # Create client and patch MAX_FILE_SIZE
        with patch(
            "app.core.clients.write.local_file_system_write.FS_BASE_PATH", str(temp_dir)
        ):
            write_client = LocalFileSystemWriteClient(
                base_path=str(temp_dir), allowed_paths=[]
            )

            # Patch MAX_FILE_SIZE to a small value
            with patch(
                "app.core.clients.write.local_file_system_write.MAX_FILE_SIZE", 100
            ):
                large_content = b"x" * 200  # 200 bytes - exceeds limit

                with pytest.raises(HTTPException) as exc_info:
                    await write_client.write_file_content(
                        resource_path="large_file.txt", content=large_content
                    )

                assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_write_file_content_existing_file_overwrite(
        self, write_client, temp_dir, sample_content
    ):
        """Test overwriting existing file."""
        resource_path = "existing_file.txt"
        initial_content = b"Initial content"

        # Create initial file
        expected_path = temp_dir / resource_path
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        expected_path.write_bytes(initial_content)

        # Overwrite with new content
        result = await write_client.write_file_content(
            resource_path=resource_path, content=sample_content
        )

        # Verify file was overwritten
        assert expected_path.read_bytes() == sample_content
        assert result["size"] == len(sample_content)

    @pytest.mark.asyncio
    async def test_write_stream_success(self, write_client, temp_dir, sample_metadata):
        """Test successful stream write."""
        resource_path = "stream_files/sample_stream.txt"

        # Create async generator for content chunks
        async def content_stream():
            chunks = [b"Hello, ", b"World! ", b"This is ", b"streaming content."]
            for chunk in chunks:
                yield chunk

        result = await write_client.write_stream(
            resource_path=resource_path,
            content_stream=content_stream(),
            metadata=sample_metadata,
        )

        # Verify the file was created
        expected_path = temp_dir / resource_path
        assert expected_path.exists()

        # Verify content
        expected_content = b"Hello, World! This is streaming content."
        assert expected_path.read_bytes() == expected_content

        # Verify return result
        assert result["path"] == str(expected_path)
        assert result["size"] == len(expected_content)
        assert result["client"] == "FileSystemWrite"
        assert "checksum" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_write_stream_empty_stream(self, write_client, temp_dir):
        """Test write_stream with empty stream creates empty file."""

        async def empty_stream():
            return
            yield  # Never reached

        result = await write_client.write_stream(
            resource_path="empty.txt", content_stream=empty_stream()
        )

        # Should create empty file
        assert result["size"] == 0
        assert result["client"] == "FileSystemWrite"

        # Verify empty file exists
        empty_file = temp_dir / "empty.txt"
        assert empty_file.exists()
        assert empty_file.stat().st_size == 0

    @pytest.mark.asyncio
    async def test_write_stream_size_limit_exceeded(self, temp_dir):
        """Test stream write with size limit exceeded."""
        with patch(
            "app.core.clients.write.local_file_system_write.FS_BASE_PATH", str(temp_dir)
        ):
            write_client = LocalFileSystemWriteClient(
                base_path=str(temp_dir), allowed_paths=[]
            )

            # Patch MAX_FILE_SIZE to a small value
            with patch(
                "app.core.clients.write.local_file_system_write.MAX_FILE_SIZE", 50
            ):

                async def large_stream():
                    # Generate chunks that exceed limit
                    for i in range(10):
                        yield b"x" * 10  # 10 bytes each, total 100 bytes

                with pytest.raises(HTTPException) as exc_info:
                    await write_client.write_stream(
                        resource_path="large_stream.txt", content_stream=large_stream()
                    )

                assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_health_check_success(self, write_client, temp_dir):
        """Test successful health check."""
        result = await write_client.health_check()

        assert result["status"] == "healthy"
        assert result["client"] == "FileSystemWrite"
        assert result["base_path"] == str(temp_dir)
        assert result["writable"] is True
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_health_check_directory_not_writable(self, temp_dir):
        """Test health check with non-writable directory."""
        # Create client with non-existent/non-writable directory and expect
        # initialization to fail
        non_writable_path = temp_dir / "non_existent_dir"

        with patch("pathlib.Path.exists") as mock_exists, patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_exists.return_value = (
                False  # Make exists() return False to trigger mkdir
            )
            mock_mkdir.side_effect = PermissionError("Permission denied")

            # Expect HTTPException during client initialization
            with pytest.raises(HTTPException) as exc_info:
                LocalFileSystemWriteClient(
                    base_path=str(non_writable_path),
                    allowed_paths=[str(non_writable_path)],
                )

            assert exc_info.value.status_code == 500
            assert "Failed to initialize write client" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_path_validation_allowed_paths(self, temp_dir):
        """Test path validation with allowed_paths restrictions."""
        # Create client with specific allowed paths
        allowed_subdir = temp_dir / "allowed"
        allowed_subdir.mkdir()

        with patch(
            "app.core.clients.write.local_file_system_write.FS_BASE_PATH", str(temp_dir)
        ):
            write_client = LocalFileSystemWriteClient(
                base_path=str(temp_dir), allowed_paths=[str(allowed_subdir)]
            )

        # Test allowed path
        result = await write_client.write_file_content(
            resource_path="allowed/test.txt", content=b"test content"
        )
        assert "path" in result

        # Test disallowed path
        with pytest.raises(HTTPException) as exc_info:
            await write_client.write_file_content(
                resource_path="not_allowed/test.txt", content=b"test content"
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_atomic_write_operation(self, write_client, temp_dir):
        """Test that write operations are atomic."""
        resource_path = "atomic_test.txt"
        content = b"Atomic test content"

        # Mock an exception during the final rename to test cleanup
        with patch("pathlib.Path.rename") as mock_rename:
            mock_rename.side_effect = OSError("Simulated failure")

            with pytest.raises(HTTPException):
                await write_client.write_file_content(
                    resource_path=resource_path, content=content
                )

            # Verify target file was not created (atomic operation failed cleanly)
            expected_path = temp_dir / resource_path
            assert not expected_path.exists()

            # Verify no temp files are left behind
            temp_files = list(temp_dir.glob("*.tmp"))
            assert len(temp_files) == 0

    def test_client_initialization(self, temp_dir):
        """Test client initialization with various parameters."""
        # Test with minimal parameters (FS_BASE_PATH takes precedence)
        with patch(
            "app.core.clients.write.local_file_system_write.FS_BASE_PATH", str(temp_dir)
        ):
            client = LocalFileSystemWriteClient(base_path=str(temp_dir))
            assert client.base_path == Path(temp_dir)
            assert client.client_name == "FileSystemWrite"
            assert client.allowed_paths == []

        # Test with allowed_paths
        allowed_paths = [str(temp_dir / "allowed1"), str(temp_dir / "allowed2")]
        with patch(
            "app.core.clients.write.local_file_system_write.FS_BASE_PATH", str(temp_dir)
        ):
            client = LocalFileSystemWriteClient(
                base_path=str(temp_dir), allowed_paths=allowed_paths
            )
            assert len(client.allowed_paths) == 2
            assert all(isinstance(p, str) for p in client.allowed_paths)

    @pytest.mark.asyncio
    async def test_metadata_handling(self, write_client, temp_dir, sample_content):
        """Test that metadata is properly handled (stored in result)."""
        resource_path = "metadata_test.txt"
        metadata = {
            "content_type": "application/octet-stream",
            "tags": {"key1": "value1", "key2": "value2"},
            "meta_custom_field": "custom_value",
        }

        result = await write_client.write_file_content(
            resource_path=resource_path, content=sample_content, metadata=metadata
        )

        # Metadata should be included in result for potential use by caller
        # (filesystem doesn't store metadata in file attributes, but returns it)
        assert "timestamp" in result
        assert result["client"] == "FileSystemWrite"
