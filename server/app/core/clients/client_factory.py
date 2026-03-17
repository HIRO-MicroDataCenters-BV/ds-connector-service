# Client Factory
from typing import Any, Dict, Optional

import logging

from fastapi import HTTPException

from ..source_type import SourceType
from .base import BaseReadDataClient, BaseWriteDataClient

logger = logging.getLogger(__name__)


class ClientFactory:
    """Factory for creating and managing data clients"""

    def __init__(self):
        self._read_clients: Dict[SourceType, BaseReadDataClient] = {}
        self._write_clients: Dict[SourceType, BaseWriteDataClient] = {}
        self._default_client_type = SourceType.FILE
        logger.info("Initialized client factory")

    def register_read_client(
        self, source_type: SourceType, client: BaseReadDataClient
    ) -> None:
        """Register a read client for a specific source type"""
        self._read_clients[source_type] = client
        logger.info(f"Registered read client for source type: {source_type.value}")

    def register_write_client(
        self, source_type: SourceType, client: BaseWriteDataClient
    ) -> None:
        """Register a write client for a specific source type"""
        self._write_clients[source_type] = client
        logger.info(f"Registered write client for source type: {source_type.value}")

    def get_read_client(
        self, source_type: Optional[SourceType] = None
    ) -> BaseReadDataClient:
        """Get read client for source type"""
        client_type = source_type or self._default_client_type

        if client_type not in self._read_clients:
            logger.error(
                f"No read client registered for source type: {client_type.value}"
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    f"No read client registered for source type: "
                    f"{client_type.value}"
                ),
            )
        return self._read_clients[client_type]

    def get_write_client(
        self, source_type: Optional[SourceType] = None
    ) -> BaseWriteDataClient:
        """Get write client for source type"""
        client_type = source_type or self._default_client_type

        if client_type not in self._write_clients:
            logger.error(
                f"No write client registered for source type: {client_type.value}"
            )
            raise HTTPException(
                status_code=500,
                detail=(
                    f"No write client registered for source type: "
                    f"{client_type.value}"
                ),
            )
        return self._write_clients[client_type]

    def get_read_client_by_name(self, client_name: str) -> BaseReadDataClient:
        """Get read client by direct client name (e.g., 'rest', 's3', 'file')"""
        try:
            source_type = SourceType(client_name.lower())
            return self._read_clients[source_type]
        except (KeyError, ValueError):
            logger.error(f"No read client registered for: {client_name}")
            raise HTTPException(
                status_code=500, detail=f"No read client registered for: {client_name}"
            )

    def get_write_client_by_name(self, client_name: str) -> BaseWriteDataClient:
        """Get write client by direct client name (e.g., 'rest', 's3', 'file')"""
        try:
            source_type = SourceType(client_name.lower())
            return self._write_clients[source_type]
        except (KeyError, ValueError):
            logger.error(f"No write client registered for: {client_name}")
            raise HTTPException(
                status_code=500, detail=f"No write client registered for: {client_name}"
            )

    def list_registered_clients(self) -> Dict[str, Dict[str, Any]]:
        """List all registered clients with their health status"""
        clients_info = {}

        # List read clients
        for source_type, client in self._read_clients.items():
            try:
                clients_info[f"{source_type.value}_read"] = {
                    "client_type": getattr(client, "client_name", source_type.value),
                    "registered": True,
                    "operation_type": "read",
                }
            except Exception as e:
                clients_info[f"{source_type.value}_read"] = {
                    "registered": False,
                    "operation_type": "read",
                    "error": str(e),
                }

        # List write clients
        for source_type, write_client in self._write_clients.items():
            try:
                clients_info[f"{source_type.value}_write"] = {
                    "client_type": getattr(
                        write_client, "client_name", source_type.value
                    ),
                    "registered": True,
                    "operation_type": "write",
                }
            except Exception as e:
                clients_info[f"{source_type.value}_write"] = {
                    "registered": False,
                    "operation_type": "write",
                    "error": str(e),
                }

        return clients_info
