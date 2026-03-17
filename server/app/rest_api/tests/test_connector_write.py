"""Unit tests for connector write API routes."""

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.core.usecases import DataProductWriteUseCase
from app.main import app
from app.rest_api.routes.connector_write import get_write_usecases


class TestConnectorWriteRoutes:
    """Test connector write API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def sample_upload_response(self):
        """Sample upload response for testing."""
        return {
            "message": "File uploaded successfully",
            "resource_path": "test_data/sample_file.txt",
            "metadata": {
                "size": 1024,
                "client": "FileSystemWrite",
                "checksum": "abc123def456",
                "timestamp": "2026-02-17T10:30:00Z",
            },
        }

    @pytest.fixture
    def mock_usecases(self):
        """Create mock write usecases."""
        return AsyncMock(spec=DataProductWriteUseCase)

    @pytest.fixture(autouse=True)
    def setup_and_cleanup_dependencies(self):
        """Automatically clean up dependency overrides after each test."""
        yield
        # Cleanup after each test
        app.dependency_overrides.clear()

    def override_usecases_dependency(self, mock_usecases):
        """Helper method to override the get_write_usecases dependency."""
        app.dependency_overrides[
            get_write_usecases
        ] = lambda interface_id: mock_usecases

    def test_distribution_upload_success_with_file(
        self, client, sample_upload_response, mock_usecases
    ):
        """Test successful file upload via multipart form."""
        # Setup mock
        mock_usecases.upload_data_product.return_value = sample_upload_response

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Prepare test file
        test_content = b"This is test file content"
        files = {"file": ("test.txt", test_content, "text/plain")}

        # Make request
        response = client.post(
            "/distribution-upload/interface1/test_data/uploaded_file.txt", files=files
        )

        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert "Data product uploaded successfully" in response_data["message"]
        assert "result" in response_data
        assert response_data["result"]["resource_path"] == "test_data/sample_file.txt"

        # Verify use case was called correctly
        mock_usecases.upload_data_product.assert_called_once()

    def test_distribution_upload_success_with_json_content(
        self, client, sample_upload_response, mock_usecases
    ):
        """Test successful upload via JSON content."""
        # Setup mock
        mock_usecases.upload_data_product.return_value = sample_upload_response

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Prepare JSON payload
        json_payload = {
            "content": "This is JSON content data",
            "metadata": {
                "content_type": "text/plain",
                "tags": {"source": "api", "type": "test"},
            },
        }

        # Make request
        response = client.post(
            "/distribution-upload/interface1/test_data/json_file.txt",
            json=json_payload,
            headers={"Content-Type": "application/json"},
        )

        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert "Data product uploaded successfully" in response_data["message"]

    def test_distribution_stream_upload_success_with_file(
        self, client, sample_upload_response, mock_usecases
    ):
        """Test successful streaming upload via multipart form."""
        # Setup mock
        mock_usecases.stream_upload_data_product.return_value = sample_upload_response

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Prepare test file
        test_content = (
            b"This is streaming test content" * 1000
        )  # Larger content for streaming
        files = {"file": ("large_test.txt", test_content, "text/plain")}

        # Make request
        response = client.post(
            "/distribution-stream-upload/interface1/test_data/streamed_file.txt",
            files=files,
        )

        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert "Data product stream uploaded successfully" in response_data["message"]

        # Verify use case was called correctly
        mock_usecases.stream_upload_data_product.assert_called_once()

    def test_distribution_stream_upload_success_with_json_content(
        self, client, sample_upload_response, mock_usecases
    ):
        """Test successful streaming upload via JSON content."""
        # Setup mock
        mock_usecases.stream_upload_data_product.return_value = sample_upload_response

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Prepare JSON payload with large content
        large_content = "This is large JSON content " * 1000
        json_payload = {
            "content": large_content,
            "metadata": {
                "content_type": "text/plain",
                "tags": {"source": "api", "type": "stream"},
            },
        }

        # Make request
        response = client.post(
            "/distribution-stream-upload/interface1/test_data/json_stream.txt",
            json=json_payload,
            headers={"Content-Type": "application/json"},
        )

        # Verify
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert "Data product stream uploaded successfully" in response_data["message"]

    def test_distribution_upload_invalid_interface(self, client):
        """Test upload with invalid interface ID."""
        test_content = b"Test content"
        files = {"file": ("test.txt", test_content, "text/plain")}

        # Make request with invalid interface
        response = client.post(
            "/distribution-upload/invalid_interface/test.txt", files=files
        )

        # Should return 404 or similar error depending on implementation
        assert response.status_code >= 400

    def test_distribution_upload_error_handling(self, client, mock_usecases):
        """Test error handling during upload."""
        # Setup mock to raise exception
        mock_usecases.upload_data_product.side_effect = HTTPException(
            status_code=413, detail="File too large"
        )

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Prepare test file
        test_content = b"Large file content"
        files = {"file": ("large_file.txt", test_content, "text/plain")}

        # Make request
        response = client.post(
            "/distribution-upload/interface1/test_data/large_file.txt", files=files
        )

        # Verify error response
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        response_data = response.json()
        assert response_data["detail"] == "File too large"

    def test_distribution_upload_missing_content(self, client, mock_usecases):
        """Test upload with missing file and JSON content."""
        # For missing content, this should be caught before the use case is called
        # But for completeness, ensure mock has proper return value
        mock_usecases.upload_data_product.return_value = {
            "message": "Empty content uploaded",
            "resource_path": "test_data/missing_content.txt",
        }

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request without file or JSON content
        response = client.post(
            "/distribution-upload/interface1/test_data/missing_content.txt"
        )

        # Should return 201 - API handles empty content gracefully
        assert response.status_code == status.HTTP_201_CREATED

    def test_distribution_upload_unsupported_content_type(self, client, mock_usecases):
        """Test upload with unsupported content type."""
        # Configure mock return value
        mock_usecases.upload_data_product.return_value = {
            "message": "File uploaded with unsupported type",
            "resource_path": "test_data/test.txt",
        }

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request with unsupported content type
        response = client.post(
            "/distribution-upload/interface1/test_data/test.txt",
            data="raw text data",
            headers={"Content-Type": "text/xml"},  # Unsupported type
        )

        # Should return 201 - API handles unsupported content type gracefully
        assert response.status_code == status.HTTP_201_CREATED

    def test_health_check_write_success(self, client, mock_usecases):
        """Test write health check endpoint success."""
        # Setup mock
        health_data = {
            "status": "healthy",
            "details": "Write services operational",
            "writable": True,
        }
        mock_usecases.health_check.return_value = health_data

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request (assuming health endpoint exists for write services)
        response = client.get("/interface-health-write/interface1")

        # Verify
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert response_data["writable"] is True

    def test_health_check_write_unhealthy(self, client, mock_usecases):
        """Test write health check when write services are unavailable."""
        # Setup mock
        health_data = {
            "status": "unhealthy",
            "error": "Write permissions denied",
            "writable": False,
        }
        mock_usecases.health_check.return_value = health_data

        # Override the dependency
        self.override_usecases_dependency(mock_usecases)

        # Make request
        response = client.get("/interface-health-write/interface1")

        # Verify
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        response_data = response.json()
        assert response_data["status"] == "unhealthy"
        assert response_data["writable"] is False
        assert "error" in response_data
