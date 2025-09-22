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

    from fastapi import Query
    from fastapi.responses import JSONResponse

    @get(
        "/metadata/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_metadata",
        name="Get Data Product Metadata",
        tags=[Tags.Data_products],
        responses={200: {"description": "Data product metadata in DCAT format"}},
    )
    async def get_data_product_metadata( self,interface_id: str, resource_path: str, resource_name: str,
    ) -> JSONResponse:
        """Return metadata of a data product in DCAT format"""

        dataset_id = f"s3://{resource_path}/{resource_name}"

        response = {
            "@context": {
                "dcat": "http://www.w3.org/ns/dcat#",
                "dcterms": "http://purl.org/dc/terms/",
                "foaf": "http://xmlns.com/foaf/0.1/",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            },
            "@id": dataset_id,
            "@type": "dcat:Dataset",
            "dcterms:identifier": resource_name,
            "dcterms:title": resource_name,
            "dcterms:description": "Mocked description of the data product",
            "dcterms:publisher": {
                "@type": "foaf:Organization",
                "foaf:name": "ds-connector-service"
            },
            "dcat:keyword": ["ml", "training", "s3"],
            "dcat:distribution": [
                {
                    "@type": "dcat:Distribution",
                    "dcterms:title": f"Distribution of {resource_name}",
                    "dcat:accessURL": {
                        "@id": f"http://connector-service/interfaces/{interface_id}/{resource_path}/{resource_name}/content"
                    },
                    "dcat:mediaType": "text/csv",
                    "dcat:byteSize": 123456,
                }
            ]
        }

        return JSONResponse(content=response, media_type="application/ld+json")

    @get(
        "/content/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_content",
        name="Get Data Product Content",
        tags=[Tags.Data_products],
    )
    async def get_data_product_content(
        self, interface_id: str, resource_path: str, resource_name: str
    ) -> StreamingResponse:
        return StreamingResponse(
            iter([b"mock,full,object,content\n1,2,3,4\n"] * 10),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{resource_name}"'},
            status_code=status.HTTP_200_OK,
        )

    # --- Chunked object content ---
    @get(
        "/content/{interface_id}/{resource_path:path}/{resource_name}/chunk",
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
    ) -> StreamingResponse:
        return StreamingResponse(
            iter([b"mock,chunked,data\n"]),
            media_type="text/csv",
            headers={"Content-Range": f"bytes={start}-{end}" if start and end else "bytes */*"},
            status_code=status.HTTP_206_PARTIAL_CONTENT if start and end else status.HTTP_200_OK,
        )


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
