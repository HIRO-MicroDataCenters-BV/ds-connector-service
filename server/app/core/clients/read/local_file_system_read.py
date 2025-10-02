# File System Client Implementation
from typing import List
import logging
import os
import re
from pathlib import Path
from typing import Optional, AsyncGenerator, Dict, Any
from ..base import BaseReadDataClient
from fastapi import HTTPException  
from ....rest_api.serializers import DataProductDistribution
import hashlib
import aiofiles
import aiofiles.ospath
import asyncio
from datetime import datetime
from app.settings import get_settings
from .content_types import CONTENT_TYPE_MAP

logger = logging.getLogger(__name__)

settings = get_settings()
CHUNK_SIZE = settings.CHUNK_SIZE
MAX_FILE_SIZE = settings.MAX_FILE_SIZE
MAX_FILES_TO_LIST = settings.MAX_FILES_TO_LIST
FS_BASE_PATH = settings.FS_BASE_PATH

## TODO: use custome exceptions instead of HTTPException
class FileSystemDataClient(BaseReadDataClient):
    """Client for local file system data sources"""    
    def __init__(self, base_path: Optional[str] = None, allowed_paths: Optional[List[str]] = None):
        """
        Initialize file system client
        
        Args:
            base_path: Base directory path for file operations
            allowed_paths: List of allowed directory paths for security
        """
        self.base_path = Path(base_path or FS_BASE_PATH).resolve()
        self.client_name = "FileSystem"

            # Ensure base path exists
        if not self.base_path.exists():
            logger.error(f"Base path does not exist: {self.base_path}")
            raise FileNotFoundError(f"Base path does not exist: {self.base_path}")

        if allowed_paths:
            self.allowed_paths = [Path(path).resolve() for path in allowed_paths]
        else:
            # Default to base_path only
            self.allowed_paths = [self.base_path]

        logger.info(f"Initialized File System client with base_path: {self.base_path}")
        logger.info(f"Allowed paths: {[str(p) for p in self.allowed_paths]}")
    
    def _resolve_file_path(self, resource_path: str, resource_name: str) -> Path:
        """
        Resolve and validate file path from components
        
        Args:
            resource_path: Path to the resource
            resource_name: Name of the resource
        Returns:
            Path: Resolved file path
        Raises:
            HTTPException: If path is invalid or not allowed
        """
        # Build file path: base_path/resource_path/resource_name
        clean_path = resource_path.strip('/')
        if clean_path:
            file_path = self.base_path / clean_path / resource_name
        else:
            file_path = self.base_path / resource_name
        
        try:
            resolved_path = file_path.resolve()
        except (OSError, RuntimeError) as e:
            logger.error(f"Invalid file path resolution: {file_path} - {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid file path: {str(e)}")

        # In case of allowed paths: Ensure path is within allowed directories if we have allowed paths
        if self.allowed_paths:
            path_allowed = False
            for allowed_path in self.allowed_paths:
                try:
                    resolved_path.relative_to(allowed_path)
                    path_allowed = True
                    break
                except ValueError:
                    continue
            
            if not path_allowed:
                logger.warning(f"Access denied to path: {resolved_path}")
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied: path outside allowed directories"
                )
        
        return resolved_path
    
    def _parse_range_header(self, range_header: str) -> Optional[tuple[int, Optional[int]]]:
        """
        Parse HTTP Range header into start/end bytes
        
        Args:
            range_header: HTTP Range header value
            
        Returns:
            Tuple of (start_byte, end_byte) or None if invalid
        """
        if not range_header:
            return None
        
        match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if match:
            start = int(match.group(1))
            end_str = match.group(2)
            end = int(end_str) if end_str else None
            return (start, end)
        
        return None
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
 
    async def _collect_files_recursively(self, root_path: str, parent: str = "", max_files: int = 20) -> list[tuple[str, str]]:
        """Recursively collect files up to max_files limit"""
        files = []
        if await aiofiles.os.path.exists(root_path):
            async for entry in aiofiles.os.scandir(root_path):
                entry_rel_path = f"{parent}/{entry.name}" if parent else entry.name
                if entry.is_file():
                    files.append((entry_rel_path, entry.path))
                    if len(files) >= max_files:
                        return files
                elif entry.is_dir():
                    sub_files = await self._collect_files_recursively(entry.path, entry_rel_path, max_files - len(files))
                    files.extend(sub_files)
                    if len(files) >= max_files:
                        return files
        return files    
   
    async def stream_content(
        self, 
        interface_id: str,
        resource_path: str,
        resource_name: str,
        range_header: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """Stream file content with optional range support"""
        file_path = self._resolve_file_path(interface_id, resource_path, resource_name)
        
        logger.info(f"Streaming file: {file_path} with range: {range_header}")
        
        # Check if file exists and is readable
        if not await aiofiles.os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="Resource not found")
        
        if not await aiofiles.os.path.isfile(file_path):
            logger.error(f"Path is not a file: {file_path}")
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        try:
            # Check file size
            file_stat = await aiofiles.os.stat(file_path)
            if file_stat.st_size > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File too large")
            
            # Parse range if provided
            range_info = self._parse_range_header(range_header) if range_header else None
            
            async with aiofiles.open(file_path, 'rb') as file:
                total_bytes = 0
                
                if range_info:
                    start_byte, end_byte = range_info
                    file_size = file_stat.st_size
                    
                    logger.info(f"File size: {file_size}, Range: {start_byte}-{end_byte}")
                    
                    # Validate and adjust range
                    if start_byte >= file_size:
                        logger.error(f"Range not satisfiable: {start_byte} >= {file_size}")
                        raise HTTPException(
                            status_code=416, 
                            detail="Range not satisfiable"
                        )
                    
                    if end_byte is None:
                        end_byte = file_size - 1
                    else:
                        end_byte = min(end_byte, file_size - 1)
                    
                    # Seek to start position
                    await file.seek(start_byte)
                    
                    # Calculate bytes to read
                    bytes_to_read = end_byte - start_byte + 1
                    bytes_read = 0
                    
                    logger.info(f"Streaming range: {bytes_to_read} bytes from {start_byte}")
                    
                    # Stream the range
                    while bytes_read < bytes_to_read:
                        chunk_size = min(CHUNK_SIZE, bytes_to_read - bytes_read)
                        chunk = await file.read(chunk_size)
                        
                        if not chunk:
                            break
                        
                        bytes_read += len(chunk)
                        total_bytes += len(chunk)
                        yield chunk
                else:
                    # Stream entire file
                    logger.info("Streaming entire file")
                    while True:
                        chunk = await file.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        total_bytes += len(chunk)
                        yield chunk
                
                logger.info(f"File streaming completed: {total_bytes} bytes")
                        
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
            raise HTTPException(status_code=403, detail="Permission denied")
        except OSError as e:
            logger.error(f"File system error: {file_path} - {str(e)}")
            raise HTTPException(status_code=500, detail=f"File system error: {str(e)}")
    
    async def get_metadata(
        self, 
        resource_path: str,
        resource_name: str
    ) -> DataProductDistribution:
        """Get file metadata"""
        print("Getting metadata...")
        print("Resource path:", resource_path)
        print("Resource name:", resource_name)
        file_path = self._resolve_file_path(resource_path, resource_name)
        print("Resolved file path:", file_path)
        
        logger.info(f"Getting file metadata: {file_path}")
        
        try:
            ## Check if file exists and is readable
            if not await aiofiles.ospath.exists(file_path):
                raise HTTPException(status_code=404, detail="Resource not found")
            
            if not await aiofiles.ospath.isfile(file_path):
                raise HTTPException(status_code=400, detail="Path is not a file")
            
            # Get file stats
            loop = asyncio.get_event_loop()
            file_stat = await loop.run_in_executor(None, os.stat, file_path)
            
            # Determine content type based on extension
            suffix = file_path.suffix.lower()
            
            content_type = CONTENT_TYPE_MAP.get(suffix, 'application/octet-stream')
            logger.info(f"Determined content type: {content_type} for suffix: {suffix}")

            # Calculate checksum for small files (< 100MB)
            checksum = ""
            if file_stat.st_size < 100 * 1024 * 1024:  # 100MB
                loop = asyncio.get_event_loop()
                checksum = await loop.run_in_executor(None, self._calculate_file_checksum, file_path)
            
            metadata = DataProductDistribution(
                title=resource_name,
                description=f"File resource {resource_name}",
                access_url=str(file_path),
                byte_size=file_stat.st_size,
                media_type=content_type,
                checksum=checksum,
                has_policy=None,
                access_rights=None,
                license=None,
                format=suffix.lstrip('.'),
                issued=datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                modified=datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                download_url=None,
                compress_format=None,
                package_format=None,
                conforms_to=None,
                rights=None
            )
            
            logger.info(f"File metadata retrieved: {metadata.byte_size} bytes, {content_type}")
            return metadata
            
        except PermissionError:
            logger.error(f"Permission denied for metadata: {file_path}")
            raise HTTPException(status_code=403, detail="Permission denied")
        except OSError as e:
            logger.error(f"File system metadata error: {file_path} - {str(e)}")
            raise HTTPException(status_code=500, detail=f"File system error: {str(e)}")
    
    async def list_data_products(self, resource_path: str) -> List[DataProductDistribution]:
        """List data products from file system structure"""
        logger.info(f"Listing file system data products from: {resource_path}")
        try:
            products = []
            resource_files = await self._collect_files_recursively(resource_path, max_files=MAX_FILES_TO_LIST)
            for file_name, file_path in resource_files:
                file_stat = await aiofiles.os.stat(file_path)
                suffix = Path(file_path).suffix.lower()
                content_type = CONTENT_TYPE_MAP.get(suffix, 'application/octet-stream')
                checksum = ""
                product = DataProductDistribution(
                    title=file_name.split('/')[-1],
                    description=f"File resource {file_name}",
                    access_url=str(file_path),
                    byte_size=file_stat.st_size,
                    media_type=content_type,
                    checksum=checksum,
                    has_policy=None,
                    access_rights=None,
                    license=None,
                    format=suffix.lstrip('.'),
                    issued=datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    modified=datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    download_url=None,
                    compress_format=None,
                    package_format=None,
                    conforms_to=None,
                    rights=None
                )
                products.append(product)
            logger.info(f"File system data products retrieved: {len(products)} products")
            return products
        except Exception as e:
            logger.error(f"File system list data products error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"File system error: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check file system accessibility"""
        try:
            # Check if base path exists and is accessible
            exists = await aiofiles.os.path.exists(self.base_path)
            is_dir = await aiofiles.os.path.isdir(self.base_path) if exists else False
            
            # Try to create a test file
            test_file = self.base_path / ".connector_health_check"
            can_write = False
            try:
                async with aiofiles.open(test_file, 'w') as f:
                    await f.write("health_check")
                can_write = True
                await aiofiles.os.remove(test_file)
            except Exception:
                pass
            
            return {
                "client_type": self.client_name,
                "status": "healthy" if exists and is_dir and can_write else "unhealthy",
                "base_path": str(self.base_path),
                "exists": exists,
                "is_directory": is_dir,
                "can_write": can_write,
                "allowed_paths": [str(p) for p in self.allowed_paths]
            }
        except Exception as e:
            return {
                "client_type": self.client_name,
                "status": "unhealthy",
                "base_path": str(self.base_path),
                "error": str(e)
            }
