# S3 Write Client Implementation
from typing import Any, AsyncGenerator, Dict, List, Optional

import hashlib
import logging
from datetime import datetime
from io import BytesIO

import aioboto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException

from app.settings import get_settings

from ..base import BaseWriteDataClient

logger = logging.getLogger(__name__)

settings = get_settings()
CHUNK_SIZE = settings.CHUNK_SIZE
MAX_FILE_SIZE = settings.MAX_FILE_SIZE
MIN_PART_SIZE = 5 * 1024 * 1024  # 5MB minimum part size for S3 multipart upload


class S3WriteClient(BaseWriteDataClient):
    """Client for writing to S3-compatible storage (AWS S3, MinIO, etc.)"""

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
        Initialize S3-compatible write client (works with AWS S3, MinIO, etc.)

        Args:
            bucket_name: S3 bucket name (required)
            prefix: Base prefix for S3 objects (like base_path for filesystem)
            access_key_id: S3 access key ID
            secret_access_key: S3 secret access key
            session_token: S3 session token (for temporary credentials)
            region_name: S3 region
            endpoint_url: S3 endpoint URL (required for MinIO and other
                S3-compatible services)
            allowed_prefixes: List of allowed prefixes for security
        """
        self.bucket_name = bucket_name
        self.prefix = (prefix if prefix else "").strip("/")
        self.client_name = "S3Write"

        # S3 configuration for boto3
        self.s3_config = {
            "region_name": region_name,
        }

        if access_key_id:
            self.s3_config["aws_access_key_id"] = access_key_id
        if secret_access_key:
            self.s3_config["aws_secret_access_key"] = secret_access_key
        if session_token:
            self.s3_config["aws_session_token"] = session_token
        if endpoint_url:
            self.s3_config["endpoint_url"] = endpoint_url

        # Set up allowed prefixes for security
        if allowed_prefixes is not None:
            self.allowed_prefixes = [p.strip("/") for p in allowed_prefixes]
        else:
            self.allowed_prefixes = []

        logger.info(
            f"Initialized S3 write client with bucket: {self.bucket_name}, "
            f"prefix: {self.prefix}"
        )

    def _resolve_s3_key(self, resource_path: str) -> str:
        """
        Resolve and validate S3 key from resource path

        Args:
            resource_path: Resource path

        Returns:
            str: Full S3 key

        Raises:
            HTTPException: If path is invalid or not allowed
        """
        try:
            # Clean the resource path
            resource_path = resource_path.strip("/")

            # Combine prefix with resource path
            if self.prefix:
                s3_key = f"{self.prefix}/{resource_path}"
            else:
                s3_key = resource_path

            # Security check: validate against allowed prefixes
            if self.allowed_prefixes:
                key_allowed = any(
                    s3_key.startswith(allowed_prefix)
                    for allowed_prefix in self.allowed_prefixes
                )
                if not key_allowed:
                    raise HTTPException(
                        status_code=403,
                        detail=f"S3 key not in allowed prefixes: {s3_key}",
                    )

            return s3_key

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Invalid S3 key for {resource_path}: {e}")
            raise HTTPException(
                status_code=400, detail=f"Invalid resource path: {resource_path}"
            )

    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate MD5 checksum of content"""
        return hashlib.md5(content).hexdigest()

    def _apply_metadata(
        self, upload_params: Dict[str, Any], metadata: Dict[str, Any]
    ) -> None:
        """
        Apply metadata to S3 upload parameters

        Args:
            upload_params: The upload parameters dict to modify
            metadata: Metadata dictionary with content_type, cache_control, tags, etc.
        """
        # S3 metadata
        if "content_type" in metadata:
            upload_params["ContentType"] = metadata["content_type"]

        if "cache_control" in metadata:
            upload_params["CacheControl"] = metadata["cache_control"]

        # Custom metadata (must be prefixed with x-amz-meta-)
        s3_metadata: Dict[str, str] = {}
        for key, value in metadata.items():
            if key.startswith("meta_"):
                s3_metadata[key[5:]] = str(value)  # Remove 'meta_' prefix

        if s3_metadata:
            upload_params["Metadata"] = s3_metadata

        # S3 tags (if provided)
        if "tags" in metadata and metadata["tags"]:
            tag_string = "&".join([f"{k}={v}" for k, v in metadata["tags"].items()])
            upload_params["Tagging"] = tag_string

    async def write_file_content(
        self,
        resource_path: str,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Write entire file content to S3 at once

        Args:
            resource_path: S3 key path where to write the resource
            content: Complete file content as bytes
            metadata: Optional metadata (tags, content-type, etc.)

        Returns:
            Dict containing write result information
        """
        s3_key = self._resolve_s3_key(resource_path)

        # Check file size limit
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size {len(content)} exceeds limit {MAX_FILE_SIZE}",
            )

        try:
            session = aioboto3.Session()

            async with session.client("s3", **self.s3_config) as s3_client:
                # Prepare upload parameters
                upload_params = {
                    "Bucket": self.bucket_name,
                    "Key": s3_key,
                    "Body": content,
                }

                # Add metadata if provided
                if metadata:
                    self._apply_metadata(upload_params, metadata)

                # Upload the object
                await s3_client.put_object(**upload_params)

                checksum = self._calculate_checksum(content)

                logger.info(
                    f"Successfully uploaded {len(content)} bytes to "
                    f"s3://{self.bucket_name}/{s3_key}"
                )

                return {
                    "path": f"s3://{self.bucket_name}/{s3_key}",
                    "bucket": self.bucket_name,
                    "key": s3_key,
                    "size": len(content),
                    "checksum": checksum,
                    "timestamp": datetime.now().isoformat(),
                    "client": self.client_name,
                }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "NoSuchBucket":
                raise HTTPException(
                    status_code=404, detail=f"S3 bucket not found: {self.bucket_name}"
                )
            elif error_code == "AccessDenied":
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied to S3 bucket: {self.bucket_name}",
                )
            else:
                logger.error(f"S3 ClientError uploading {s3_key}: {e}")
                raise HTTPException(
                    status_code=500, detail=f"S3 upload failed: {error_code}"
                )

        except NoCredentialsError:
            raise HTTPException(
                status_code=401, detail="S3 credentials not found or invalid"
            )

        except Exception as e:
            logger.error(f"Failed to upload to S3 {s3_key}: {e}")
            raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    async def write_stream(
        self,
        resource_path: str,
        content_stream: AsyncGenerator[bytes, None],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Write file content from an async stream using multipart upload

        Args:
            resource_path: S3 key path where to write the resource
            content_stream: Async generator yielding content chunks
            metadata: Optional metadata

        Returns:
            Dict containing write result information
        """
        s3_key = self._resolve_s3_key(resource_path)

        try:
            session = aioboto3.Session()

            async with session.client("s3", **self.s3_config) as s3_client:
                # Prepare multipart upload parameters
                upload_params = {"Bucket": self.bucket_name, "Key": s3_key}

                # Add metadata if provided
                if metadata:
                    self._apply_metadata(upload_params, metadata)

                # Start multipart upload
                response = await s3_client.create_multipart_upload(**upload_params)
                upload_id = response["UploadId"]

                parts = []
                part_number = 1
                total_size = 0
                hasher = hashlib.md5()
                current_chunk = BytesIO()
                current_chunk_size = 0

                try:
                    async for chunk in content_stream:
                        if not chunk:
                            continue

                        total_size += len(chunk)

                        # Check size limit during streaming
                        if total_size > MAX_FILE_SIZE:
                            # Abort multipart upload
                            await s3_client.abort_multipart_upload(
                                Bucket=self.bucket_name, Key=s3_key, UploadId=upload_id
                            )
                            raise HTTPException(
                                status_code=413,
                                detail=f"Stream size exceeds limit {MAX_FILE_SIZE}",
                            )

                        hasher.update(chunk)
                        current_chunk.write(chunk)
                        current_chunk_size += len(chunk)

                        # Upload part when it reaches minimum size (5MB for S3)
                        # For smaller files, we'll upload all at once in final part
                        if current_chunk_size >= MIN_PART_SIZE:  # 5MB minimum
                            current_chunk.seek(0)
                            part_data = current_chunk.read()

                            part_response = await s3_client.upload_part(
                                Bucket=self.bucket_name,
                                Key=s3_key,
                                PartNumber=part_number,
                                UploadId=upload_id,
                                Body=part_data,
                            )

                            parts.append(
                                {
                                    "ETag": part_response["ETag"],
                                    "PartNumber": part_number,
                                }
                            )

                            part_number += 1
                            current_chunk = BytesIO()
                            current_chunk_size = 0

                    # Upload any remaining data as final part
                    if current_chunk_size > 0:
                        current_chunk.seek(0)
                        part_data = current_chunk.read()

                        part_response = await s3_client.upload_part(
                            Bucket=self.bucket_name,
                            Key=s3_key,
                            PartNumber=part_number,
                            UploadId=upload_id,
                            Body=part_data,
                        )

                        parts.append(
                            {"ETag": part_response["ETag"], "PartNumber": part_number}
                        )

                    # Complete multipart upload
                    if parts:
                        await s3_client.complete_multipart_upload(
                            Bucket=self.bucket_name,
                            Key=s3_key,
                            UploadId=upload_id,
                            MultipartUpload={"Parts": parts},
                        )
                    else:
                        # No parts uploaded, abort
                        await s3_client.abort_multipart_upload(
                            Bucket=self.bucket_name, Key=s3_key, UploadId=upload_id
                        )
                        raise HTTPException(
                            status_code=400, detail="No data received from stream"
                        )

                except Exception:
                    # Abort multipart upload on any error
                    try:
                        await s3_client.abort_multipart_upload(
                            Bucket=self.bucket_name, Key=s3_key, UploadId=upload_id
                        )
                    except Exception as abort_error:
                        logger.warning(
                            f"Failed to abort multipart upload: {abort_error}"
                        )
                    raise

                checksum = hasher.hexdigest()

                logger.info(
                    f"Successfully streamed {total_size} bytes to "
                    f"s3://{self.bucket_name}/{s3_key}"
                )

                return {
                    "path": f"s3://{self.bucket_name}/{s3_key}",
                    "bucket": self.bucket_name,
                    "key": s3_key,
                    "size": total_size,
                    "checksum": checksum,
                    "timestamp": datetime.now().isoformat(),
                    "client": self.client_name,
                    "parts_count": len(parts),
                }

        except HTTPException:
            raise
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"S3 ClientError streaming upload {s3_key}: {e}")
            raise HTTPException(
                status_code=500, detail=f"S3 stream upload failed: {error_code}"
            )
        except NoCredentialsError:
            raise HTTPException(
                status_code=401, detail="S3 credentials not found or invalid"
            )
        except Exception as e:
            logger.error(f"Failed to stream upload to S3 {s3_key}: {e}")
            raise HTTPException(
                status_code=500, detail=f"S3 stream upload failed: {str(e)}"
            )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check S3 write client health and connectivity
        """
        try:
            session = aioboto3.Session()

            async with session.client("s3", **self.s3_config) as s3_client:
                # Check if bucket exists and is accessible
                try:
                    await s3_client.head_bucket(Bucket=self.bucket_name)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    if error_code == "NoSuchBucket":
                        return {
                            "status": "unhealthy",
                            "client": self.client_name,
                            "error": f"S3 bucket does not exist: {self.bucket_name}",
                            "timestamp": datetime.now().isoformat(),
                        }
                    elif error_code in ["403", "AccessDenied"]:
                        return {
                            "status": "unhealthy",
                            "client": self.client_name,
                            "error": f"Access denied to S3 bucket: {self.bucket_name}",
                            "timestamp": datetime.now().isoformat(),
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "client": self.client_name,
                            "error": f"S3 bucket check failed: {error_code}",
                            "timestamp": datetime.now().isoformat(),
                        }

                # Try to perform a test write (and delete)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                test_key = (
                    f"{self.prefix}/health_check_write_{timestamp}"
                    if self.prefix
                    else f"health_check_write_{timestamp}"
                )
                test_content = b"health_check"

                try:
                    # Write test object
                    await s3_client.put_object(
                        Bucket=self.bucket_name, Key=test_key, Body=test_content
                    )

                    # Delete test object
                    await s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)

                    return {
                        "status": "healthy",
                        "client": self.client_name,
                        "bucket": self.bucket_name,
                        "prefix": self.prefix,
                        "writable": True,
                        "timestamp": datetime.now().isoformat(),
                    }

                except ClientError as write_error:
                    error_code = write_error.response.get("Error", {}).get(
                        "Code", "Unknown"
                    )
                    return {
                        "status": "unhealthy",
                        "client": self.client_name,
                        "error": f"Cannot write to S3 bucket: {error_code}",
                        "timestamp": datetime.now().isoformat(),
                    }

        except NoCredentialsError:
            return {
                "status": "unhealthy",
                "client": self.client_name,
                "error": "S3 credentials not found or invalid",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            return {
                "status": "unhealthy",
                "client": self.client_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
