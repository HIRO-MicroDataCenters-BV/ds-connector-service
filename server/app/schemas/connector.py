"""Schemas for data connector and data product metadata."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ConnectorMetadata(BaseModel):
    connector_id: str
    region: str
    supported_interfaces: List[str]
    status: str
    version: str


class DataProductDistribution(BaseModel):
    title: str
    access_url: str
    media_type: str
    byte_size: int


class DataProduct(BaseModel):
    id: str
    type: str = Field(default="dataset")
    identifier: str
    title: str
    description: str
    publisher: Dict[
        str, Any
    ]  # e.g., {"type": "organization", "name": "ds-connector-service"}
    keyword: List[str] = []
    distribution: List[DataProductDistribution] = []
    region: str


class DataProductSummary(BaseModel):
    id: str
    name: str
    description: str
