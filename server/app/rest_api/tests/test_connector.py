"""Unit tests for connector API routes."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.core.usecases import DataProductReadUseCase
from app.main import app
from app.rest_api.routes.connector_read import get_read_usecases
from app.rest_api.serializers import DataProductDistribution


class TestConnectorRoutes:
    """Test connector API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def sample_distribution(self):
        """Sample distribution for testing."""
        return DataProductDistribution(
            title="phenotype_data.csv",
            description="Clinical phenotype data for disease study",
            access_url="/multimodal_disease_ABC_data/phenotype_data.csv",
            byte_size=2048,
            media_type="text/csv",
            format="csv",
        )

    @pytest.fixture
    def mock_usecases(self):
        """Create mock usecases."""
        return AsyncMock(spec=DataProductReadUseCase)

    @pytest.fixture(autouse=True)
    def setup_and_cleanup_dependencies(self):
        """Automatically clean up dependency overrides after each test."""
        yield
        # Cleanup after each test
        app.dependency_overrides.clear()

    def override_usecases_dependency(self, mock_usecases):
        """Helper method to override the get_read_usecases dependency."""
        app.dependency_overrides[get_read_usecases] = lambda interface_id: mock_usecases

    def test_get_connector_metadata_success(self, client):
        """Test getting connector metadata (no mocking needed for static data)."""
        # Make request
        response = client.get("/connector-metadata")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["connector_id"] == "ds-connector-service"
        assert "supported_interfaces" in response_data
        assert response_data["status"] == "healthy"

    def test_get_distribution_metadata_success(
        self, client, sample_distribution, mock_usecases
    ):
        """Test getting distribution metadata successfully."""
        # Setup mock
        mock_usecases.get_distribution_metadata.return_value = sample_distribution

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request
        response = client.get(
            "/distribution-metadata/interface1/"
            "multimodal_disease_ABC_data/phenotype_data.csv"
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["region"] == "ki"
        assert response_data["distribution"]["title"] == "phenotype_data.csv"
        assert response_data["distribution"]["media_type"] == "text/csv"

    def test_get_distribution_metadata_if_error_constructing_query(
        self, client, mock_usecases
    ):
        """Test error handling when constructing query fails."""
        error_message = "Invalid file path format"
        mock_usecases.get_distribution_metadata.side_effect = HTTPException(
            status_code=422, detail=error_message
        )

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request
        response = client.get("/distribution-metadata/interface1/invalid/path/file.txt")

        # Verify error is propagated
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json() == {"detail": error_message}

    def test_list_dataproduct_distributions_success(
        self, client, sample_distribution, mock_usecases
    ):
        """Test listing distributions successfully."""
        # Setup mock
        distributions = [sample_distribution]
        mock_usecases.list_dataproduct_distributions.return_value = distributions

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request
        response = client.get(
            "/dataproduct-distributions/interface1/multimodal_disease_ABC_data"
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "data_products" in response_data
        assert len(response_data["data_products"]) == 1

    def test_read_distribution_content_success(
        self, client, sample_distribution, mock_usecases
    ):
        """Test reading file content successfully."""
        # Setup mock
        file_content = b"patient_id,age,sex\nPT001,45,M\nPT002,32,F"
        mock_usecases.get_distribution_metadata.return_value = sample_distribution
        mock_usecases.read_dataproduct_distribution_content.return_value = file_content

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request
        response = client.get(
            "/distribution-content/interface1/"
            "multimodal_disease_ABC_data/phenotype_data.csv"
        )

        # Verify
        assert response.status_code == status.HTTP_200_OK
        assert response.content == file_content
        assert "text/csv" in response.headers["content-type"]
        assert (
            'filename="phenotype_data.csv"' in response.headers["content-disposition"]
        )

    def test_health_check_success(self, client, mock_usecases):
        """Test health check endpoint."""
        # Setup mock
        health_data = {
            "status": "healthy",
            "client_type": "FileSystem",
            "timestamp": "2023-10-09T13:30:00Z",
        }
        mock_usecases.health_check.return_value = health_data

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request
        response = client.get("/interface-health-read/interface1")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert response_data["client_type"] == "FileSystem"

    def test_health_check_unhealthy(self, client, mock_usecases):
        """Test health check when service is unhealthy."""
        # Setup mock
        health_data = {
            "status": "unhealthy",
            "client_type": "FileSystem",
            "error": "Base directory not accessible",
        }
        mock_usecases.health_check.return_value = health_data

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request
        response = client.get("/interface-health-read/interface1")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "unhealthy"
        assert "error" in response_data

    def test_list_dataproducts_success(self, client, mock_usecases):
        """Test listing data products successfully."""
        # Setup mock
        dataproducts = ["multimodal_disease_ABC_data", "multimodal_disease_XYZ_data"]
        mock_usecases.list_dataproducts.return_value = dataproducts

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request
        response = client.get("/dataproducts/interface1")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "dataproducts" in response_data
        assert len(response_data["dataproducts"]) == 2
        assert "multimodal_disease_ABC_data" in response_data["dataproducts"]
