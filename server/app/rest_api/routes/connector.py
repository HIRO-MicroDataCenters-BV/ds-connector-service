from typing import Any, Dict

import logging

from classy_fastapi import Routable, delete, get, post
from fastapi import APIRouter, Body, Query, status

from app.response import JSONLDResponse
from app.tags import Tags

logger = logging.getLogger(__name__)


class ConnectorRoutes(Routable):
    def __init__(self):
        super().__init__()

    @post(
        "/data-products/",
        operation_id="create_data_product",
        name="Create Data Product",
        tags=[Tags.Data_products],
        responses={
            201: {"description": "Data product created successfully"},
            400: {"description": "Invalid input"},
        },
    )
    async def create_data_product(
        self, data_product: Dict[str, Any] = Body(...)
    ) -> JSONLDResponse:
        """Register a new data product (metadata only)"""
        # Stub: In real case, store metadata in Catalog/Connector DB
        return JSONLDResponse(
            {
                "id": "dp-12345",
                "name": data_product.get("name", "unnamed"),
                "mimetype": data_product.get("mimetype", "application/octet-stream"),
                "size": data_product.get("size", 0),
                "tags": data_product.get("tags", []),
                "status": "created",
            },
            status_code=status.HTTP_201_CREATED,
        )

    @get(
        "/health-check/",
        operation_id="health_check",
        name="Health Check",
        tags=[Tags.Health],
        responses={200: {"description": "Service is healthy"}},
    )
    async def health_check(self) -> JSONLDResponse:
        """Check if the Connector service is running"""
        return JSONLDResponse({"status": "healthy"}, status_code=status.HTTP_200_OK)

    @get(
        "/metrics",
        operation_id="get_metrics",
        name="Metrics",
        tags=[Tags.Monitoring],
        responses={200: {"description": "Prometheus metrics"}},
    )
    async def get_metrics(self) -> str:
        """Return Prometheus metrics"""
        return "# Prometheus metrics placeholder"

    @get(
        "/data-products/",
        operation_id="list_data_products",
        name="List Data Products",
        tags=[Tags.Data_products],
        responses={200: {"description": "List of data products"}},
    )
    async def list_data_products(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(100, ge=1, le=1000),
    ) -> JSONLDResponse:
        """Return paginated list of available data products"""
        return JSONLDResponse(
            {
                "data_products": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
            },
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/data-products/{connector_id}/{data_product_id}/",
        operation_id="get_data_product",
        name="Get Data Product",
        tags=[Tags.Data_products],
        responses={200: {"description": "Data product metadata"}},
    )
    async def get_data_product(
        self, connector_id: str, data_product_id: str
    ) -> JSONLDResponse:
        """Return metadata for a specific data product"""
        return JSONLDResponse(
            {
                "connector_id": connector_id,
                "data_product_id": data_product_id,
                "metadata": {},
            },
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/data-products/{connector_id}/{data_product_id}/content",
        operation_id="get_data_product_content",
        name="Get Data Product Content",
        tags=[Tags.Data_products],
        responses={200: {"description": "MMIO object with data product content"}},
    )
    async def get_data_product_content(
        self, connector_id: str, data_product_id: str
    ) -> JSONLDResponse:
        """Retrieve data product content wrapped in MMIO"""
        return JSONLDResponse(
            {
                "connector_id": connector_id,
                "data_product_id": data_product_id,
                "content": {},
            },
            status_code=status.HTTP_200_OK,
        )

    @delete(
        "/data-products/{connector_id}/{data_product_id}/",
        operation_id="delete_data_product",
        name="Delete Data Product",
        tags=[Tags.Data_products],
        responses={
            200: {"description": "Data product deleted successfully"},
            404: {"description": "Data product not found"},
        },
    )
    async def delete_data_product(
        self, connector_id: str, data_product_id: str
    ) -> JSONLDResponse:
        """Delete a data product (delegated to the underlying Interface)"""
        # Stub: In real case, call Interface/S3 to remove object
        return JSONLDResponse(
            {
                "connector_id": connector_id,
                "data_product_id": data_product_id,
                "deleted": True,
            },
            status_code=status.HTTP_200_OK,
        )

    @post(
        "/contracts/validate",
        operation_id="validate_contract",
        name="Validate Contract",
        tags=[Tags.Contracts],
        responses={
            200: {"description": "Contract is valid"},
            403: {"description": "Invalid contract"},
        },
    )
    async def validate_contract(self, contract: Dict[str, Any]) -> JSONLDResponse:
        """Validate a contract before allowing access to data"""
        return JSONLDResponse(
            {
                "valid": True,
                "contract": contract,
            },
            status_code=status.HTTP_200_OK,
        )

    @post(
        "/transactions/",
        operation_id="log_transaction",
        name="Log Transaction",
        tags=[Tags.Transactions],
        responses={201: {"description": "Transaction recorded"}},
    )
    async def log_transaction(self, transaction: Dict[str, Any]) -> JSONLDResponse:
        """Record a transaction in the Clearing House"""
        return JSONLDResponse(
            {
                "transaction_id": "12345",
                "status": "recorded",
            },
            status_code=status.HTTP_201_CREATED,
        )


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
