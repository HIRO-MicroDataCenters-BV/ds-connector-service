from typing import Any, AsyncGenerator, Dict, List, Optional

from abc import ABC, abstractmethod

from ...rest_api.serializers import DataProductDistribution


# Abstract Base Client
class BaseReadDataClient(ABC):
    """Abstract base class for all data source clients"""

    @abstractmethod
    async def stream_content(
        self,
        resource_path: str,
        resource_name: str,
        range_header: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream resource content with optional range support
        Args:
            resource_path: Path to the resource
            resource_name: Name of the resource
            range_header: HTTP Range header value (e.g., "bytes=0-1023")
        Yields:
            bytes: Chunks of resource data
        Raises:
            HTTPException: On client-specific errors
        """
        raise NotImplementedError("Subclasses must implement stream_content")
        yield  # type: ignore[unreachable]
        # Required to make this an async generator (unreachable)

    @abstractmethod
    async def get_metadata(
        self, resource_path: str, resource_name: str
    ) -> DataProductDistribution:
        """
        Get resource metadata without transferring content

        Args:
            resource_path: Path to the resource
            resource_name: Name of the resource

        Returns:
            ResourceMetadata: Standardized metadata object

        Raises:
            HTTPException: On client-specific errors
        """
        ...

    @abstractmethod
    async def list_data_products(
        self, resource_path: str
    ) -> List[DataProductDistribution]:
        """
        List available data products

        Args:
            resource_path: Path to the resource
        Returns:
            List[DataProduct]: List of available data products

        Raises:
            HTTPException: On client-specific errors
        """
        ...

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check client health and connectivity

        Returns:
            Dict containing health status information
        """
        ...

    @abstractmethod
    async def read_file_content(
        self,
        resource_path: str,
        resource_name: str,
    ) -> bytes:
        """
        Read the entire file content at once into memory

        Args:
            resource_path: Path to the resource
            resource_name: Name of the resource file

        Returns:
            bytes: Full content of the file

        Raises:
            HTTPException: On client-specific errors
        """
        ...
