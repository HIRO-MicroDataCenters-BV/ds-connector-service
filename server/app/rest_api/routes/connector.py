from typing import List, Optional

from classy_fastapi import Routable, get
from fastapi import APIRouter, Query, status, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from app.core import usecases
from app.core.clients.client_factory import ClientFactory
from ..serializers import DataProductDistribution, DataProductItem, ConnectorMetadata
from app.tags import Tags
from app.core.clients.factory_instance import client_factory
from app.core.source_type import SourceType


def get_usecases(interface_id: str) -> usecases.DataproductUseCase:
    # In real implementation, this would fetch a client from ClientFactory
    client = client_factory.get_client_by_name(interface_id)
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
        self, interface_id: str, resource_path: str, resource_name: str
    ) -> StreamingResponse:
        """Return the full dataset content (CSV)."""
        return StreamingResponse(
            iter([b"full,object,content\n1,2,3,4\n"] * 10),
            media_type="text/csv",
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
        "/metadata/{interface_id}/{resource_path}/dataproducts",
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
        # page: int = Query(1, ge=1, description="Page number"),
        # page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    ) -> JSONResponse:
        """Return a paginated list of data product distributions with region."""

        all_dataproducts_metadata = usecases.list_dataproducts(resource_path)

        ## TODO Implement pagination logic here if needed
        return JSONResponse(
            content={
                "region": "ki",
                "data_products": [d.dict() for d in all_dataproducts_metadata],
            },
            status_code=status.HTTP_200_OK,
        )


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
