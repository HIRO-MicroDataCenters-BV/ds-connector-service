from typing import Any, Dict, Optional

import logging

from classy_fastapi import Routable, get, post
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse

from app.core import usecases
from app.core.clients.base import BaseWriteDataClient
from app.core.clients.factory_instance import client_factory
from app.settings import get_settings
from app.tags import Tags

from ..serializers import HealthCheck, UploadResponse

logger = logging.getLogger(__name__)

settings = get_settings()
CHUNK_SIZE = settings.CHUNK_SIZE


def _prepare_metadata(
    file: UploadFile,
    content_type: Optional[str] = None,
    tags: Optional[str] = None,
    upload_source: str = "rest_api",
) -> Dict[str, Any]:
    """
    Helper function to prepare metadata for file uploads

    Args:
        file: UploadFile instance
        content_type: Optional content type override
        tags: Optional tags string in format "key=value,key2=value2"
        upload_source: Source identifier for the upload

    Returns:
        Metadata dictionary

    Raises:
        HTTPException: If tags format is invalid
    """
    metadata: Dict[str, Any] = {}

    # Set content type
    if content_type:
        metadata["content_type"] = content_type
    elif file.content_type:
        metadata["content_type"] = file.content_type

    # Parse tags if provided
    if tags:
        try:
            tag_dict = {}
            for tag_pair in tags.split(","):
                key, value = tag_pair.strip().split("=", 1)
                tag_dict[key.strip()] = value.strip()
            metadata["tags"] = tag_dict
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid tags format. Use: key=value,key2=value2",
            )

    # Add file metadata
    metadata["meta_original_filename"] = file.filename or "unknown"
    metadata["meta_upload_source"] = upload_source

    return metadata


def _prepare_json_metadata(
    request: Request, tags: Optional[str] = None, upload_source: str = "rest_api_json"
) -> Dict[str, Any]:
    """
    Helper function to prepare metadata for JSON uploads

    Args:
        request: FastAPI Request instance
        tags: Optional tags string in format "key=value,key2=value2"
        upload_source: Source identifier for the upload

    Returns:
        Metadata dictionary

    Raises:
        HTTPException: If tags format is invalid
    """
    metadata: Dict[str, Any] = {}

    # Set content type from request
    content_type = request.headers.get("content-type", "application/json")
    metadata["content_type"] = content_type

    # Parse tags if provided
    if tags:
        try:
            tag_dict = {}
            for tag_pair in tags.split(","):
                key, value = tag_pair.strip().split("=", 1)
                tag_dict[key.strip()] = value.strip()
            metadata["tags"] = tag_dict
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid tags format. Use: key=value,key2=value2",
            )

    # Add metadata for JSON uploads
    metadata["meta_original_filename"] = "json_payload"
    metadata["meta_upload_source"] = upload_source

    return metadata


async def _detect_content_type_and_extract(
    request: Request, file: Optional[UploadFile] = None
) -> tuple[bytes, str]:
    """
    Detect content type and extract content accordingly

    Args:
        request: FastAPI Request instance
        file: Optional UploadFile for multipart uploads (may be None for direct uploads)

    Returns:
        Tuple of (content_bytes, detected_content_type)
    """
    content_type = request.headers.get("content-type", "")

    # Check if this is a real file upload or no file (direct content)
    if content_type.startswith("multipart/form-data") and file and file.filename:
        # File upload
        content = await file.read()
        detected_type = "multipart"
    else:
        # Direct content upload (JSON, text, etc.) - no file provided
        content = await request.body()
        detected_type = "direct"

    return content, detected_type


def get_write_usecases(interface_id: str) -> usecases.DataProductWriteUseCase:
    """
    Get write use cases for the specified interface

    Args:
        interface_id: Interface identifier (s3, file, etc.)

    Returns:
        DataProductWriteUseCase instance

    Raises:
        HTTPException: If interface is not supported
    """
    # Use the same factory pattern as read clients
    client: BaseWriteDataClient = client_factory.get_write_client_by_name(interface_id)
    return usecases.DataProductWriteUseCase(client)


