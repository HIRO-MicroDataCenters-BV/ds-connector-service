# Data Connector Service - Clients and API Guide

This guide provides comprehensive documentation for the Data Connector Service, covering both read and write operations, client architecture, and API interactions.

## Table of Contents

1. [Service Overview](#service-overview)
2. [Architecture](#architecture)
3. [Read Clients](#read-clients)
4. [Write Clients](#write-clients)
5. [API Endpoints](#api-endpoints)
6. [Usage Examples](#usage-examples)
7. [Health Monitoring](#health-monitoring)

## Service Overview

The Data Connector Service provides a unified API for accessing and managing data products across different storage backends. It supports both read and write operations through a pluggable client architecture that can work with various storage systems.

### Key Features

- **Multi-Storage Support**: File system, S3-compatible storage
- **Unified API**: Consistent interface regardless of storage backend
- **Streaming Support**: Efficient handling of large files through streaming
- **Health Monitoring**: Built-in health checks for all storage interfaces
- **Metadata Management**: Rich metadata support with checksums and tags
- **Error Resilience**: Comprehensive error handling and recovery

## Architecture

The service follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    REST API Layer                           │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Read Routes    │    │      Write Routes               │ │
│  │                 │    │                                 │ │
│  │ • List Products │    │ • Upload Files                  │ │
│  │ • Get Content   │    │ • Stream Upload                 │ │
│  │ • Metadata      │    │ • Health Check                  │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   Use Case Layer                            │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │DataProductRead  │    │   DataProductWrite              │ │
│  │   UseCase       │    │      UseCase                    │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   Client Layer                              │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Read Clients   │    │     Write Clients               │ │
│  │                 │    │                                 │ │
│  │ • FileSystem    │    │ • FileSystem                    │ │
│  │ • S3            │    │ • S3                            │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                Storage Backends                             │
│           ┌───────────┐    ┌─────────────────┐              │
│           │   Local   │    │       S3        │              │
│           │Filesystem │    │   Compatible    │              │
│           └───────────┘    └─────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Read Clients

Read clients provide access to existing data products and their metadata.

### Supported Read Operations

- **List Data Products**: Enumerate available data products
- **Get Distribution Content**: Retrieve file content (streaming and non-streaming)
- **Get Metadata**: Retrieve file metadata including size, checksums, etc.
- **Health Checks**: Verify storage backend connectivity and permissions

### LocalFileSystemReadClient

Provides read access to files on the local filesystem.

**Configuration:**
```python
{
    "base_path": "/data/storage",
    "allowed_paths": ["/data/storage/products", "/data/storage/distributions"]
}
```

**Features:**
- Path validation and security controls
- Streaming support for large files
- Metadata extraction (size, modification time, checksums)

### S3ReadClient

Provides read access to files in S3-compatible storage.

**Configuration:**
```python
{
    "bucket_name": "data-products",
    "prefix": "distributions/",
    "access_key_id": "your-access-key",
    "secret_access_key": "your-secret-key",
    "endpoint_url": "https://s3.amazonaws.com",  # Optional for custom S3 endpoints
    "region": "us-east-1"
}
```

**Features:**
- S3 streaming support
- Presigned URL generation
- Cross-region support
- Custom S3-compatible endpoints

## Write Clients

Write clients enable uploading and managing data products.

### Supported Write Operations

- **Upload Files**: Store files with metadata
- **Stream Upload**: Memory-efficient upload of large files
- **Atomic Operations**: Ensure data consistency during uploads
- **Health Checks**: Verify write permissions and connectivity

### LocalFileSystemWriteClient

Provides write access to the local filesystem.

**Configuration:**
```python
{
    "base_path": "/data/storage",
    "allowed_paths": ["/data/storage/uploads"],
    "max_file_size": 1073741824  # 1GB
}
```

**Features:**
- Atomic writes with temporary files
- Directory creation
- File size limitations
- Path validation for security

**Example Usage:**
```python
from app.core.clients.write.filesystem_write_client import LocalFileSystemWriteClient

# Initialize client
client = LocalFileSystemWriteClient(
    base_path="/data/storage",
    allowed_paths=["/data/storage/uploads"]
)

# Write file content
result = await client.write_file_content(
    resource_path="products/dataset.json",
    content=b'{"data": "example"}',
    metadata={"content_type": "application/json"}
)

# Stream upload
async def data_generator():
    for chunk in large_data:
        yield chunk

result = await client.write_stream(
    resource_path="products/large_file.zip",
    content_stream=data_generator(),
    metadata={"content_type": "application/zip"}
)
```

### S3WriteClient

Provides write access to S3-compatible storage.

**Configuration:**
```python
{
    "bucket_name": "data-products", 
    "prefix": "uploads/",
    "access_key_id": "your-access-key",
    "secret_access_key": "your-secret-key",
    "endpoint_url": "https://s3.amazonaws.com",  # Optional
    "region": "us-east-1",
    "allowed_prefixes": ["uploads/", "temp/"],  # Optional path restrictions
    "max_file_size": 5368709120  # 5GB
}
```

**Features:**
- Multipart uploads for large files
- Automatic retry and error handling
- Metadata and tagging support
- Server-side encryption support

**Example Usage:**
```python
from app.core.clients.write.s3_write_client import S3WriteClient

# Initialize client
client = S3WriteClient(
    bucket_name="my-bucket",
    prefix="uploads/",
    access_key_id="key",
    secret_access_key="secret"
)

# Upload with metadata and tags
result = await client.write_file_content(
    resource_path="dataset.csv",
    content=csv_data,
    metadata={
        "content_type": "text/csv",
        "tags": {"project": "analytics", "version": "1.0"},
        "meta_original_filename": "raw_data.csv"
    }
)
```

## API Endpoints

### Read Endpoints

#### List Data Products
```http
GET /dataproducts/{interface_id}
```
Returns a list of available data products for the specified storage interface.

**Response:**
```json
{
    "dataproducts": [
        {
            "identifier": "product-1",
            "title": "Sales Dataset",
            "description": "Monthly sales data"
        }
    ]
}
```

#### Get Distribution Content  
```http
GET /distribution-content/{interface_id}/{resource_path}
```
Retrieves the content of a specific distribution. Supports range requests for streaming.

**Headers:**
- `Range: bytes=0-1024` (optional, for partial content)

#### Get Distribution Metadata
```http
GET /distribution-metadata/{interface_id}/{resource_path}
```
Returns metadata about a specific distribution.

**Response:**
```json
{
    "byteSize": 1024768,
    "format": "CSV",
    "checksum": "sha256:abc123...",
    "issued": "2026-02-18T10:00:00Z",
    "modified": "2026-02-18T10:30:00Z"
}
```

#### List Distribution Items
```http
GET /dataproduct-distributions/{interface_id}/{dataproduct_id}
```
Lists all distributions for a specific data product.

### Write Endpoints

#### Upload File
```http
POST /distribution-upload/{interface_id}/{resource_path}
```
Uploads a file using either multipart form data or direct JSON content.

**Multipart Upload:**
```bash
curl -X POST "http://localhost:8000/distribution-upload/s3/products/dataset.csv" \
  -F "file=@dataset.csv" \
  -F "tags=project=analytics,version=1.0"
```

**JSON Upload:**
```bash
curl -X POST "http://localhost:8000/distribution-upload/file/products/config.json" \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"setting\": \"value\"}", "metadata": {"tags": {"type": "config"}}}'
```

**Response:**
```json
{
    "message": "Data product uploaded successfully (file)",
    "result": {
        "resource_path": "products/dataset.csv",
        "message": "File uploaded successfully",
        "metadata": {
            "size": 1024,
            "checksum": "abc123...",
            "timestamp": "2026-02-18T10:30:00Z"
        }
    }
}
```

#### Stream Upload
```http
POST /distribution-stream-upload/{interface_id}/{resource_path}
```
Efficiently uploads large files using streaming. Supports both file streaming and JSON content streaming, optimized for memory usage with large datasets.

**File Stream Upload (Multipart):**
```bash
# Upload large file via streaming
curl -X POST "http://localhost:8000/distribution-stream-upload/s3/large/video.mp4" \
  -F "file=@large_video.mp4" \
  -F "content_type=video/mp4" \
  -F "tags=project=media,quality=4k"
```

**File Stream Upload (Binary Data):**
```bash
# Stream raw binary data
curl -X POST "http://localhost:8000/distribution-stream-upload/file/backups/database.dump" \
  -H "Content-Type: application/octet-stream" \
  -H "Transfer-Encoding: chunked" \
  --data-binary @large_database.dump
```

**JSON Content Streaming:**
```bash
# Stream large JSON datasets
curl -X POST "http://localhost:8000/distribution-stream-upload/s3/analytics/large_dataset.json" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "{\"records\": [{\"id\": 1, \"data\": \"...\"}, {\"id\": 2, \"data\": \"...\"}]}",
    "metadata": {
      "content_type": "application/json",
      "tags": {"source": "analytics", "size": "large", "format": "json"},
      "meta_record_count": "1000000",
      "meta_compression": "none"
    }
  }'
```

**Python Streaming Example:**
```python
import aiohttp
import asyncio

async def stream_large_file():
    url = "http://localhost:8000/distribution-stream-upload/s3/data/large_dataset.csv"
    
    # File streaming
    async with aiohttp.ClientSession() as session:
        with open("large_dataset.csv", "rb") as file:
            data = aiohttp.FormData()
            data.add_field('file', file, filename='large_dataset.csv', content_type='text/csv')
            data.add_field('tags', 'project=analysis,type=streaming')
            
            async with session.post(url, data=data) as response:
                result = await response.json()
                print(f"Stream upload result: {result}")

async def stream_json_content():
    url = "http://localhost:8000/distribution-stream-upload/s3/json/streaming_data.json"
    
    # JSON content streaming
    large_json_data = {
        "content": '{"data": [' + ','.join([f'{{"record": {i}}}' for i in range(10000)]) + ']}',
        "metadata": {
            "content_type": "application/json",
            "tags": {"type": "streaming", "records": "10000"},
            "meta_generated_at": "2026-02-18T10:30:00Z"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=large_json_data) as response:
            result = await response.json()
            print(f"JSON stream result: {result}")

# Run examples
asyncio.run(stream_large_file())
asyncio.run(stream_json_content())
```

**Response (same for both stream types):**
```json
{
    "message": "Data product stream uploaded successfully (file stream|direct content stream)",
    "result": {
        "resource_path": "large/video.mp4",
        "message": "Stream upload completed successfully",
        "metadata": {
            "size": 2147483648,
            "checksum": "sha256:def789...",
            "timestamp": "2026-02-18T10:30:00Z",
            "upload_type": "multipart_stream|direct_stream",
            "client": "S3WriteClient"
        }
    }
}
```

#### Health Check (Read)
```http
GET /interface-health/{interface_id}
```
Checks the health and accessibility of a read interface.

#### Health Check (Write)
```http
GET /interface-health-write/{interface_id}
```
Checks the health and write permissions of a write interface.

**Response:**
```json
{
    "status": "healthy",
    "interface_id": "s3",
    "readable": true,
    "writable": true,
    "details": "All systems operational",
    "last_check": "2026-02-18T10:30:00Z"
}
```

## Usage Examples

### Python Client Library

```python
import asyncio
from ds_connector_service import DataConnectorClient

async def main():
    # Initialize client
    client = DataConnectorClient("http://localhost:8000")
    
    # List data products
    products = await client.list_dataproducts("s3")
    print(f"Available products: {products}")
    
    # Download a file
    content = await client.get_distribution_content("s3", "products/dataset.csv")
    
    # Upload a file
    with open("new_dataset.csv", "rb") as f:
        result = await client.upload_file("s3", "products/new_dataset.csv", f.read())
        print(f"Upload result: {result}")

asyncio.run(main())
```

### cURL Examples

**List Products:**
```bash
curl "http://localhost:8000/dataproducts/s3"
```

**Download Content:**
```bash
curl "http://localhost:8000/distribution-content/s3/products/dataset.csv" \
  -o dataset.csv
```

**Upload File:**
```bash
curl -X POST "http://localhost:8000/distribution-upload/s3/products/new_file.json" \
  -F "file=@data.json" \
  -F "tags=project=demo,version=2.0"
```

**Check Health:**
```bash
curl "http://localhost:8000/interface-health/s3"
curl "http://localhost:8000/interface-health-write/s3"
```

### Streaming Large Files

For files larger than available memory, use streaming endpoints that support both file and JSON content streaming:

**File Stream Upload:**
```bash
# Stream large binary file
curl -X POST "http://localhost:8000/distribution-stream-upload/s3/large/dataset.zip" \
  -H "Transfer-Encoding: chunked" \
  --data-binary @large_dataset.zip

# Stream using multipart form
curl -X POST "http://localhost:8000/distribution-stream-upload/file/media/video.mp4" \
  -F "file=@large_video.mp4" \
  -F "tags=type=media,quality=hd"
```

**JSON Content Stream Upload:**
```bash
# Stream large JSON dataset
curl -X POST "http://localhost:8000/distribution-stream-upload/s3/analytics/events.json" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "{\"events\": [/* large array of events */]}",
    "metadata": {
      "content_type": "application/json", 
      "tags": {"source": "analytics", "type": "events"},
      "meta_event_count": "500000"
    }
  }'
```

**Python Streaming Examples:**
```python
# File streaming download
async with client.stream_distribution_content("s3", "large/dataset.zip") as stream:
    async for chunk in stream:
        process_chunk(chunk)

# Large file streaming upload
async def upload_large_file():
    with open("huge_dataset.csv", "rb") as file:
        result = await client.stream_upload("s3", "data/huge_dataset.csv", file)
        return result

# JSON streaming upload
async def upload_large_json():
    large_data = {"records": [{"id": i, "data": f"record_{i}"} for i in range(100000)]}
    json_content = json.dumps(large_data)
    
    result = await client.stream_upload_json("s3", "data/large_records.json", {
        "content": json_content,
        "metadata": {"tags": {"type": "records", "count": "100000"}}
    })
    return result
```

## Health Monitoring

### Health Check Endpoints

The service provides health check endpoints for monitoring:

- **Read Health**: `GET /interface-health/{interface_id}`
- **Write Health**: `GET /interface-health-write/{interface_id}`
- **Overall Health**: `GET /health`

### Health Check Response Format

```json
{
    "status": "healthy|degraded|unhealthy",
    "interface_id": "s3",
    "readable": true,
    "writable": true,
    "details": "Descriptive status message",
    "last_check": "2026-02-18T10:30:00Z",
    "response_time_ms": 150,
    "error": null
}
```

### Monitoring Integration

**Prometheus Metrics:**
```bash
curl "http://localhost:8000/metrics"
```

**Health Check Script:**
```bash
#!/bin/bash
# health_check.sh

for interface in file s3; do
    echo "Checking $interface..."
    
    # Check read health
    read_status=$(curl -s "http://localhost:8000/interface-health/$interface" | jq -r '.status')
    echo "Read status: $read_status"
    
    # Check write health  
    write_status=$(curl -s "http://localhost:8000/interface-health-write/$interface" | jq -r '.status')
    echo "Write status: $write_status"
    
    if [ "$read_status" != "healthy" ] || [ "$write_status" != "healthy" ]; then
        echo "WARNING: Interface $interface is not fully healthy"
    fi
done
```

## Security Considerations

- **Path Validation**: All clients validate resource paths to prevent directory traversal
- **Access Control**: Configurable allowed paths restrict access to authorized directories
- **Credential Management**: Use environment variables or secure vaults for storage credentials
- **HTTPS**: Always use HTTPS in production environments
- **File Size Limits**: Configure appropriate limits to prevent DoS attacks
- **Input Validation**: All inputs are validated and sanitized

## Performance Optimization

- **Streaming**: Use streaming endpoints for large files to reduce memory usage
- **Compression**: Enable compression for text-based data products
- **Caching**: Implement caching for frequently accessed metadata
- **Connection Pooling**: Configure appropriate connection pools for S3 clients
- **Multipart Uploads**: Large S3 uploads automatically use multipart upload for better performance

## Troubleshooting

### Common Issues

**"Interface not found" errors:**
- Check that the interface is registered in the client factory
- Verify configuration is properly loaded

**S3 connection timeouts:**
- Check network connectivity
- Verify credentials and permissions
- Consider adjusting timeout settings

**File permission errors:**
- Ensure the service has read/write permissions to configured paths
- Check that directories exist and are accessible

**Memory issues with large files:**
- Use streaming endpoints instead of regular upload/download
- Increase available memory or implement chunked processing

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger("app.core.clients").setLevel(logging.DEBUG)
```

Check interface status:
```bash
curl "http://localhost:8000/interface-health/YOUR_INTERFACE"
```

---

For additional support or questions, please refer to the main [README](./README.md) or contact the development team.
