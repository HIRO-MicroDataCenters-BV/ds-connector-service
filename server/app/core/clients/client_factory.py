# Client Factory
from typing import Any, Dict, Optional

import logging

from fastapi import HTTPException

from ..source_type import SourceType
from .base import BaseReadDataClient

logger = logging.getLogger(__name__)


class ClientFactory:
    """Factory for creating and managing data clients"""

    def __init__(self):
        self._clients: Dict[SourceType, BaseReadDataClient] = {}
        self._default_client_type = SourceType.FILE
        logger.info("Initialized client factory")

    def register_client(
        self, source_type: SourceType, client: BaseReadDataClient
    ) -> None:
        """Register a client for a specific source type"""
        self._clients[source_type] = client
        logger.info(f"Registered client for source type: {source_type.value}")

    def get_client(
        self, source_type: Optional[SourceType] = None
    ) -> BaseReadDataClient:
        """Get client for source type"""
        client_type = source_type or self._default_client_type

        if client_type not in self._clients:
            logger.error(f"No client registered for source type: {client_type.value}")
            raise HTTPException(
                status_code=500,
                detail=f"No client registered for source type: {client_type.value}",
            )
        return self._clients[client_type]

    def get_client_by_name(self, client_name: str) -> BaseReadDataClient:
        """Get client by direct client name (e.g., 'rest', 's3', 'file')"""
        try:
            source_type = SourceType(client_name.lower())
            return self._clients[source_type]
        except (KeyError, ValueError):
            logger.error(f"No client registered for: {client_name}")
            raise HTTPException(
                status_code=500, detail=f"No client registered for: {client_name}"
            )

    def list_registered_clients(self) -> Dict[str, Dict[str, Any]]:
        """List all registered clients with their health status"""
        clients_info = {}
        for source_type, client in self._clients.items():
            try:
                # This would be async in real implementation
                clients_info[source_type.value] = {
                    "client_type": getattr(client, "client_name", source_type.value),
                    "registered": True,
                }
            except Exception as e:
                clients_info[source_type.value] = {"registered": False, "error": str(e)}

        return clients_info
