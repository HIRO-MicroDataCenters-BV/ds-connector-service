from typing import Any, AsyncGenerator, Dict, List, Optional

from abc import ABC

from app.core.clients.base import BaseReadDataClient

from ..rest_api.serializers import DataProductDistribution


class Iusecases(ABC):
    client: BaseReadDataClient

    def __init__(self, client: BaseReadDataClient):
        self.client = client


class DataproductUseCase(Iusecases):
    def __init__(self, client):
        super().__init__(client)

    async def get_distribution_metadata(
        self, resource_path: str, resource_name: str
    ) -> DataProductDistribution:
        return await self.client.get_distribution_metadata(resource_path, resource_name)

    async def list_dataproduct_distributions(
        self, resource_path: str
    ) -> List[DataProductDistribution]:
        return await self.client.list_dataproduct_distributions(resource_path)

    async def health_check(self) -> Dict[str, Any]:
        return await self.client.health_check()

    async def read_dataproduct_distribution_content(
        self, resource_path: str, resource_name: str
    ) -> bytes:
        return await self.client.read_file_content(resource_path, resource_name)

    async def stream_dataproduct_distribution_content(
        self,
        resource_path: str,
        resource_name: str,
        range_header: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        async for chunk in self.client.stream_content(
            resource_path, resource_name, range_header
        ):
            yield chunk

    async def list_dataproducts(self) -> List[str]:
        """List available data products (subdirectories from base path)."""
        return await self.client.list_dataproducts()
