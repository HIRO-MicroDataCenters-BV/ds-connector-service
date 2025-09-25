"""Schemas for data connector and data product metadata."""

from typing import List, Optional

from pydantic import BaseModel


class ConnectorMetadata(BaseModel):
    connector_id: str
    region: str
    supported_interfaces: List[str]
    status: str
    version: str


class DataProductDistribution(BaseModel):
    title: str
    description: Optional[str]
    access_url: str
    download_url: Optional[str]
    media_type: str
    byte_size: Optional[int]
    format: Optional[str]
    license: Optional[str]
    access_rights: Optional[str]
    release_date: Optional[str]
    packaging_format: Optional[str]


class DataProductItem(BaseModel):
    distribution: List[DataProductDistribution]
    region: str