class ConnectorWriteRoutes(Routable):
    """Routes for data product write operations"""

    def __init__(self):
        super().__init__()

    @post(
        "/distribution-upload/{interface_id}/{resource_path:path}",
        operation_id="upload_dataproduct",
        name="Upload Data Product",
        tags=[Tags.Data_products],
        response_model=UploadResponse,
    )
    async def upload_dataproduct(
        self,
        request: Request,
        interface_id: str,
        resource_path: str,
        file: Optional[UploadFile] = File(
            None, description="File to upload (for multipart uploads)"
        ),
        content_type: Optional[str] = Form(
            None, description="Content type override (for multipart uploads)"
        ),
        tags: Optional[str] = Form(
            None, description="Comma-separated tags (key=value,key2=value2)"
        ),
        usecases: usecases.DataProductWriteUseCase = Depends(get_write_usecases),
    ) -> JSONResponse:
        """
        Upload a complete data product file or JSON data

        Supports two upload methods:
        1. Multipart file upload: Use form-data with file field
        2. Direct JSON/data upload: Send JSON/text directly in request body

        Args:
            request: FastAPI request object
            interface_id: Storage interface (file, s3)
            resource_path: Path where to store the data
            file: File to upload (for multipart uploads only)
            content_type: Optional content type override (for multipart uploads)
            tags: Optional tags in format "key=value,key2=value2"
            usecases: Write use case dependency

        Returns:
            Upload result information
        """
        logger.info(
            f"Uploading data product to interface: {interface_id}, "
            f"path: {resource_path}"
        )

        try:
            # Detect content type and extract content
            content, detected_type = await _detect_content_type_and_extract(
                request, file
            )

            if detected_type == "multipart" and file and file.filename:
                # File upload - use existing metadata preparation
                metadata = _prepare_metadata(file, content_type, tags, "rest_api")
            else:
                # Direct content upload (JSON, etc.)
                # For direct uploads, tags come from query parameters
                query_tags = request.query_params.get("tags")
                metadata = _prepare_json_metadata(
                    request, query_tags, "rest_api_direct"
                )

            # Upload the content (same for both types)
            result = await usecases.upload_data_product(
                resource_path=resource_path, content=content, metadata=metadata
            )

            logger.info(f"Successfully uploaded data product: {result}")

            upload_type = (
                "file" if detected_type == "multipart" else "direct json content"
            )
            return JSONResponse(
                content={
                    "message": f"Data product uploaded successfully ({upload_type})",
                    "result": result,
                },
                status_code=status.HTTP_201_CREATED,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload data product: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    @post(
        "/distribution-stream-upload/{interface_id}/{resource_path:path}",
        operation_id="stream_upload_dataproduct",
        name="Stream Upload Data Product",
        tags=[Tags.Data_products],
        response_model=UploadResponse,
    )
    async def stream_upload_dataproduct(
        self,
        request: Request,
        interface_id: str,
        resource_path: str,
        file: Optional[UploadFile] = File(
            None, description="File to stream upload (for multipart uploads)"
        ),
        content_type: Optional[str] = Form(
            None, description="Content type override (for multipart uploads)"
        ),
        tags: Optional[str] = Form(None, description="Comma-separated tags"),
        usecases: usecases.DataProductWriteUseCase = Depends(get_write_usecases),
    ) -> JSONResponse:
        """
        Upload a data product using streaming (memory-efficient for large files/data)

        Supports two streaming methods:
        1. Multipart file streaming: Stream file chunks
        2. Direct content streaming: Stream JSON/text data from request body

        Args:
            request: FastAPI request object
            interface_id: Storage interface (file, s3)
            resource_path: Path where to store the data
            file: File to stream upload (for multipart uploads only)
            content_type: Optional content type override (for multipart uploads)
            tags: Optional tags
            usecases: Write use case dependency

        Returns:
            Upload result information
        """
        logger.info(
            f"Streaming upload data product to interface: {interface_id}, "
            f"path: {resource_path}"
        )

        try:
            # Detect content type
            request_content_type = request.headers.get("content-type", "")

            if (
                request_content_type.startswith("multipart/form-data")
                and file
                and file.filename
            ):
                # File streaming upload
                metadata = _prepare_metadata(
                    file, content_type, tags, "rest_api_stream"
                )

                # Create async generator for file content
                async def content_stream():
                    while True:
                        chunk = await file.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        yield chunk

                upload_type = "file stream"

            else:
                # Direct content streaming
                query_tags = request.query_params.get("tags")
                metadata = _prepare_json_metadata(
                    request, query_tags, "rest_api_stream_direct"
                )

                # Create async generator for request body content
                async def content_stream():
                    async for chunk in request.stream():
                        if chunk:
                            yield chunk

                upload_type = "direct content stream"

            # Stream upload the content (same for both types)
            result = await usecases.stream_upload_data_product(
                resource_path=resource_path,
                content_stream=content_stream(),
                metadata=metadata,
            )

            logger.info(f"Successfully stream uploaded data product: {result}")

            return JSONResponse(
                content={
                    "message": (
                        f"Data product stream uploaded successfully " f"({upload_type})"
                    ),
                    "result": result,
                },
                status_code=status.HTTP_201_CREATED,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to stream upload data product: {e}")
            raise HTTPException(
                status_code=500, detail=f"Stream upload failed: {str(e)}"
            )

    @get(
        "/interface-health-write/{interface_id}",
        operation_id="health_check_write",
        name="Write Health Check",
        tags=[Tags.Health],
        response_model=HealthCheck,
    )
    async def health_check_write(
        self,
        interface_id: str,
        usecases: usecases.DataProductWriteUseCase = Depends(get_write_usecases),
    ) -> JSONResponse:
        """
        Perform health check on the write capabilities of the specified interface

        Args:
            interface_id: Storage interface to test
            usecases: Write use case dependency

        Returns:
            Health check result
        """
        logger.info(f"Performing write health check for interface: {interface_id}")

        try:
            health = await usecases.health_check()

            if health.get("status") == "healthy":
                return JSONResponse(content=health, status_code=status.HTTP_200_OK)
            else:
                return JSONResponse(
                    content=health, status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        except Exception as e:
            logger.error(f"Write health check failed for {interface_id}: {e}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "interface": interface_id,
                    "error": str(e),
                    "timestamp": health.get("timestamp")
                    if "health" in locals()
                    else None,
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


# Create the router
write_router = APIRouter()
connector_write_routes = ConnectorWriteRoutes()
write_router.include_router(connector_write_routes.router)
