from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from prometheus_fastapi_instrumentator import Instrumentator

from .rest_api.routes.connector import router as connector_router
from app.core.clients.factory_instance import client_factory
from app.core.source_type import SourceType

class CustomFastAPI(FastAPI):
    def openapi(self) -> Dict[str, Any]:
        if self.openapi_schema:
            return self.openapi_schema
        openapi_schema = get_openapi(
            title="Connector Service API",
            version="0.1.0",
            description=(
                "The Connector Service provides a unified"
                " API for accessing Data Products, "
                "validating Contracts, and logging Transactions in the NextGen node."
            ),
            contact={
                "name": "HIRO-MicroDataCenters",
                "email": "all-hiro@hiro-microdatacenters.nl",
            },
            license_info={
                "name": "MIT",
                "url": "https://github.com/HIRO-MicroDataCenters-BV/"
                "ds-connector-service/blob/main/LICENSE",
            },
            routes=self.routes,
        )
        self.openapi_schema = openapi_schema
        return self.openapi_schema


app = CustomFastAPI()

client_factory.list_registered_clients()  # Initialize and log registered clients

Instrumentator().instrument(app).expose(app)
app.include_router(connector_router)
