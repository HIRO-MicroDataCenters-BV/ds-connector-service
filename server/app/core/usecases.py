from abc import ABC
from ..rest_api.serializers import DataProductDistribution
from typing import List

class Iusecases(ABC):
    def __init__(self, client):
        self.client = client

class DataproductUseCase(Iusecases):
    def __init__(self, client):
        super().__init__(client)

    async def get_dataproduct_metadata(self, resource_path: str, resource_name: str) -> DataProductDistribution:
        return await self.client.get_metadata(resource_path, resource_name)

    async def list_dataproducts(self, resource_path: str) -> List[DataProductDistribution]:
        return await self.client.list_data_products(resource_path)