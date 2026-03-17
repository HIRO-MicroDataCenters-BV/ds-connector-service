"""Schemas for data connector and data product metadata."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    status: str = Field(examples=["OK"])


class UploadResponse(BaseModel):
    """Response model for upload operations"""

    message: str = Field(description="Upload status message")
    result: Optional[Dict[str, Any]] = Field(
        description="Upload result details", default=None
    )


class ConnectorMetadata(BaseModel):
    connector_id: str
    region: str
    supported_interfaces: List[str]
    status: str
    version: str


class DataProductDistribution(BaseModel):
    """Standardized metadata for resources across different sources"""

    access_service: Optional[str] = None
    access_url: Optional[str] = None
    byte_size: Optional[int] = None
    compress_format: Optional[str] = None
    download_url: Optional[str] = None
    media_type: Optional[str] = None
    package_format: Optional[str] = None
    access_rights: Optional[str] = None
    conforms_to: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    issued: Optional[str] = None
    license: Optional[str] = None
    modified: Optional[str] = None
    rights: Optional[str] = None
    title: Optional[str] = None
    has_policy: Optional[str] = None
    checksum: Optional[str] = None


class DataProductItem(BaseModel):
    distribution: List[DataProductDistribution]
    region: str = ""
