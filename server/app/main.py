from typing import Any, Dict

import functools

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.clients.factory_instance import client_factory
from app.logging_config import setup_logging

from .rest_api.routes.connector import router as connector_router
from .rest_api.routes.health_check import router as health_router


class CustomFastAPI(FastAPI):
    def openapi(self) -> Dict[str, Any]:
        if self.openapi_schema:
            return self.openapi_schema

        # Fix functools.partial objects missing __name__ attribute
        for route in self.routes:
            if hasattr(route, "endpoint") and isinstance(
                route.endpoint, functools.partial
            ):
                if not hasattr(route.endpoint, "__name__"):
                    # Set __name__ from the original function
                    if hasattr(route.endpoint.func, "__name__"):
                        setattr(
                            route.endpoint,
                            "__name__",
                            route.endpoint.func.__name__,
                        )
                    else:
                        setattr(route.endpoint, "__name__", "unknown_endpoint")

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


setup_logging()


app = CustomFastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client_factory.list_registered_clients()  # Initialize and log registered clients

Instrumentator().instrument(app).expose(app)
app.include_router(connector_router)
app.include_router(health_router)
