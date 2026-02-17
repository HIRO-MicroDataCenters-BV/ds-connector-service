from app.core.clients.client_factory import ClientFactory
from app.core.clients.read.local_file_system_read import FileSystemDataClient
from app.core.clients.read.s3_read_client import S3DataClient
from app.core.clients.write.local_file_system_write import LocalFileSystemWriteClient
from app.core.clients.write.s3_write_client import S3WriteClient
from app.core.source_type import SourceType
from app.settings import get_settings

# Get settings instance
settings = get_settings()

# Initialize client factory
client_factory = ClientFactory()

# TODO: update the factory client to send the env to it like the other clients
# Register filesystem clients (always available)
client_factory.register_read_client(
    SourceType.FILE, FileSystemDataClient()  # Uses settings/env variables
)
client_factory.register_write_client(
    SourceType.FILE, LocalFileSystemWriteClient()  # Uses settings/env variables
)

# Register S3 client (if S3 configuration is available)
if settings.S3_BUCKET_NAME:
    # Configure S3 client with all environment variables
    s3_client = S3DataClient(
        bucket_name=settings.S3_BUCKET_NAME,
        prefix=settings.S3_PREFIX or "",
        access_key_id=settings.S3_ACCESS_KEY_ID,
        secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        session_token=settings.S3_SESSION_TOKEN,
        region_name=settings.S3_REGION,
        endpoint_url=settings.S3_ENDPOINT_URL,
        allowed_prefixes=None,  # No restrictions by default
    )

    client_factory.register_read_client(SourceType.S3, s3_client)

    # Register S3 write client with same configuration
    s3_write_client = S3WriteClient(
        bucket_name=settings.S3_BUCKET_NAME,
        prefix=settings.S3_PREFIX or "",
        access_key_id=settings.S3_ACCESS_KEY_ID,
        secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        session_token=settings.S3_SESSION_TOKEN,
        region_name=settings.S3_REGION,
        endpoint_url=settings.S3_ENDPOINT_URL,
        allowed_prefixes=None,  # No restrictions by default
    )

    client_factory.register_write_client(SourceType.S3, s3_write_client)
