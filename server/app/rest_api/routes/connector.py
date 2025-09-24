from typing import List, Optional

from classy_fastapi import Routable, get
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.schemas import connector as schemas
from app.tags import Tags


class ConnectorRoutes(Routable):
    def __init__(self):
        super().__init__()

    @get(
        "/metadata/connector",
        operation_id="get_connector_metadata",
        name="Get Connector Metadata",
        tags=[Tags.Data_products],
        response_model=schemas.ConnectorMetadata,
    )
    async def get_connector_metadata(self) -> JSONResponse:
        return JSONResponse(
            content={
                "connector_id": "ds-connector-service",
                "region": "eu-central-1",
                "supported_interfaces": ["s3", "rest", "sql"],
                "status": "healthy",
                "version": "0.1.0",
            },
            status_code=status.HTTP_200_OK,
        )

    @get(
        "/metadata/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_dataproduct_metadata",
        name="Get Data Product Metadata",
        tags=[Tags.Data_products],
        response_model=schemas.DataProduct,
    )
    async def get_dataproduct_metadata(
        self,
        interface_id: str,
        resource_path: str,
        resource_name: str,
    ) -> JSONResponse:
        """Return metadata of a single data product (plain JSON)."""
        product = schemas.DataProduct(
            id=f"s3://{resource_path}/{resource_name}",
            identifier=resource_name,
            title=resource_name,
            description=f"Description for {resource_name}",
            publisher={"type": "organization", "name": "ds-connector-service"},
            keyword=["s3"],
            distribution=[
                schemas.DataProductDistribution(
                    title=f"Distribution of {resource_name}",
                    access_url=f"http://connector-service/content/dataproducts/"
                    f"{interface_id}/{resource_path}/{resource_name}",
                    media_type="text/csv",
                    byte_size=123456,
                )
            ],
            region="ki",  # or "hus" depending on your logic
        )
        return JSONResponse(content=product.dict(), status_code=status.HTTP_200_OK)

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
                "Content-Range": f"bytes={start}-{end}"
                if start is not None and end is not None
                else "bytes */*"
            },
            status_code=(
                status.HTTP_206_PARTIAL_CONTENT
                if start is not None and end is not None
                else status.HTTP_200_OK
            ),
        )

    @get(
        "/metadata/dataproducts",
        operation_id="list_dataproducts",
        name="List Data Products",
        tags=[Tags.Data_products],
        response_model=List[schemas.DataProductSummary],
    )
    async def list_dataproducts(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    ) -> JSONResponse:
        """Return a paginated list of data products."""
        all_data_products = [
            {
                "id": f"s3://datasets/{i}/data_{i}.csv",
                "name": f"data_{i}.csv",
                "description": f"Description for data_{i}",
            }
            for i in range(1, 51)
        ]
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_data_products = all_data_products[start_index:end_index]

        return JSONResponse(
            content={
                "page": page,
                "page_size": page_size,
                "total": len(all_data_products),
                "dataproducts": paginated_data_products,
            },
            status_code=status.HTTP_200_OK,
        )


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
