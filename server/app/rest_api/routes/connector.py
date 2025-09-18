import logging
import boto3
from classy_fastapi import Routable, get
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, status


from app.response import JSONLDResponse
from app.tags import Tags

logger = logging.getLogger(__name__)


class ConnectorRoutes(Routable):
    def __init__(self):
        super().__init__()



    @get(
        "/health-check/",
        operation_id="health_check",
        name="Health Check",
        tags=[Tags.Health],
    )
    async def health_check(self) -> JSONLDResponse:
        """Check if the Connector service is running"""
        return JSONLDResponse({"status": "healthy"}, status_code=status.HTTP_200_OK)

    @get(
        "/metrics",
        operation_id="get_metrics",
        name="Metrics",
        tags=[Tags.Monitoring],
    )
    async def get_metrics(self) -> str:
        """Return Prometheus metrics"""
        return "# Prometheus metrics placeholder"



    @get(
        "/metadata/connector",
        operation_id="get_connector_metadata",
        name="Get Connector Metadata",
        tags=[Tags.Data_products],
    )
    async def get_connector_metadata(self) -> JSONLDResponse:
        """Return connector metadata (region, supported interfaces, etc.)"""
        return JSONLDResponse(
            {
                "connector_id": "ds-connector-service",
                "region": "eu-central-1",
                "supported_interfaces": ["s3", "rest", "sql"],
                "status": "healthy",
                "version": "0.1.0",
            },
            status_code=status.HTTP_200_OK,
        )


    # --- helpers (replace with real impls) ---
    async def get_node_labels_from_k8s() -> list[str]:
        # Example: call Kubernetes API (CoreV1Api) to fetch node labels
        return ["ki", "hus", "uva"]  # mocked for now

    async def get_connector_name() -> str:
        # Example: call your own metadata endpoint or config
        return "ds-connector-service"  # mocked for now

    @get(
        "/metadata/dataproducts/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_metadata",
        name="Get Data Product Metadata",
        tags=[Tags.Data_products],
        responses={
            200: {
                "description": "Data product metadata",
                "content": {
                    "application/json": {
                        "example": {
                            "interface_id": "amsterdam-s3",
                            "resource": "datasets/images/cats.csv",
                            "location": "s3://datasets/images/cats.csv",
                            "size_bytes": 123456,
                            "mimetype": "application/csv",
                            "last_modified": "2025-09-16T12:00:00Z",
                            "dataproduct_name": "cats.csv",
                            "display_name": "empty",
                            "connector_name": "ds-connector-service",
                            "region": "amsterdam",
                            "node_labels": ["ki", "hus", "uva"],
                            "presigned_url": "https://s3.partner/datasets/images/cats.csv?X-Amz-Signature=abc123",
                        }
                    }
                },
            }
        },
    )

    async def get_data_product_metadata(self,interface_id: str, resource_path: str, resource_name: str
    ) -> JSONLDResponse:
        """Return metadata of a data product (size, mimetype, region, etc.)"""

        # get dynamic values
        node_labels = await self.get_node_labels_from_k8s()
        connector_name = await self.get_connector_name()


        response = {
            "interface_id": interface_id,
            "resource": f"{resource_path}/{resource_name}",
            "location": f"s3://{resource_path}/{resource_name}",
            "size_bytes": 123456,
            "mimetype": "application/csv",
            "last_modified": "2025-09-16T12:00:00Z",
            "dataproduct_name": resource_name,
            "display_name": "empty",
            "connector_name": connector_name,
            "region": "amsterdam",
            "node_labels": node_labels
        }

        return JSONLDResponse(response, status_code=status.HTTP_200_OK)

    async def get_s3_client(self):
        return boto3.client(
            "s3",
            aws_access_key_id="PARTNER_KEY",
            aws_secret_access_key="PARTNER_SECRET",
            region_name="eu-central-1",
        )

    @get(
        "/content/dataproducts/{interface_id}/{resource_path:path}/{resource_name}",
        operation_id="get_data_product_content",
        name="Get Data Product Content",
        tags=[Tags.Data_products],
        responses={200: {"description": "Raw content of the data product"}},
    )
    async def get_data_product_content(self,
        interface_id: str, resource_path: str, resource_name: str
    ):
        """Retrieve the whole content of a data product from S3 and stream it"""


        key = f"{resource_path}/{resource_name}"

        s3 = self.get_s3_client()
        obj = s3.get_object(Bucket=resource_path, Key=key)

        return StreamingResponse(
            obj["Body"].iter_chunks(),  # stream content instead of loading all in memory
            media_type=obj.get("ContentType", "application/octet-stream"),
            headers={
                "Content-Length": str(obj["ContentLength"]),
                "Content-Disposition": f'attachment; filename="{resource_name}"',
            },
            status_code=status.HTTP_200_OK,
        )



    @get(
        "/content/dataproducts/{interface_id}/{resource_path}/{resource_name}/chunk",
        operation_id="get_data_product_chunk",
        name="Get Data Product Chunk",
        tags=[Tags.Data_products],
        responses={200: {"description": "Partial content (chunk) of the data product"}},
    )
    async def get_data_product_chunk(
        self,
        interface_id: str,
        resource_path: str,  # bucket name
        resource_name: str,  # object key
        start: int,  # query param: start byte
        end: int,  # query param: end byte
    ):
        """Retrieve a chunk (byte range) of a data product from S3"""

        key = resource_name
        bucket = resource_path


        s3 = boto3.client(
            "s3",
            aws_access_key_id="PARTNER_KEY",
            aws_secret_access_key="PARTNER_SECRET",
            region_name="eu-central-1",
        )


        byte_range = f"bytes={start}-{end}"
        obj = s3.get_object(Bucket=bucket, Key=key, Range=byte_range)

        return StreamingResponse(
            obj["Body"].iter_chunks(),
            media_type=obj.get("ContentType", "application/octet-stream"),
            headers={
                "Content-Range": byte_range,
                "Content-Length": str(obj["ContentLength"]),
                "Content-Disposition": f'attachment; filename="{resource_name}"',
            },
            status_code=206,
        )


router = APIRouter()
connector_routes = ConnectorRoutes()
router.include_router(connector_routes.router)
