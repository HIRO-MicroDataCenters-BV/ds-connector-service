# S3 Client Implementation
from typing import Any, AsyncGenerator, Dict, List, Optional

import logging
import re
from urllib.parse import unquote

import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException

from app.settings import get_settings

from ....rest_api.serializers import DataProductDistribution
from ..base import BaseReadDataClient
from .content_types import CONTENT_TYPE_MAP

logger = logging.getLogger(__name__)

settings = get_settings()
CHUNK_SIZE = settings.CHUNK_SIZE
MAX_FILE_SIZE = settings.MAX_FILE_SIZE
MAX_FILES_TO_LIST = settings.MAX_FILES_TO_LIST


class S3DataClient(BaseReadDataClient):
    """Client for S3-compatible data sources (AWS S3, MinIO, etc.)"""

    def __init__(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        session_token: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        allowed_prefixes: Optional[List[str]] = None,
    ):
        """
        Initialize S3-compatible client (works with AWS S3, MinIO, etc.)

        Args:
            bucket_name: S3 bucket name (required)
            prefix: Base prefix for S3 objects (like base_path for filesystem)
            access_key_id: S3 access key ID (AWS Access Key ID for AWS S3)
            secret_access_key: S3 secret access key (AWS Secret Access Key for AWS S3)
            session_token: S3 session token (for temporary credentials)
            region_name: S3 region (AWS region for AWS S3)
            endpoint_url: S3 endpoint URL (required for MinIO and other
                         S3-compatible services)
            allowed_prefixes: List of allowed prefixes for security
        """
        # Bucket name is required as parameter (no environment fallback)
        self.bucket_name = bucket_name

        # Follow filesystem pattern: only prefix uses environment fallback
        self.prefix = (prefix if prefix else "").strip("/")

        self.client_name = "S3"

        # S3-compatible service credentials and config
        # Note: boto3 requires AWS-named parameters even for non-AWS S3 services
        self.s3_config = {
            "region_name": region_name,
        }

        if access_key_id:
            self.s3_config["aws_access_key_id"] = access_key_id  # boto3 parameter name
        if secret_access_key:
            self.s3_config[
                "aws_secret_access_key"
            ] = secret_access_key  # boto3 parameter name
        if session_token:
            self.s3_config["aws_session_token"] = session_token  # boto3 parameter name
        if endpoint_url:
            self.s3_config["endpoint_url"] = endpoint_url

        # Set up allowed prefixes for security
        # Simple approach: use parameter if provided, otherwise default to
        # empty list (no restrictions)
        if allowed_prefixes is not None:
            self.allowed_prefixes = [p.strip("/") for p in allowed_prefixes]
        else:
            # Default to empty list (no prefix restrictions)
            self.allowed_prefixes = []

        logger.info(
            f"Initialized S3 client with bucket: {self.bucket_name}, "
            f"prefix: {self.prefix}"
        )
        logger.info(f"Allowed prefixes: {self.allowed_prefixes}")

    def _resolve_s3_key(self, resource_path: str) -> str:
        """
        Resolve and validate S3 key from resource path

        Args:
            resource_path: Resource path
        Returns:
            str: Valid S3 object key
        Raises:
            HTTPException: If path is invalid or not allowed
        """
        # Clean the resource path
        clean_path = resource_path.strip("/")

        # Build S3 key: prefix/resource_path
        if self.prefix and clean_path:
            s3_key = f"{self.prefix}/{clean_path}"
        elif self.prefix:
            s3_key = self.prefix
        else:
            s3_key = clean_path

        # URL decode the key to handle encoded characters
        s3_key = unquote(s3_key)

        # Validate against allowed prefixes
        if self.allowed_prefixes:
            key_allowed = False
            for allowed_prefix in self.allowed_prefixes:
                if not allowed_prefix:  # Empty prefix means root access
                    key_allowed = True
                    break
                elif (
                    s3_key.startswith(allowed_prefix + "/") or s3_key == allowed_prefix
                ):
                    key_allowed = True
                    break

            if not key_allowed:
                logger.warning(f"Access denied to S3 key: {s3_key}")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: key outside allowed prefixes",
                )

        return s3_key

    def _parse_range_header(
        self, range_header: str
    ) -> Optional[tuple[int, Optional[int]]]:
        """
        Parse HTTP Range header into start/end bytes
        """
        if not range_header:
            return None

        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end_str = match.group(2)
            end = int(end_str) if end_str else None
            return (start, end)

        return None

    def _map_s3_error(self, error: ClientError) -> HTTPException:
        """Map S3 errors to appropriate HTTP exceptions"""
        error_code = error.response["Error"]["Code"]

        if error_code == "NoSuchKey":
            return HTTPException(status_code=404, detail="Resource not found")
        elif error_code == "NoSuchBucket":
            return HTTPException(status_code=404, detail="Bucket not found")
        elif error_code == "AccessDenied":
            return HTTPException(status_code=403, detail="Access denied")
        elif error_code == "InvalidRange":
            return HTTPException(status_code=416, detail="Range not satisfiable")
        else:
            logger.error(f"S3 error: {error_code} - {error}")
            return HTTPException(status_code=500, detail=f"S3 error: {error_code}")

    async def stream_content(
        self,
        resource_path: str,
        range_header: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Stream S3 object content with optional range support"""
        s3_key = self._resolve_s3_key(resource_path)

        logger.info(
            f"Streaming S3 object: s3://{self.bucket_name}/{s3_key} "
            f"with range: {range_header}"
        )

        try:
            session = aioboto3.Session()
            async with session.client("s3", **self.s3_config) as s3_client:
                # First, get object metadata to validate and get size
                try:
                    head_response = await s3_client.head_object(
                        Bucket=self.bucket_name, Key=s3_key
                    )
                    object_size = head_response["ContentLength"]

                    # Check file size limit
                    if object_size > MAX_FILE_SIZE:
                        raise HTTPException(status_code=413, detail="File too large")

                except ClientError as e:
                    raise self._map_s3_error(e)

                # Prepare get_object parameters
                get_params = {
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                }

                # Parse range if provided
                range_info = (
                    self._parse_range_header(range_header) if range_header else None
                )

                if range_info:
                    start_byte, end_byte = range_info

                    logger.info(
                        f"Object size: {object_size}, Range: {start_byte}-{end_byte}"
                    )

                    # Validate range
                    if start_byte >= object_size:
                        logger.error(
                            f"Range not satisfiable: {start_byte} >= {object_size}"
                        )
                        raise HTTPException(
                            status_code=416, detail="Range not satisfiable"
                        )

                    if end_byte is None:
                        end_byte = object_size - 1
                    else:
                        end_byte = min(end_byte, object_size - 1)

                    # Set Range parameter for S3
                    get_params["Range"] = f"bytes={start_byte}-{end_byte}"

                    # At this point end_byte is guaranteed to be an int
                    assert end_byte is not None
                    logger.info(
                        f"Streaming range: "
                        f"{end_byte - start_byte + 1} bytes "
                        f"from {start_byte} to {end_byte}"
                    )

                # Get object with streaming
                try:
                    response = await s3_client.get_object(**get_params)

                    total_bytes = 0
                    stream = response["Body"]

                    # Use iter_chunks for proper streaming with controlled chunk size
                    async for chunk in stream.iter_chunks(chunk_size=CHUNK_SIZE):
                        if chunk:
                            total_bytes += len(chunk)
                            yield chunk

                    logger.info(f"S3 streaming completed: {total_bytes} bytes")

                except ClientError as e:
                    raise self._map_s3_error(e)

        except NoCredentialsError:
            logger.error("S3 credentials not found")
            raise HTTPException(status_code=500, detail="S3 credentials not configured")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"S3 streaming error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")

    async def read_file_content(self, resource_path: str) -> bytes:
        """
        Read the entire S3 object content at once into memory

        Args:
            resource_path: Resource path for the S3 object

        Returns:
            bytes: Complete object content

        Raises:
            HTTPException: If object not found, too large, or access denied
        """
        s3_key = self._resolve_s3_key(resource_path)

        logger.info(f"Reading entire S3 object: s3://{self.bucket_name}/{s3_key}")

        try:
            session = aioboto3.Session()
            async with session.client("s3", **self.s3_config) as s3_client:
                # First, check object size
                try:
                    head_response = await s3_client.head_object(
                        Bucket=self.bucket_name, Key=s3_key
                    )
                    object_size = head_response["ContentLength"]

                    if object_size > MAX_FILE_SIZE:
                        raise HTTPException(status_code=413, detail="File too large")

                except ClientError as e:
                    raise self._map_s3_error(e)

                # Get entire object
                try:
                    response = await s3_client.get_object(
                        Bucket=self.bucket_name, Key=s3_key
                    )

                    # Read all content
                    content: bytes = await response["Body"].read()

                    logger.info(f"S3 object read completed: {len(content)} bytes")
                    return content

                except ClientError as e:
                    raise self._map_s3_error(e)

        except NoCredentialsError:
            logger.error("S3 credentials not found")
            raise HTTPException(status_code=500, detail="S3 credentials not configured")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"S3 read error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")

    async def get_distribution_metadata(
        self, resource_path: str
    ) -> DataProductDistribution:
        """Get S3 object metadata"""
        s3_key = self._resolve_s3_key(resource_path)

        logger.info(f"Getting metadata for S3 object: s3://{self.bucket_name}/{s3_key}")

        try:
            session = aioboto3.Session()
            async with session.client("s3", **self.s3_config) as s3_client:
                try:
                    response = await s3_client.head_object(
                        Bucket=self.bucket_name, Key=s3_key
                    )

                    # Extract metadata from S3 response
                    object_size = response["ContentLength"]
                    last_modified = response["LastModified"]
                    etag = response.get("ETag", "").strip('"')
                    content_type = response.get("ContentType", "")

                    # Determine content type if not set
                    if not content_type:
                        # Extract from key extension
                        key_parts = s3_key.split(".")
                        if len(key_parts) > 1:
                            suffix = f".{key_parts[-1].lower()}"
                            content_type = CONTENT_TYPE_MAP.get(
                                suffix, "application/octet-stream"
                            )
                        else:
                            content_type = "application/octet-stream"

                    # Extract object name for title
                    object_name = s3_key.split("/")[-1] if "/" in s3_key else s3_key

                    # Use ETag as checksum (it's MD5 for single-part uploads)
                    checksum = (
                        etag if etag and "-" not in etag else ""
                    )  # Multi-part uploads have "-" in ETag

                    # Extract format from key
                    format_ext = ""
                    if "." in object_name:
                        format_ext = object_name.split(".")[-1].lower()

                    metadata = DataProductDistribution(
                        title=object_name,
                        description=f"S3 object {object_name}",
                        access_url=f"s3://{resource_path}",
                        byte_size=object_size,
                        media_type=content_type,
                        checksum=checksum,
                        has_policy=None,
                        access_rights=None,
                        license=None,
                        format=format_ext,
                        issued=last_modified.isoformat() if last_modified else None,
                        modified=last_modified.isoformat() if last_modified else None,
                        download_url=None,
                        compress_format=None,
                        package_format=None,
                        conforms_to=None,
                        rights=None,
                    )

                    logger.info(
                        f"S3 metadata retrieved: {metadata.byte_size} bytes, "
                        f"{content_type}"
                    )
                    return metadata

                except ClientError as e:
                    raise self._map_s3_error(e)

        except NoCredentialsError:
            logger.error("S3 credentials not found")
            raise HTTPException(status_code=500, detail="S3 credentials not configured")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"S3 metadata error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")

    async def list_dataproduct_distributions(
        self, directory_resource_path: str
    ) -> List[DataProductDistribution]:
        """List data product distributions from S3 prefix structure"""
        s3_prefix = self._resolve_s3_key(directory_resource_path)
        if s3_prefix and not s3_prefix.endswith("/"):
            s3_prefix += "/"

        logger.info(
            f"Listing S3 objects with prefix: s3://{self.bucket_name}/{s3_prefix}"
        )

        try:
            session = aioboto3.Session()
            async with session.client("s3", **self.s3_config) as s3_client:
                products = []
                paginator = s3_client.get_paginator("list_objects_v2")

                try:
                    page_iterator = paginator.paginate(
                        Bucket=self.bucket_name,
                        Prefix=s3_prefix,
                        MaxKeys=MAX_FILES_TO_LIST,
                    )

                    object_count = 0
                    async for page in page_iterator:
                        if "Contents" in page:
                            for obj in page["Contents"]:
                                if object_count >= MAX_FILES_TO_LIST:
                                    break

                                s3_key = obj["Key"]

                                # Skip if it's just the directory prefix itself
                                if s3_key == s3_prefix.rstrip("/"):
                                    continue

                                # Extract relative path from prefix
                                relative_path = (
                                    s3_key[len(s3_prefix) :] if s3_prefix else s3_key
                                )
                                object_name = (
                                    relative_path.split("/")[-1]
                                    if "/" in relative_path
                                    else relative_path
                                )

                                # Skip empty object names
                                if not object_name:
                                    continue

                                # Determine content type
                                suffix = ""
                                content_type = "application/octet-stream"
                                if "." in object_name:
                                    suffix = f".{object_name.split('.')[-1].lower()}"
                                    content_type = CONTENT_TYPE_MAP.get(
                                        suffix, "application/octet-stream"
                                    )

                                # Create distribution object
                                product = DataProductDistribution(
                                    title=object_name,
                                    description=f"S3 object {object_name}",
                                    access_url=f"s3://{self.bucket_name}/{s3_key}",
                                    byte_size=obj["Size"],
                                    media_type=content_type,
                                    checksum=obj.get("ETag", "").strip('"'),
                                    has_policy=None,
                                    access_rights=None,
                                    license=None,
                                    format=suffix.lstrip("."),
                                    issued=obj["LastModified"].isoformat()
                                    if obj.get("LastModified")
                                    else None,
                                    modified=obj["LastModified"].isoformat()
                                    if obj.get("LastModified")
                                    else None,
                                    download_url=None,
                                    compress_format=None,
                                    package_format=None,
                                    conforms_to=None,
                                    rights=None,
                                )
                                products.append(product)
                                object_count += 1

                        if object_count >= MAX_FILES_TO_LIST:
                            break

                    logger.info(f"S3 data products retrieved: {len(products)} products")
                    return products

                except ClientError as e:
                    raise self._map_s3_error(e)

        except NoCredentialsError:
            logger.error("S3 credentials not found")
            raise HTTPException(status_code=500, detail="S3 credentials not configured")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"S3 list distributions error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")

    async def list_dataproducts(self) -> List[str]:
        """
        List only the first-level 'directories' (common prefixes) within the base prefix

        Returns:
            List[str]: List of subdirectory names (first level only) from base prefix

        Raises:
            HTTPException: If bucket is not accessible
        """
        # Use the configured prefix as base
        base_prefix = self.prefix
        if base_prefix and not base_prefix.endswith("/"):
            base_prefix += "/"

        logger.info(f"Listing S3 prefixes under: s3://{self.bucket_name}/{base_prefix}")

        try:
            session = aioboto3.Session()
            async with session.client("s3", **self.s3_config) as s3_client:
                try:
                    response = await s3_client.list_objects_v2(
                        Bucket=self.bucket_name,
                        Prefix=base_prefix,
                        Delimiter="/",  # This groups objects by 'directory'
                    )

                    subdirectories = []

                    # Get common prefixes (these are like subdirectories)
                    if "CommonPrefixes" in response:
                        for prefix_info in response["CommonPrefixes"]:
                            prefix = prefix_info["Prefix"]
                            # Remove base prefix and trailing slash to get dir name
                            dir_name = prefix[len(base_prefix) :].rstrip("/")
                            if dir_name:  # Skip empty names
                                subdirectories.append(dir_name)

                    # Sort for consistent output
                    subdirectories.sort()

                    logger.info(
                        f"Found {len(subdirectories)} subdirectories in S3 prefix"
                    )
                    return subdirectories

                except ClientError as e:
                    raise self._map_s3_error(e)

        except NoCredentialsError:
            logger.error("S3 credentials not found")
            raise HTTPException(status_code=500, detail="S3 credentials not configured")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"S3 list dataproducts error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """Check S3 accessibility"""
        try:
            session = aioboto3.Session()
            async with session.client("s3", **self.s3_config) as s3_client:
                # Test bucket access
                try:
                    await s3_client.head_bucket(Bucket=self.bucket_name)
                    bucket_accessible = True
                except ClientError:
                    bucket_accessible = False

                # Test prefix access by listing objects
                prefix_accessible = False
                if bucket_accessible:
                    try:
                        await s3_client.list_objects_v2(
                            Bucket=self.bucket_name, Prefix=self.prefix, MaxKeys=1
                        )
                        prefix_accessible = True
                    except ClientError:
                        prefix_accessible = False

                return {
                    "client_type": self.client_name,
                    "status": "healthy"
                    if bucket_accessible and prefix_accessible
                    else "unhealthy",
                    "bucket_name": self.bucket_name,
                    "prefix": self.prefix,
                    "bucket_accessible": bucket_accessible,
                    "prefix_accessible": prefix_accessible,
                    "allowed_prefixes": self.allowed_prefixes,
                    "region": self.s3_config.get("region_name"),
                }

        except NoCredentialsError:
            return {
                "client_type": self.client_name,
                "status": "unhealthy",
                "bucket_name": self.bucket_name,
                "error": "S3 credentials not configured",
            }
        except Exception as e:
            return {
                "client_type": self.client_name,
                "status": "unhealthy",
                "bucket_name": self.bucket_name,
                "error": str(e),
            }
