"""Unit tests for DataProductReadUseCase."""

from unittest.mock import AsyncMock

import pytest

from app.core.usecases import DataProductReadUseCase
from app.rest_api.serializers import DataProductDistribution


class TestDataProductReadUseCase:
    """Test cases for DataProductReadUseCase class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for testing."""
        client = AsyncMock()
        client.get_distribution_metadata = AsyncMock()
        client.list_dataproduct_distributions = AsyncMock()
        client.health_check = AsyncMock()
        client.read_file_content = AsyncMock()
        client.stream_content = AsyncMock()
        client.list_dataproducts = AsyncMock()
        return client

    @pytest.fixture
    def usecase(self, mock_client):
        """Create a DataProductReadUseCase instance for testing."""
        return DataProductReadUseCase(mock_client)

    @pytest.fixture
    def sample_distribution(self):
        """Create a sample DataProductDistribution for testing."""
        return DataProductDistribution(
            title="test.txt",
            description="Test file",
            access_url="/data/test.txt",
            byte_size=1024,
            media_type="text/plain",
            checksum="abc123",
            format="txt",
            issued="2023-01-01T00:00:00",
            modified="2023-01-02T00:00:00",
        )

    @pytest.mark.asyncio
    async def test_get_distribution_metadata_success(
        self, usecase, mock_client, sample_distribution
    ):
        """Test getting distribution metadata successfully."""
        # Setup mock
        mock_client.get_distribution_metadata.return_value = sample_distribution

        # Execute
        result = await usecase.get_distribution_metadata("test/file.txt")

        # Verify
        mock_client.get_distribution_metadata.assert_called_once_with("test/file.txt")
        assert result == sample_distribution

    @pytest.mark.asyncio
    async def test_list_dataproduct_distributions_success(
        self, usecase, mock_client, sample_distribution
    ):
        """Test listing dataproduct distributions successfully."""
        # Setup mock
        distributions = [sample_distribution]
        mock_client.list_dataproduct_distributions.return_value = distributions

        # Execute
        result = await usecase.list_dataproduct_distributions("test/directory")

        # Verify
        mock_client.list_dataproduct_distributions.assert_called_once_with(
            "test/directory"
        )
        assert result == distributions

    @pytest.mark.asyncio
    async def test_health_check_success(self, usecase, mock_client):
        """Test health check successfully."""
        # Setup mock
        health_data = {
            "client_type": "FileSystem",
            "status": "healthy",
            "base_path": "/data",
            "exists": True,
            "is_directory": True,
            "can_write": True,
        }
        mock_client.health_check.return_value = health_data

        # Execute
        result = await usecase.health_check()

        # Verify
        mock_client.health_check.assert_called_once()
        assert result == health_data

    @pytest.mark.asyncio
    async def test_read_dataproduct_distribution_content_success(
        self, usecase, mock_client
    ):
        """Test reading dataproduct distribution content successfully."""
        # Setup mock
        content = b"File content here"
        mock_client.read_file_content.return_value = content

        # Execute
        result = await usecase.read_dataproduct_distribution_content("test/file.txt")

        # Verify
        mock_client.read_file_content.assert_called_once_with("test/file.txt")
        assert result == content

    @pytest.mark.asyncio
    async def test_stream_dataproduct_distribution_content_success(
        self, usecase, mock_client
    ):
        """Test streaming dataproduct distribution content successfully."""

        # Setup mock - async generator
        async def mock_stream_generator(resource_path, range_header=None):
            yield b"chunk1"
            yield b"chunk2"
            yield b"chunk3"

        # Mock the stream_content to return the async generator
        mock_client.stream_content = mock_stream_generator

        # Execute
        chunks = []
        async for chunk in usecase.stream_dataproduct_distribution_content(
            "test/file.txt"
        ):
            chunks.append(chunk)

        # Verify
        assert chunks == [b"chunk1", b"chunk2", b"chunk3"]

    @pytest.mark.asyncio
    async def test_stream_dataproduct_distribution_content_with_range(
        self, usecase, mock_client
    ):
        """Test streaming dataproduct distribution content with range header."""

        # Setup mock - async generator
        async def mock_stream_generator(resource_path, range_header):
            yield b"partial_chunk"

        # Mock the stream_content method
        mock_client.stream_content = mock_stream_generator

        # Execute
        chunks = []
        range_header = "bytes=0-1023"
        async for chunk in usecase.stream_dataproduct_distribution_content(
            "test/file.txt", range_header
        ):
            chunks.append(chunk)

        # Verify
        assert chunks == [b"partial_chunk"]

    @pytest.mark.asyncio
    async def test_list_dataproducts_success(self, usecase, mock_client):
        """Test listing dataproducts successfully."""
        # Setup mock
        products = ["product1", "product2", "product3"]
        mock_client.list_dataproducts.return_value = products

        # Execute
        result = await usecase.list_dataproducts()

        # Verify
        mock_client.list_dataproducts.assert_called_once()
        assert result == products

    @pytest.mark.asyncio
    async def test_client_dependency_injection(self, mock_client):
        """Test that the client is properly injected."""
        usecase = DataProductReadUseCase(mock_client)
        assert usecase.client == mock_client

    @pytest.mark.asyncio
    async def test_multiple_operations_sequence(
        self, usecase, mock_client, sample_distribution
    ):
        """Test a sequence of operations to ensure state is maintained."""
        # Setup mocks
        mock_client.list_dataproducts.return_value = ["product1"]
        mock_client.list_dataproduct_distributions.return_value = [sample_distribution]
        mock_client.get_distribution_metadata.return_value = sample_distribution
        mock_client.read_file_content.return_value = b"content"

        # Execute sequence
        products = await usecase.list_dataproducts()
        distributions = await usecase.list_dataproduct_distributions("product1")
        metadata = await usecase.get_distribution_metadata("product1/file.txt")
        content = await usecase.read_dataproduct_distribution_content(
            "product1/file.txt"
        )

        # Verify all operations were called
        assert products == ["product1"]
        assert distributions == [sample_distribution]
        assert metadata == sample_distribution
        assert content == b"content"

        # Verify all mock calls
        mock_client.list_dataproducts.assert_called_once()
        mock_client.list_dataproduct_distributions.assert_called_once_with("product1")
        mock_client.get_distribution_metadata.assert_called_once_with(
            "product1/file.txt"
        )
        mock_client.read_file_content.assert_called_once_with("product1/file.txt")

    @pytest.mark.asyncio
    async def test_error_propagation(self, usecase, mock_client):
        """Test that errors from the client are properly propagated."""
        # Setup mock to raise exception
        mock_client.get_distribution_metadata.side_effect = Exception("Client error")

        # Execute and verify exception is propagated
        with pytest.raises(Exception, match="Client error"):
            await usecase.get_distribution_metadata("test/file.txt")

    @pytest.mark.asyncio
    async def test_empty_stream_handling(self, usecase, mock_client):
        """Test handling of empty stream from client."""

        # Setup mock - empty async generator
        async def empty_stream_generator(resource_path, range_header=None):
            return
            yield  # pragma: no cover

        # Mock the stream_content method
        mock_client.stream_content = empty_stream_generator

        # Execute
        chunks = []
        async for chunk in usecase.stream_dataproduct_distribution_content(
            "test/empty.txt"
        ):
            chunks.append(chunk)

        # Verify
        assert chunks == []

    def test_usecase_inheritance(self, usecase):
        """Test that DataProductReadUseCase inherits from IReadUseCases correctly."""
        from app.core.usecases import IReadUseCases

        assert isinstance(usecase, IReadUseCases)
        assert hasattr(usecase, "client")

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self, usecase, mock_client, sample_distribution
    ):
        """Test concurrent operations on the usecase."""
        import asyncio

        # Setup mocks
        mock_client.get_distribution_metadata.return_value = sample_distribution
        mock_client.list_dataproducts.return_value = ["product1", "product2"]

        # Execute concurrent operations
        results = await asyncio.gather(
            usecase.get_distribution_metadata("file1.txt"),
            usecase.get_distribution_metadata("file2.txt"),
            usecase.list_dataproducts(),
            return_exceptions=True,
        )

        # Verify results
        assert len(results) == 3
        assert results[0] == sample_distribution
        assert results[1] == sample_distribution
        assert results[2] == ["product1", "product2"]

        # Verify mock calls
        assert mock_client.get_distribution_metadata.call_count == 2
        mock_client.list_dataproducts.assert_called_once()
