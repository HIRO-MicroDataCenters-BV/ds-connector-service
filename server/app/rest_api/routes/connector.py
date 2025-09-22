from typing import Dict, Any, Optional
from classy_fastapi import Routable, get
from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.response import JSONLDResponse
from app.tags import Tags


class DCATContext(BaseModel):
    dcat: str = Field(default="http://www.w3.org/ns/dcat#", alias="dcat")
    dcterms: str = Field(default="http://purl.org/dc/terms/", alias="dcterms")
    foaf: str = Field(default="http://xmlns.com/foaf/0.1/", alias="foaf")
    xsd: str = Field(default="http://www.w3.org/2001/XMLSchema#", alias="xsd")


class DCATPublisher(BaseModel):
    type: str = Field(default="foaf:Organization", alias="@type")
    name: str = Field(alias="foaf:name")


class DCATAccessURL(BaseModel):
    id: str = Field(alias="@id")


class DCATDistribution(BaseModel):
    type: str = Field(default="dcat:Distribution", alias="@type")
    title: str = Field(alias="dcterms:title")
    access_url: DCATAccessURL = Field(alias="dcat:accessURL")
    media_type: str = Field(alias="dcat:mediaType")
    byte_size: int = Field(alias="dcat:byteSize")


class DCATDataset(BaseModel):
    context: DCATContext = Field(alias="@context")
    id: str = Field(alias="@id")
    type: str = Field(default="dcat:Dataset", alias="@type")
    identifier: str = Field(alias="dcterms:identifier")
    title: str = Field(alias="dcterms:title")
    description: str = Field(alias="dcterms:description")
    publisher: DCATPublisher = Field(alias="dcterms:publisher")
    keyword: list[str] = Field(alias="dcat:keyword")
    distribution: list[DCATDistribution] = Field(alias="dcat:distribution")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "@context": {
                    "dcat": "http://www.w3.org/ns/dcat#",
                    "dcterms": "http://purl.org/dc/terms/",
                    "foaf": "http://xmlns.com/foaf/0.1/",
                    "xsd": "http://www.w3.org/2001/XMLSchema#",
                },
                "@id": "s3://bucket/path/dataset.csv",
                "@type": "dcat:Dataset",
                "dcterms:identifier": "dataset.csv",
                "dcterms:title": "dataset.csv",
                "dcterms:description": "Dataset description following DCAT specification",
                "dcterms:publisher": {
                    "@type": "foaf:Organization",
                    "foaf:name": "ds-connector-service",
                },
                "dcat:keyword": ["ml", "training", "s3"],
                "dcat:distribution": [
                    {
                        "@type": "dcat:Distribution",
                        "dcterms:title": "Distribution of dataset.csv",
                        "dcat:accessURL": {
                            "@id": "http://connector-service/interfaces/s3/bucket/path/dataset.csv/content"
                        },
                        "dcat:mediaType": "text/csv",
                        "dcat:byteSize": 123456,
                    }
                ],
            }
        }


class ConnectorMetadata(BaseModel):
    connector_id: str
    region: str
    supported_interfaces: list[str]
    status: str
    version: str


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
        response_model=DCATDataset,
        responses={
            200: {
                "description": "Data product metadata in DCAT format",
                "content": {
                    "application/ld+json": {
                        "example": {
                            "@context": {
                                "dcat": "http://www.w3.org/ns/dcat#",
                                "dcterms": "http://purl.org/dc/terms/",
                                "foaf": "http://xmlns.com/foaf/0.1/"
                            },
                            "@id": "s3://datasets/customers/churn.csv",
                            "@type": "dcat:Dataset",
                            "dcterms:identifier": "churn.csv",
                            "dcterms:title": "Customer Churn Dataset",
                            "dcterms:description": "Dataset for churn prediction",
                            "dcterms:publisher": {
                                "@type": "foaf:Organization",
                                "foaf:name": "ds-connector-service"
                            },
                            "dcat:keyword": ["ml", "training", "s3"],
                            "dcat:distribution": [
                                {
                                    "@type": "dcat:Distribution",
                                    "dcterms:title": "Churn CSV distribution",
                                    "dcat:accessURL": {
                                        "@id": "http://connector-service/content/dataproducts/1/datasets/customers/churn.csv"
                                    },
                                    "dcat:mediaType": "text/csv",
                                    "dcat:byteSize": 1048576
                                }
                            ]
                        }
                    }
                }
            },
            404: {"description": "Data product not found"},
            500: {"description": "Internal server error"}
        },
    )
    async def get_data_product_metadata(
        self,
        interface_id: str,
        resource_path: str,
        resource_name: str,
    ) -> JSONResponse:
        """Return metadata of a data product in DCAT format compliant with W3C DCAT specification"""

        dataset_id = f"s3://{resource_path}/{resource_name}"

        response = {
            "@context": {
                "dcat": "http://www.w3.org/ns/dcat#",
                "dcterms": "http://purl.org/dc/terms/",
                "foaf": "http://xmlns.com/foaf/0.1/"
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
            "dcat:keyword": ["s3"],
            "dcat:distribution": [
                {
                    "@type": "dcat:Distribution",
                    "dcterms:title": f"Distribution of {resource_name}",
                    "dcat:accessURL": {
                        "@id": f"http://connector-service/content/dataproducts/{interface_id}/{resource_path}/{resource_name}"
                    },
                    "dcat:mediaType": "text/csv",
                    "dcat:byteSize": 123456
                }
            ]
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
                "content": {"text/csv": {"example": "mock,full,object,content\n1,2,3,4\n"}}
            },
            404: {"description": "Data product not found"}
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
                        "schema": {"type": "string", "example": "bytes=0-1023"}
                    }
                }
            },
            404: {"description": "Data product not found"},
            416: {"description": "Range not satisfiable"}
        },
    )
    async def get_data_product_chunk(
        self,
        interface_id: str,
        resource_path: str,
        resource_name: str,
        start: Optional[int] = Query(None, description="Start byte position for chunk"),
        end: Optional[int] = Query(None, description="End byte position for chunk"),
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


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
