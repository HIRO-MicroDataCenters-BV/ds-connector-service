from typing import List, Optional

import logging

from classy_fastapi import Routable, get
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.core import usecases
from app.core.clients.base import BaseReadDataClient
from app.core.clients.factory_instance import client_factory
from app.tags import Tags

from ..serializers import ConnectorMetadata, DataProductItem

logger = logging.getLogger(__name__)


def get_read_usecases(interface_id: str) -> usecases.DataProductReadUseCase:
    """
    Get read use cases for the specified interface

    Args:
        interface_id: Interface identifier (s3, file, etc.)

    Returns:
        DataProductWriteUseCase instance

    Raises:
        HTTPException: If interface is not supported
    """
    client: BaseReadDataClient = client_factory.get_read_client_by_name(interface_id)
    return usecases.DataProductReadUseCase(client)


class ConnectorReadRoutes(Routable):
    """Routes for data product read operations"""

    def __init__(self):
        super().__init__()

    @get(
        "/connector-metadata",
        operation_id="get_connector_metadata",
        name="Get Connector Metadata",
        tags=[Tags.Data_products],
        response_model=ConnectorMetadata,
    )
    async def get_connector_metadata(self) -> JSONResponse:
        return JSONResponse(
            content={
                "connector_id": "ds-connector-service",
                "region": "eu-central-1",
                "supported_interfaces": ["s3", "rest", "file"],
                "status": "healthy",
                "version": "0.1.0",
            },
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/distribution-metadata/{interface_id}/{resource_path:path}",
        operation_id="get_distribution_metadata",
        name="Get Distribution Metadata",
        tags=[Tags.Data_products],
    )
    async def get_distribution_metadata(
        self,
        interface_id: str,
        resource_path: str,
        usecases: usecases.DataProductReadUseCase = Depends(get_read_usecases),
    ) -> JSONResponse:
        """Return Metadata for a distribution along with region."""
        logger.info(
            f"Getting metadata for a single distribution for interface: {interface_id}"
        )

        distribution_metadata = await usecases.get_distribution_metadata(
            resource_path=resource_path
        )
        return JSONResponse(
            content={"region": "ki", "distribution": distribution_metadata.dict()},
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/distribution-content/{interface_id}/" "{resource_path:path}/chunk",
        operation_id="get_dataproduct_chunk",
        name="Get Data Product Chunk",
        tags=[Tags.Data_products],
        responses={
            200: {"description": "Full chunk when no range specified"},
            206: {
                "description": "Partial content chunk",
                "content": {"text/csv": {"example": "partial,data\n"}},
                "headers": {
                    "Content-Range": {
                        "description": "Range of bytes returned",
                        "schema": {"type": "string", "example": "bytes=0-1023"},
                    }
                },
            },
            404: {"description": "Data product not found"},
            416: {"description": "Range not satisfiable"},
        },
    )
    async def get_dataproduct_chunk(
        self,
        interface_id: str,
        resource_path: str,
        range_header: Optional[str] = Query(
            None,
            description="HTTP Range header for partial content requests",
            example="bytes=0-1023",
        ),
        usecases: usecases.DataProductReadUseCase = Depends(get_read_usecases),
    ) -> StreamingResponse:
        """Return a dataset chunk (partial CSV content)."""

        # Get metadata to determine correct media type
        metadata = await usecases.get_distribution_metadata(resource_path=resource_path)

        # Stream content with range support
        content_generator = usecases.stream_dataproduct_distribution_content(
            resource_path=resource_path, range_header=range_header
        )

        # Determine response headers and status
        headers = {}
        status_code = status.HTTP_200_OK

        if range_header:
            # For range requests, we should return 206 Partial Content
            headers["Content-Range"] = f"{range_header}/*"
            status_code = status.HTTP_206_PARTIAL_CONTENT
        else:
            # Full file streaming - show download link in Swagger
            headers["Content-Disposition"] = f'attachment; filename="{metadata.title}"'

        return StreamingResponse(
            content_generator,
            media_type=metadata.media_type or "application/octet-stream",
            headers=headers,
            status_code=status_code,
        )

    @get(
        "/distribution-content/{interface_id}/{resource_path:path}",
        operation_id="get_dataproduct_content",
        name="Get Data Product Content",
        tags=[Tags.Data_products],
    )
    async def get_dataproduct_content(
        self,
        interface_id: str,
        resource_path: str,
        usecases: usecases.DataProductReadUseCase = Depends(get_read_usecases),
    ) -> StreamingResponse:
        """Return the full dataset content."""
        logger.info("Getting full data product content as a single response")
        # Get metadata to determine correct media type
        metadata = await usecases.get_distribution_metadata(resource_path=resource_path)

        full_content = await usecases.read_dataproduct_distribution_content(
            resource_path=resource_path
        )

        return StreamingResponse(
            iter([full_content]),
            media_type=metadata.media_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{metadata.title}"'},
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/dataproduct-distributions/{interface_id}/{directory_resource_path:path}",
        operation_id="list_dataproduct_distributions",
        name="List Data Product Distributions",
        tags=[Tags.Data_products],
        response_model=List[DataProductItem],
    )
    async def list_dataproduct_distributions(
        self,
        interface_id: str,
        directory_resource_path: str,
        usecases: usecases.DataProductReadUseCase = Depends(get_read_usecases),
    ) -> JSONResponse:
        """Return a paginated list of data product distributions with region."""
        logger.info(f"Listing data products for interface: {interface_id}")
        all_dataproducts_metadata = await usecases.list_dataproduct_distributions(
            directory_resource_path
        )

        # TODO Implement pagination logic here if needed
        return JSONResponse(
            content={
                "region": "ki",
                "data_products": [d.dict() for d in all_dataproducts_metadata],
            },
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/dataproducts/{interface_id}",
        operation_id="list_dataproducts",
        name="List Data Products",
        tags=[Tags.Data_products],
        response_model=List[str],
    )
    async def list_dataproducts(
        self,
        interface_id: str,
        usecases: usecases.DataProductReadUseCase = Depends(get_read_usecases),
    ) -> JSONResponse:
        """List available data products from the base path."""
        logger.info(f"Listing data products for interface: {interface_id}")
        dataproducts = await usecases.list_dataproducts()
        return JSONResponse(
            content={"dataproducts": dataproducts},
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/interface-health/{interface_id}",
        operation_id="health_check",
        name="Health Check",
        tags=[Tags.Data_products],
    )
    async def health_check(
        self,
        interface_id: str,
        usecases: usecases.DataProductReadUseCase = Depends(get_read_usecases),
    ) -> JSONResponse:
        """Perform health check on the specified interface."""
        logger.info(f"Performing health check for interface: {interface_id}")
        try:
            health = await usecases.health_check()
            return JSONResponse(content=health, status_code=status.HTTP_200_OK)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# Create the router
read_router = APIRouter()
connector_read_routes = ConnectorReadRoutes()
read_router.include_router(connector_read_routes.router)
