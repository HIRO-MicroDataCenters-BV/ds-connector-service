from typing import Any, AsyncGenerator, Dict, List, Optional

from abc import ABC

from app.core.clients.base import BaseReadDataClient, BaseWriteDataClient

from ..rest_api.serializers import DataProductDistribution


class IReadUseCases(ABC):
    """Abstract base class for read use cases"""

    client: BaseReadDataClient

    def __init__(self, client: BaseReadDataClient):
        self.client = client


class IWriteUseCases(ABC):
    """Abstract base class for write use cases"""

    client: BaseWriteDataClient

    def __init__(self, client: BaseWriteDataClient):
        self.client = client


class DataProductReadUseCase(IReadUseCases):
    def __init__(self, client):
        super().__init__(client)

    async def get_distribution_metadata(
        self, resource_path: str
    ) -> DataProductDistribution:
        return await self.client.get_distribution_metadata(resource_path)

    async def list_dataproduct_distributions(
        self, directory_resource_path: str
    ) -> List[DataProductDistribution]:
        return await self.client.list_dataproduct_distributions(directory_resource_path)

    async def health_check(self) -> Dict[str, Any]:
        return await self.client.health_check()

    async def read_dataproduct_distribution_content(self, resource_path: str) -> bytes:
        return await self.client.read_file_content(resource_path)

    async def stream_dataproduct_distribution_content(
        self,
        resource_path: str,
        range_header: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        async for chunk in self.client.stream_content(resource_path, range_header):
            yield chunk

    async def list_dataproducts(self) -> List[str]:
        """List available data products (subdirectories from base path)."""
        return await self.client.list_dataproducts()


class DataProductWriteUseCase(IWriteUseCases):
    """Use case for data product write operations"""

    def __init__(self, client: BaseWriteDataClient):
        super().__init__(client)

    async def upload_data_product(
        self,
        resource_path: str,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Upload a complete data product file at once

        Args:
            resource_path: Path where to store the data product
            content: Complete file content as bytes
            metadata: Optional metadata (content_type, tags, etc.)

        Returns:
            Dict containing upload result information
        """
        return await self.client.write_file_content(resource_path, content, metadata)

    async def stream_upload_data_product(
        self,
        resource_path: str,
        content_stream: AsyncGenerator[bytes, None],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Upload a data product file using streaming (memory-efficient)

        Args:
            resource_path: Path where to store the data product
            content_stream: Async generator yielding content chunks
            metadata: Optional metadata

        Returns:
            Dict containing upload result information
        """
        return await self.client.write_stream(resource_path, content_stream, metadata)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check write client health and connectivity

        Returns:
            Dict containing health status information
        """
        return await self.client.health_check()
