# File System Write Client Implementation
from typing import Any, AsyncGenerator, Dict, List, Optional

import hashlib
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

import aiofiles
import aiofiles.ospath
from fastapi import HTTPException

from app.settings import get_settings

from ..base import BaseWriteDataClient

logger = logging.getLogger(__name__)

settings = get_settings()
CHUNK_SIZE = settings.CHUNK_SIZE
MAX_FILE_SIZE = settings.MAX_FILE_SIZE
FS_BASE_PATH = settings.FS_BASE_PATH


class LocalFileSystemWriteClient(BaseWriteDataClient):
    """Client for writing to local file system"""

    def __init__(
        self, base_path: Optional[str] = None, allowed_paths: Optional[List[str]] = None
    ):
        """
        Initialize file system write client

        Args:
            base_path: Base directory path for file operations
            allowed_paths: List of allowed directory paths for security
        """
        self.base_path = Path(
            FS_BASE_PATH if FS_BASE_PATH else base_path if base_path else "."
        ).resolve()
        self.client_name = "FileSystemWrite"
        self.allowed_paths = allowed_paths or []

        # Ensure base path exists
        if not self.base_path.exists():
            try:
                self.base_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create base path {self.base_path}: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to initialize write client: {e}"
                )

    def _resolve_path(self, resource_path: str) -> Path:
        """
        Resolve and validate the resource path

        Args:
            resource_path: Relative path to the resource

        Returns:
            Path: Absolute resolved path

        Raises:
            HTTPException: If path is invalid or not allowed
        """
        try:
            # Clean and normalize the path
            resource_path = resource_path.lstrip("/")
            full_path = (self.base_path / resource_path).resolve()

            # Security check: ensure path is within base_path
            if not str(full_path).startswith(str(self.base_path)):
                raise HTTPException(
                    status_code=403, detail=f"Path traversal detected: {resource_path}"
                )

            # Check allowed paths if configured
            if self.allowed_paths:
                path_allowed = any(
                    str(full_path).startswith(str(Path(allowed).resolve()))
                    for allowed in self.allowed_paths
                )
                if not path_allowed:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Path not in allowed directories: {resource_path}",
                    )

            return full_path

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Invalid path {resource_path}: {e}")
            raise HTTPException(
                status_code=400, detail=f"Invalid resource path: {resource_path}"
            )

    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate MD5 checksum of content"""
        return hashlib.md5(content).hexdigest()

    async def write_file_content(
        self,
        resource_path: str,
        content: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Write entire file content at once (atomic operation)

        Args:
            resource_path: Relative path where to write the resource
            content: Complete file content as bytes
            metadata: Optional metadata (permissions, timestamps, etc.)

        Returns:
            Dict containing write result information
        """
        full_path = self._resolve_path(resource_path)

        # Check file size limit
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size {len(content)} exceeds limit {MAX_FILE_SIZE}",
            )

        try:
            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first for atomic operation
            temp_path = None
            try:
                # Create temporary file in the same directory as target
                with tempfile.NamedTemporaryFile(
                    dir=full_path.parent, delete=False, suffix=".tmp"
                ) as temp_file:
                    temp_path = Path(temp_file.name)

                # Write content to temporary file
                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(content)

                # Apply metadata if provided
                if metadata:
                    await self._apply_metadata(temp_path, metadata)

                # Atomic move to final location
                temp_path.rename(full_path)
                temp_path = None  # Successfully moved, don't clean up

                checksum = self._calculate_checksum(content)

                logger.info(f"Successfully wrote {len(content)} bytes to {full_path}")

                return {
                    "path": str(full_path),
                    "size": len(content),
                    "checksum": checksum,
                    "timestamp": datetime.now().isoformat(),
                    "client": self.client_name,
                }

            finally:
                # Clean up temp file if operation failed
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception as cleanup_error:
                        logger.warning(
                            f"Failed to cleanup temp file {temp_path}: {cleanup_error}"
                        )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to write file {full_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")

    async def write_stream(
        self,
        resource_path: str,
        content_stream: AsyncGenerator[bytes, None],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Write file content from an async stream (memory-efficient)

        Args:
            resource_path: Relative path where to write the resource
            content_stream: Async generator yielding content chunks
            metadata: Optional metadata

        Returns:
            Dict containing write result information
        """
        full_path = self._resolve_path(resource_path)

        try:
            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first for atomic operation
            temp_path = None
            total_size = 0
            hasher = hashlib.md5()

            try:
                # Create temporary file in the same directory as target
                with tempfile.NamedTemporaryFile(
                    dir=full_path.parent, delete=False, suffix=".tmp"
                ) as temp_file:
                    temp_path = Path(temp_file.name)

                # Stream content to temporary file
                async with aiofiles.open(temp_path, "wb") as f:
                    async for chunk in content_stream:
                        if not chunk:
                            continue

                        total_size += len(chunk)

                        # Check size limit during streaming
                        if total_size > MAX_FILE_SIZE:
                            raise HTTPException(
                                status_code=413,
                                detail=f"Stream size exceeds limit {MAX_FILE_SIZE}",
                            )

                        hasher.update(chunk)
                        await f.write(chunk)

                # Apply metadata if provided
                if metadata:
                    await self._apply_metadata(temp_path, metadata)

                # Atomic move to final location
                temp_path.rename(full_path)
                temp_path = None  # Successfully moved, don't clean up

                checksum = hasher.hexdigest()

                logger.info(f"Successfully streamed {total_size} bytes to {full_path}")

                return {
                    "path": str(full_path),
                    "size": total_size,
                    "checksum": checksum,
                    "timestamp": datetime.now().isoformat(),
                    "client": self.client_name,
                }

            finally:
                # Clean up temp file if operation failed
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception as cleanup_error:
                        logger.warning(
                            f"Failed to cleanup temp file {temp_path}: {cleanup_error}"
                        )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to stream write file {full_path}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to stream write file: {e}"
            )

    async def _apply_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> None:
        """Apply metadata to a file (permissions, timestamps, etc.)"""
        try:
            if "permissions" in metadata:
                file_path.chmod(metadata["permissions"])

            if "mtime" in metadata:
                # Set modification time
                timestamp = metadata["mtime"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp).timestamp()
                os.utime(file_path, (timestamp, timestamp))

        except Exception as e:
            logger.warning(f"Failed to apply metadata to {file_path}: {e}")
            # Don't fail the entire operation for metadata issues

    async def health_check(self) -> Dict[str, Any]:
        """
        Check write client health and connectivity
        """
        try:
            # Check if base path exists and is writable
            if not self.base_path.exists():
                return {
                    "status": "unhealthy",
                    "client": self.client_name,
                    "error": f"Base path does not exist: {self.base_path}",
                    "timestamp": datetime.now().isoformat(),
                }

            if not os.access(self.base_path, os.W_OK):
                return {
                    "status": "unhealthy",
                    "client": self.client_name,
                    "error": f"Base path is not writable: {self.base_path}",
                    "timestamp": datetime.now().isoformat(),
                }

            # Try to create a test file
            test_path = self.base_path / ".health_check_write"
            try:
                async with aiofiles.open(test_path, "w") as f:
                    await f.write("health_check")

                # Clean up test file
                if test_path.exists():
                    test_path.unlink()

                return {
                    "status": "healthy",
                    "client": self.client_name,
                    "base_path": str(self.base_path),
                    "writable": True,
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as write_error:
                return {
                    "status": "unhealthy",
                    "client": self.client_name,
                    "error": f"Cannot write to base path: {write_error}",
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "client": self.client_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
