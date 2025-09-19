from classy_fastapi import Routable, get
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from app.response import JSONLDResponse
from app.tags import Tags


class ConnectorRoutes(Routable):
    def __init__(self):
        super().__init__()

    # --- Connector metadata ---
    @get(
        "/metadata/connector",
        operation_id="get_connector_metadata",
        name="Get Connector Metadata",
        tags=[Tags.Data_products],
    )
    async def get_connector_metadata(self) -> JSONLDResponse:
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

    # --- Data product metadata ---
    @get(
        "/metadata/dataproducts/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_metadata",
        name="Get Data Product Metadata",
        tags=[Tags.Data_products],
    )
    async def get_data_product_metadata(
        self, interface_id: str, resource_path: str, resource_name: str
    ):
        response = {
            "@context": {
                "dcat": "http://www.w3.org/ns/dcat#",
                "dcterms": "http://purl.org/dc/terms/",
            },
            "@id": f"{interface_id}://{resource_path}/{resource_name}",
            "@type": "dcat:Dataset",
            "dcterms:identifier": resource_name,
            "dcterms:title": resource_name,
            "dcat:distribution": [
                {
                    "@type": "dcat:Distribution",
                    "dcat:accessURL": {
                        "@id": f"http://connector-service/content/dataproducts/{interface_id}/{resource_path}/{resource_name}"
                    },
                    "dcat:mediaType": "text/csv",
                    "dcat:byteSize": 123456,
                }
            ],
            "dcterms:spatial": {"dcterms:Location": ["ki", "hus", "uva"]},
            "dcterms:publisher": "ds-connector-service",
            "dcterms:modified": "2025-09-16T12:00:00Z",
        }
        return JSONResponse(content=response, media_type="application/ld+json")

    # --- Whole object content ---
    @get(
        "/content/dataproducts/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_content",
        name="Get Data Product Content",
        tags=[Tags.Data_products],
    )
    async def get_data_product_content(
        self, interface_id: str, resource_path: str, resource_name: str
    ):
        return StreamingResponse(
            iter([b"mock,full,object,content\n1,2,3,4\n"] * 10),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{resource_name}"'},
            status_code=status.HTTP_200_OK,
        )

    # --- Chunked object content ---
    @get(
        "/content/dataproducts/{interface_id}/{resource_path:path}/{resource_name}/chunk",
        operation_id="get_data_product_chunk",
        name="Get Data Product Chunk",
        tags=[Tags.Data_products],
    )
    async def get_data_product_chunk(
        self,
        interface_id: str,
        resource_path: str,
        resource_name: str,
        start: int | None = Query(None),
        end: int | None = Query(None),
    ):
        return StreamingResponse(
            iter([b"mock,chunked,data\n"]),
            media_type="text/csv",
            headers={"Content-Range": f"bytes={start}-{end}" if start and end else "bytes */*"},
            status_code=status.HTTP_206_PARTIAL_CONTENT if start and end else status.HTTP_200_OK,
        )



router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
