from typing import List, Optional

from classy_fastapi import Routable, get
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.response import JSONLDResponse
from app.tags import Tags
from app import schemas


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

    @get(
        "/metadata/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_metadata",
        name="Get Data Product Metadata",
        tags=[Tags.Data_products],
        response_model=schemas.DCATDataset,
        responses={
            200: {
                "description": "Data product metadata in DCAT format",
                "content": {
                    "application/ld+json": {
                        "example": {
                            "@context": {
                                "dcat": "http://www.w3.org/ns/dcat#",
                                "dcterms": "http://purl.org/dc/terms/",
                                "foaf": "http://xmlns.com/foaf/0.1/",
                            },
                            "@id": "s3://datasets/customers/churn.csv",
                            "@type": "dcat:Dataset",
                            "dcterms:identifier": "churn.csv",
                            "dcterms:title": "Customer  Dataset",
                            "dcterms:description": "Dataset for churn prediction",
                            "dcterms:publisher": {
                                "@type": "foaf:Organization",
                                "foaf:name": "ds-connector-service",
                            },
                            "dcat:keyword": ["ml", "training", "s3"],
                            "dcat:distribution": [
                                {
                                    "@type": "dcat:Distribution",
                                    "dcterms:title": "Churn CSV distribution",
                                    "dcat:accessURL": {
                                        "@id": "http://connector-service/content/"
                                        "dataproducts/1/"
                                        "datasets/customers/churn.csv"
                                    },
                                    "dcat:mediaType": "text/csv",
                                    "dcat:byteSize": 1048576,
                                }
                            ],
                        }
                    }
                },
            },
            404: {"description": "Data product not found"},
            500: {"description": "Internal server error"},
        },
    )
    async def get_data_product_metadata(
        self,
        interface_id: str,
        resource_path: str,
        resource_name: str,
    ) -> JSONResponse:
        """Return metadata of a data product in DCAT format
        compliant with W3C DCAT specification"""

        dataset_id = f"s3://{resource_path}/{resource_name}"

        response = {
            "@context": {
                "dcat": "http://www.w3.org/ns/dcat#",
                "dcterms": "http://purl.org/dc/terms/",
                "foaf": "http://xmlns.com/foaf/0.1/",
            },
            "@id": dataset_id,
            "@type": "dcat:Dataset",
            "dcterms:identifier": resource_name,
            "dcterms:title": resource_name,
            "dcterms:description": "Mocked description of the data product",
            "dcterms:publisher": {
                "@type": "foaf:Organization",
                "foaf:name": "ds-connector-service",
            },
            "dcat:keyword": ["s3"],
            "dcat:distribution": [
                {
                    "@type": "dcat:Distribution",
                    "dcterms:title": f"Distribution of {resource_name}",
                    "dcat:accessURL": {
                        "@id": f"http://connector-service/content/dataproducts/"
                        f"{interface_id}/{resource_path}/{resource_name}"
                    },
                    "dcat:mediaType": "text/csv",
                    "dcat:byteSize": 123456,
                }
            ],
            "region": "ki",
        }

        return JSONResponse(content=response, media_type="application/ld+json")

    @get(
        "/content/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_content",
        name="Get Data Product Content",
        tags=[Tags.Data_products],
        responses={
            200: {
                "description": "Full data product content",
                "content": {
                    "text/csv": {"example": "mock,full,object,content\n1,2,3,4\n"}
                },
            },
            404: {"description": "Data product not found"},
        },
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

    @get(
        "/content/{interface_id}/{resource_path:path}/{resource_name}/chunk",
        operation_id="get_data_product_chunk",
        name="Get Data Product Chunk",
        tags=[Tags.Data_products],
        responses={
            200: {"description": "Full chunk when no range specified"},
            206: {
                "description": "Partial content chunk",
                "content": {"text/csv": {"example": "mock,chunked,data\n"}},
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
    async def get_data_product_chunk(
        self,
        interface_id: str,
        resource_path: str,
        resource_name: str,
        start: Optional[int] = Query(None, description="Start byte position"),
        end: Optional[int] = Query(None, description="End byte position"),
    ) -> StreamingResponse:
        return StreamingResponse(
            iter([b"mock,chunked,data\n"]),
            media_type="text/csv",
            headers={
                "Content-Range": f"bytes={start}-{end}"
                if start and end
                else "bytes */*"
            },
            status_code=status.HTTP_206_PARTIAL_CONTENT
            if start and end
            else status.HTTP_200_OK,
        )

    @get(
        "/metadata/dataproducts",
        operation_id="list_data_products",
        name="List Data Products",
        tags=[Tags.Data_products],
        response_model=List[schemas.DataProductSummary],
        responses={
            200: {
                "description": "List of data products with pagination",
                "content": {
                    "application/json": {
                        "example": [
                            {
                                "id": "s3://datasets/customers/churn.csv",
                                "name": "churn.csv",
                                "description": "Customer churn dataset",
                            },
                            {
                                "id": "s3://datasets/sales/sales.csv",
                                "name": "sales.csv",
                                "description": "Sales dataset",
                            },
                        ]
                    }
                },
            },
        },
    )
    async def list_data_products(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(
            10, ge=1, le=100, description="Number of items per page"
        ),
    ) -> JSONResponse:
        """Return a paginated list of data products"""

        # Mocked dataset list
        all_data_products = [
            {
                "id": f"s3://datasets/{i}/data_{i}.csv",
                "name": f"data_{i}.csv",
                "description": f"Description for data_{i}",
            }
            for i in range(1, 51)  # total 50 data products
        ]

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_data_products = all_data_products[start_index:end_index]

        return JSONResponse(
            content={
                "page": page,
                "page_size": page_size,
                "total": len(all_data_products),
                "data_products": paginated_data_products,
            },
            status_code=status.HTTP_200_OK,
        )


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
