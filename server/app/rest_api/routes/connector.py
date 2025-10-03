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


def get_usecases(interface_id: str) -> usecases.DataproductUseCase:
    # In real implementation, this would fetch a client from ClientFactory
    client: BaseReadDataClient = client_factory.get_client_by_name(interface_id)
    return usecases.DataproductUseCase(client)


class ConnectorRoutes(Routable):
    def __init__(self):
        super().__init__()

    @get(
        "/metadata/connector",
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
        "/metadata/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_dataproduct_metadata",
        name="Get Data Product Distribution",
        tags=[Tags.Data_products],
    )
    async def get_dataproduct_metadata(
        self,
        interface_id: str,
        resource_path: str,
        resource_name: str,
        usecases: usecases.DataproductUseCase = Depends(get_usecases),
    ) -> JSONResponse:
        """Return Metadata for a data product along with region."""
        logger.info(
            f"Getting metadata for a single data product for interface: {interface_id}"
        )

        dataproduct_metadata = await usecases.get_dataproduct_metadata(
            resource_path, resource_name
        )
        return JSONResponse(
            content={"region": "ki", "distribution": dataproduct_metadata.dict()},
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/content/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_dataproduct_content",
        name="Get Data Product Content",
        tags=[Tags.Data_products],
    )
    async def get_dataproduct_content(
        self,
        interface_id: str,
        resource_path: str,
        resource_name: str,
        usecases: usecases.DataproductUseCase = Depends(get_usecases),
    ) -> StreamingResponse:
        """Return the full dataset content."""

        # Get metadata to determine correct media type
        metadata = await usecases.get_dataproduct_metadata(resource_path, resource_name)

        full_content = await usecases.read_dataproduct_distribution_content(
            resource_path, resource_name
        )

        return StreamingResponse(
            iter([full_content]),
            media_type=metadata.media_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{resource_name}"'},
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/content/{interface_id}/{resource_path:path}/{resource_name}/chunk",
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
        resource_name: str,
        start: Optional[int] = Query(None, description="Start byte position"),
        end: Optional[int] = Query(None, description="End byte position"),
    ) -> StreamingResponse:
        """Return a dataset chunk (partial CSV content)."""
        return StreamingResponse(
            iter([b"partial,data\n"]),
            media_type="text/csv",
            headers={
                "Content-Range": (
                    f"bytes={start}-{end}"
                    if start is not None and end is not None
                    else "bytes */*"
                )
            },
            status_code=(
                status.HTTP_206_PARTIAL_CONTENT
                if start is not None and end is not None
                else status.HTTP_200_OK
            ),
        )

    @get(
        "/metadata-list/{interface_id}/{resource_path:path}",
        operation_id="list_dataproducts",
        name="List Data Products",
        tags=[Tags.Data_products],
        response_model=List[DataProductItem],
    )
    async def list_dataproducts(
        self,
        interface_id: str,
        resource_path: str,
        usecases: usecases.DataproductUseCase = Depends(get_usecases),
    ) -> JSONResponse:
        """Return a paginated list of data product distributions with region."""
        logger.info(f"Listing data products for interface: {interface_id}")
        all_dataproducts_metadata = await usecases.list_dataproducts(resource_path)

        # TODO Implement pagination logic here if needed
        return JSONResponse(
            content={
                "region": "ki",
                "data_products": [d.dict() for d in all_dataproducts_metadata],
            },
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/health/{interface_id}",
        operation_id="health_check",
        name="Health Check",
        tags=[Tags.Data_products],
    )
    async def health_check(
        self,
        interface_id: str,
        usecases: usecases.DataproductUseCase = Depends(get_usecases),
    ) -> JSONResponse:
        try:
            health = await usecases.health_check()
            return JSONResponse(content=health, status_code=status.HTTP_200_OK)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
