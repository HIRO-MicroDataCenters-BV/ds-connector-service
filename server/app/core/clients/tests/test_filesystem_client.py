"""Unit tests for FileSystemDataClient."""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.clients.read.local_file_system_read import FileSystemDataClient
from app.rest_api.serializers import DataProductDistribution


class TestFileSystemDataClient:
    """Test cases for FileSystemDataClient class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample files for testing."""
        # Create directory structure
        (temp_dir / "folder1").mkdir()
        (temp_dir / "folder1" / "subfolder").mkdir()
        (temp_dir / "folder2").mkdir()

        # Create sample files
        files = {
            "test.txt": "Hello, World!",
            "data.csv": "name,age,city\nJohn,30,NYC\nJane,25,LA",
            "folder1/nested.json": '{"key": "value", "number": 42}',
            "folder1/subfolder/deep.xml": (
                '<?xml version="1.0"?>' "<root>" "<item>test</item>" "</root>"
            ),
            "folder2/binary.bin": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR",
        }

        created_files = {}
        for file_path, content in files.items():
            full_path = temp_dir / file_path
            if isinstance(content, str):
                full_path.write_text(content)
            else:
                full_path.write_bytes(content)
            created_files[file_path] = full_path

        return created_files

    @pytest.fixture
    def client(self, temp_dir):
        """Create a FileSystemDataClient instance for testing."""
        return FileSystemDataClient(base_path=str(temp_dir))

    def test_init_with_existing_path(self, temp_dir):
        """Test initialization with existing base path."""
        client = FileSystemDataClient(base_path=str(temp_dir))
        assert client.base_path == temp_dir.resolve()
        assert client.client_name == "FileSystem"
        assert client.allowed_paths == [temp_dir.resolve()]

    def test_init_with_nonexistent_path(self):
        """Test initialization with non-existent base path."""
        with pytest.raises(FileNotFoundError):
            FileSystemDataClient(base_path="/nonexistent/path")

    def test_init_with_allowed_paths(self, temp_dir):
        """Test initialization with allowed paths."""
        allowed_path = temp_dir / "allowed"
        allowed_path.mkdir()

        client = FileSystemDataClient(
            base_path=str(temp_dir), allowed_paths=[str(allowed_path)]
        )
        assert len(client.allowed_paths) == 1
        assert client.allowed_paths[0] == allowed_path.resolve()

    def test_resolve_file_path_valid(self, client, temp_dir):
        """Test path resolution with valid paths."""
        # Test normal file path
        result = client._resolve_file_path("test.txt")
        expected = temp_dir / "test.txt"
        assert result == expected.resolve()

        # Test nested file path
        result = client._resolve_file_path("folder1/nested.json")
        expected = temp_dir / "folder1" / "nested.json"
        assert result == expected.resolve()

        # Test empty path
        result = client._resolve_file_path("")
        assert result == temp_dir.resolve()

    def test_resolve_file_path_with_leading_slash(self, client, temp_dir):
        """Test path resolution with leading slash."""
        result = client._resolve_file_path("/test.txt")
        expected = temp_dir / "test.txt"
        assert result == expected.resolve()

    def test_resolve_file_path_outside_allowed(self, temp_dir):
        """Test path resolution outside allowed paths."""
        # Create client with restricted allowed paths
        allowed_dir = temp_dir / "allowed"
        allowed_dir.mkdir()

        client = FileSystemDataClient(
            base_path=str(temp_dir), allowed_paths=[str(allowed_dir)]
        )

        # Try to access file outside allowed path
        with pytest.raises(HTTPException) as exc_info:
            client._resolve_file_path("../outside.txt")

        assert exc_info.value.status_code == 403

    @patch("aiofiles.ospath.exists")
    @patch("aiofiles.ospath.isfile")
    @patch("aiofiles.open")
    @patch("os.stat")
    @pytest.mark.asyncio
    async def test_stream_content_full_file(
        self, mock_stat, mock_open, mock_isfile, mock_exists, client
    ):
        """Test streaming entire file content."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_stat.return_value = MagicMock(st_size=1000)

        # Mock file content
        file_content = b"Hello, World! This is test content."
        mock_file = AsyncMock()
        mock_file.read.side_effect = [
            file_content[:10],
            file_content[10:20],
            file_content[20:],
            b"",
        ]
        mock_open.return_value.__aenter__.return_value = mock_file

        # Test streaming
        chunks = []
        async for chunk in client.stream_content("test.txt"):
            chunks.append(chunk)

        # Verify result
        assert len(chunks) == 3
        assert b"".join(chunks) == file_content

    @patch("aiofiles.ospath.exists")
    @patch("aiofiles.ospath.isfile")
    @patch("aiofiles.open")
    @patch("os.stat")
    @pytest.mark.asyncio
    async def test_stream_content_with_range(
        self, mock_stat, mock_open, mock_isfile, mock_exists, client
    ):
        """Test streaming file content with range header."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_stat.return_value = MagicMock(st_size=100)

        # Mock file content
        file_content = b"0123456789" * 10  # 100 bytes
        mock_file = AsyncMock()
        mock_file.read.side_effect = [file_content[10:20], b""]
        mock_file.seek = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file

        # Test streaming with range
        chunks = []
        async for chunk in client.stream_content("test.txt", "bytes=10-19"):
            chunks.append(chunk)

        # Verify seek was called with correct position
        mock_file.seek.assert_called_once_with(10)
        assert len(chunks) == 1
        assert chunks[0] == file_content[10:20]

    @patch("aiofiles.ospath.exists")
    @pytest.mark.asyncio
    async def test_stream_content_file_not_found(self, mock_exists, client):
        """Test streaming non-existent file."""
        mock_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            async for _ in client.stream_content("nonexistent.txt"):
                pass

        assert exc_info.value.status_code == 404

    @patch("aiofiles.ospath.exists")
    @patch("aiofiles.ospath.isfile")
    @patch("os.stat")
    @pytest.mark.asyncio
    async def test_stream_content_file_too_large(
        self, mock_stat, mock_isfile, mock_exists, client
    ):
        """Test streaming file that exceeds size limit."""
        mock_exists.return_value = True
        mock_isfile.return_value = True

        # Mock a very large file
        mock_stat.return_value = MagicMock(st_size=1000 * 1024 * 1024)  # 1GB

        with patch(
            "app.core.clients.read.local_file_system_read.MAX_FILE_SIZE",
            100 * 1024 * 1024,
        ):
            with pytest.raises(HTTPException) as exc_info:
                async for _ in client.stream_content("large_file.txt"):
                    pass

            assert exc_info.value.status_code == 413

    @patch("aiofiles.ospath.exists")
    @patch("aiofiles.ospath.isfile")
    @patch("aiofiles.open")
    @patch("os.stat")
    @pytest.mark.asyncio
    async def test_read_file_content_success(
        self, mock_stat, mock_open, mock_isfile, mock_exists, client
    ):
        """Test reading entire file content."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_stat.return_value = MagicMock(st_size=1000)

        file_content = b"Complete file content here"
        mock_file = AsyncMock()
        mock_file.read.return_value = file_content
        mock_open.return_value.__aenter__.return_value = mock_file

        # Test reading
        result = await client.read_file_content("test.txt")

        assert result == file_content

    @patch("aiofiles.ospath.exists")
    @patch("aiofiles.ospath.isfile")
    @patch("os.stat")
    @pytest.mark.asyncio
    async def test_get_distribution_metadata_success(
        self, mock_stat, mock_isfile, mock_exists, client
    ):
        """Test getting file metadata."""
        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True

        # Mock file stats
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_ctime = 1609459200  # 2021-01-01
        mock_stat_result.st_mtime = 1609545600  # 2021-01-02
        mock_stat.return_value = mock_stat_result

        # Mock checksum calculation
        with patch.object(client, "_calculate_file_checksum", return_value="abc123"):
            result = await client.get_distribution_metadata("test.txt")

        # Verify result
        assert isinstance(result, DataProductDistribution)
        assert result.title == "test.txt"
        assert result.byte_size == 1024
        assert result.media_type == "text/plain"
        assert result.checksum == "abc123"
        assert result.format == "txt"

    @patch("aiofiles.ospath.exists")
    @pytest.mark.asyncio
    async def test_get_distribution_metadata_file_not_found(self, mock_exists, client):
        """Test getting metadata for non-existent file."""
        mock_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await client.get_distribution_metadata("nonexistent.txt")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_dataproducts_success(self, client, temp_dir):
        """Test listing data products (subdirectories)."""
        # Create subdirectories
        (temp_dir / "product1").mkdir()
        (temp_dir / "product2").mkdir()
        (temp_dir / "product3").mkdir()
        # Create a file (should be ignored)
        (temp_dir / "not_a_directory.txt").write_text("content")

        result = await client.list_dataproducts()

        # Should only return directories, sorted
        expected = ["product1", "product2", "product3"]
        assert sorted(result) == expected

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client, temp_dir):
        """Test health check when filesystem is accessible."""
        result = await client.health_check()

        assert result["client_type"] == "FileSystem"
        assert result["status"] == "healthy"
        assert result["base_path"] == str(temp_dir)
        assert result["exists"] is True
        assert result["is_directory"] is True
        assert result["can_write"] is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check when filesystem is not accessible."""
        # Create client with non-existent path (but don't let init fail)
        with patch("pathlib.Path.exists", return_value=True):
            client = FileSystemDataClient(base_path="/tmp/test")

        # Now make the path non-existent for health check
        with patch("aiofiles.ospath.exists", return_value=False):
            result = await client.health_check()

        assert result["client_type"] == "FileSystem"
        assert result["status"] == "unhealthy"

    def test_calculate_file_checksum(self, client, temp_dir):
        """Test file checksum calculation."""
        # Create a test file
        test_file = temp_dir / "checksum_test.txt"
        content = "Hello, World!"
        test_file.write_text(content)

        # Calculate expected checksum
        expected_checksum = hashlib.md5(content.encode()).hexdigest()

        # Test checksum calculation
        result = client._calculate_file_checksum(test_file)
        assert result == expected_checksum

    def test_calculate_file_checksum_error(self, client):
        """Test checksum calculation with non-existent file."""
        result = client._calculate_file_checksum(Path("/nonexistent/file.txt"))
        assert result == ""

    def test_parse_range_header_valid(self, client):
        """Test parsing valid range headers."""
        # Test complete range
        result = client._parse_range_header("bytes=0-499")
        assert result == (0, 499)

        # Test open-ended range
        result = client._parse_range_header("bytes=500-")
        assert result == (500, None)

        # Test another range
        result = client._parse_range_header("bytes=1000-1999")
        assert result == (1000, 1999)

    def test_parse_range_header_invalid(self, client):
        """Test parsing invalid range headers."""
        # Test invalid format
        result = client._parse_range_header("invalid-range")
        assert result is None

        # Test empty header
        result = client._parse_range_header("")
        assert result is None

        # Test None header
        result = client._parse_range_header(None)
        assert result is None

    @patch("app.core.clients.read.local_file_system_read.MAX_FILES_TO_LIST", 2)
    @pytest.mark.asyncio
    async def test_collect_files_recursively_limit(self, client, temp_dir):
        """Test file collection with limit."""
        # Create multiple files
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")
        (temp_dir / "file3.txt").write_text("content3")

        files = await client._collect_files_recursively(str(temp_dir), max_files=2)

        # Should return only 2 files due to limit
        assert len(files) == 2
        assert all(isinstance(item, tuple) and len(item) == 2 for item in files)

    @pytest.mark.asyncio
    async def test_list_dataproduct_distributions_success(self, client, sample_files):
        """Test listing data product distributions from directory."""
        result = await client.list_dataproduct_distributions("folder1")

        assert isinstance(result, list)
        assert len(result) > 0

        # Verify each item is a DataProductDistribution
        for item in result:
            assert isinstance(item, DataProductDistribution)
            assert item.title is not None
            assert item.byte_size is not None
            assert item.access_url is not None

    @pytest.mark.asyncio
    async def test_list_dataproduct_distributions_empty_directory(
        self, client, temp_dir
    ):
        """Test listing distributions from empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        result = await client.list_dataproduct_distributions("empty")
        assert isinstance(result, list)
        assert len(result) == 0
