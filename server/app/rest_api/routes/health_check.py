from classy_fastapi import Routable, get
from fastapi import APIRouter

from app.tags import Tags

from ..serializers import HealthCheck


class HealthCheckRoutes(Routable):
    def __init__(self):
        super().__init__()

    @get(
        "/health-check",
        operation_id="service_health_check",
        summary="Health check",
        response_model=HealthCheck,
        tags=[Tags.Health],
    )
    async def health_check(self) -> dict[str, str]:
        """Returns a 200 status code if the service is up and running"""
        return {"status": "OK"}


router = APIRouter()
health_routes = HealthCheckRoutes()
router.include_router(health_routes.router)
