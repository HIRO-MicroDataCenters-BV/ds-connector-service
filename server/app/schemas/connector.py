"""Schemas for data connector and data product metadata."""

from pydantic import BaseModel, Field


class DataProductSummary(BaseModel):
    id: str
    name: str
    description: str


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
                "dcterms:description": "Dataset description following "
                "DCAT specification",
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
                            "@id": "http://connector-service/interfaces/s3"
                            "/bucket/path/dataset.csv/content"
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
