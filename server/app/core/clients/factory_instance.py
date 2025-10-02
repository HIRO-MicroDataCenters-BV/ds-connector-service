from app.core.clients.client_factory import ClientFactory
from app.core.source_type import SourceType
from app.core.clients.read.local_file_system_read import FileSystemDataClient

client_factory = ClientFactory()
client_factory.register_client(SourceType.FILE, FileSystemDataClient(base_path="./data"))
# Register other clients here as needed
