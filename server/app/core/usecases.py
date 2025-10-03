from typing import Any, Dict, List

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

    async def get_dataproduct_metadata(
        self, resource_path: str, resource_name: str
    ) -> DataProductDistribution:
        return await self.client.get_metadata(resource_path, resource_name)

    async def list_dataproducts(
        self, resource_path: str
    ) -> List[DataProductDistribution]:
        return await self.client.list_data_products(resource_path)

    async def health_check(self) -> Dict[str, Any]:
        return await self.client.health_check()

    async def read_dataproduct_distribution_content(
        self, resource_path: str, resource_name: str
    ) -> bytes:
        return await self.client.read_file_content(resource_path, resource_name)
