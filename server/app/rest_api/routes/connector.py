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

    # ---------------------------
    # Health & Monitoring
    # ---------------------------

    @get(
        "/health-check/",
        operation_id="health_check",
        name="Health Check",
        tags=[Tags.Health],
    )
    async def health_check(self) -> JSONLDResponse:
        """Check if the Connector service is running"""
        return JSONLDResponse({"status": "healthy"}, status_code=status.HTTP_200_OK)

    @get(
        "/metrics",
        operation_id="get_metrics",
        name="Metrics",
        tags=[Tags.Monitoring],
    )
    async def get_metrics(self) -> str:
        """Return Prometheus metrics"""
        return "# Prometheus metrics placeholder"

    # ---------------------------
    # Connector Metadata
    # ---------------------------

    @get(
        "/metadata/connector",
        operation_id="get_connector_metadata",
        name="Get Connector Metadata",
        tags=[Tags.Data_products],
    )
    async def get_connector_metadata(self) -> JSONLDResponse:
        """Return connector metadata (region, supported interfaces, etc.)"""
         
        return JSONLDResponse(
            {
                "connector_id": "ds-connector-service",
                "region": "eu-central-1",
                "supported_interfaces": ["s3", "rest", "sql"],
                "status": "healthy",
                "version": "0.1.0",
            },
            status_code=status.HTTP_200_OK,
        )

    # ---------------------------
    # Data Products (generic path instead of connector_id)
    # ---------------------------

    @get(
        "/metadata/dataproducts/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_metadata",
        name="Get Data Product Metadata",
        tags=[Tags.Data_products],
    )
    async def get_data_product_metadata(
        self, interface_id: str, resource_path: str, resource_name: str
    ) -> JSONLDResponse:
        """Return metadata of a data product (size, mimetype, region, etc.)"""
        # Stub: here you’d call boto3 / SQL / REST interface
        # need to add region, node_labe: ki,hus,uva in the respone at end, so call k8s API to get node selector
        # need to pass presigned link to ml runner directly
        # dataproduct name need to add in response 
        # displayname need to inject "empty"
        # need to inject connector name 
        
        return JSONLDResponse(
            {
                "interface_id": interface_id,
                "resource": f"{resource_path}/{resource_name}",
                "location": f"s3://{resource_path}/{resource_name}",
                "size_bytes": 123456,
                "mimetype": "application/csv",
                "last_modified": "2025-09-16T12:00:00Z",
            },
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/{interface_id}/{resource_path:path}/{resource_name}/content",
        operation_id="get_data_product_content",
        name="Get Data Product Content",
        tags=[Tags.Data_products],
    )
    async def get_data_product_content(
        self, interface_id: str, resource_path: str, resource_name: str
    ) -> JSONLDResponse:
        """Retrieve data product content (via interface)"""
        # update endpoint to get the chunks
        # one more endpoint to get the whole information at time( no chunking getting data)
        # option 2 - connector acts as gateway
        # need to add wrapper for data to pass ML runner
        # Stub: here you’d request pre-signed URL from S3, or query SQL, etc.
        return JSONLDResponse(
            {
                "interface_id": interface_id,
                "resource": f"{resource_path}/{resource_name}",
                "access_url": f"https://presigned-url/{resource_path}/{resource_name}",
            },
            status_code=status.HTTP_200_OK,
        )


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
