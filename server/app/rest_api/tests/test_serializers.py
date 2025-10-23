"""Unit tests for serializers and data models."""

import pytest
from pydantic import ValidationError

from app.rest_api.serializers import (
    ConnectorMetadata,
    DataProductDistribution,
    DataProductItem,
)


class TestConnectorMetadata:
    """Test cases for ConnectorMetadata model."""

    def test_connector_metadata_creation_valid(self):
        """Test creating ConnectorMetadata with valid data."""
        data = {
            "connector_id": "fs-connector-001",
            "region": "us-east-1",
            "supported_interfaces": ["REST", "GraphQL"],
            "status": "active",
            "version": "1.0.0",
        }

        metadata = ConnectorMetadata(**data)  # type: ignore[arg-type]

        assert metadata.connector_id == "fs-connector-001"
        assert metadata.region == "us-east-1"
        assert metadata.supported_interfaces == ["REST", "GraphQL"]
        assert metadata.status == "active"
        assert metadata.version == "1.0.0"

    def test_connector_metadata_to_dict(self):
        """Test converting ConnectorMetadata to dictionary."""
        metadata = ConnectorMetadata(
            connector_id="test-connector",
            region="eu-west-1",
            supported_interfaces=["REST"],
            status="active",
            version="2.0.0",
        )

        result = metadata.dict()

        expected = {
            "connector_id": "test-connector",
            "region": "eu-west-1",
            "supported_interfaces": ["REST"],
            "status": "active",
            "version": "2.0.0",
        }
        assert result == expected

    def test_connector_metadata_json_serialization(self):
        """Test JSON serialization of ConnectorMetadata."""
        metadata = ConnectorMetadata(
            connector_id="json-test",
            region="asia-pacific",
            supported_interfaces=["REST", "SOAP"],
            status="maintenance",
            version="1.5.0",
        )

        json_str = metadata.json()
        assert "json-test" in json_str
        assert "asia-pacific" in json_str
        assert "maintenance" in json_str

    def test_connector_metadata_missing_required_field(self):
        """Test ConnectorMetadata creation with missing required fields."""
        with pytest.raises(ValidationError):
            ConnectorMetadata(  # type: ignore[call-arg]
                region="us-west-1",
                supported_interfaces=["REST"],
                status="active",
                # Missing connector_id and version
            )


class TestDataProductDistribution:
    """Test cases for DataProductDistribution model."""

    def test_distribution_creation_minimal(self):
        """Test creating DataProductDistribution with minimal data."""
        distribution = DataProductDistribution()

        # All fields should be None by default
        assert distribution.access_service is None
        assert distribution.access_url is None
        assert distribution.byte_size is None
        assert distribution.title is None

    def test_distribution_creation_full(self):
        """Test creating DataProductDistribution with all fields."""
        data = {
            "access_service": "FileService",
            "access_url": "/data/test.txt",
            "byte_size": 1024,
            "compress_format": "gzip",
            "download_url": "https://example.com/download",
            "media_type": "text/plain",
            "package_format": "tar",
            "access_rights": "public",
            "conforms_to": "CSV-RFC4180",
            "description": "Test data file",
            "format": "txt",
            "issued": "2023-01-01T00:00:00Z",
            "license": "MIT",
            "modified": "2023-01-02T00:00:00Z",
            "rights": "Copyright 2023",
            "title": "test.txt",
            "has_policy": "privacy-policy",
            "checksum": "abc123def456",
        }

        distribution = DataProductDistribution(**data)  # type: ignore[arg-type]

        assert distribution.access_service == "FileService"
        assert distribution.byte_size == 1024
        assert distribution.title == "test.txt"
        assert distribution.checksum == "abc123def456"

    def test_distribution_byte_size_validation(self):
        """Test byte_size field validation."""
        # Valid byte size
        distribution = DataProductDistribution(byte_size=1024)
        assert distribution.byte_size == 1024

        # Zero byte size (should be valid)
        distribution = DataProductDistribution(byte_size=0)
        assert distribution.byte_size == 0

    def test_distribution_optional_fields(self):
        """Test that all fields are optional."""
        distribution = DataProductDistribution(title="test", byte_size=100)

        # Most fields should be None
        assert distribution.title == "test"
        assert distribution.byte_size == 100
        assert distribution.access_service is None
        assert distribution.checksum is None

    def test_distribution_to_dict(self):
        """Test converting DataProductDistribution to dictionary."""
        distribution = DataProductDistribution(
            title="test.csv", byte_size=2048, media_type="text/csv", format="csv"
        )

        result = distribution.dict()

        assert result["title"] == "test.csv"
        assert result["byte_size"] == 2048
        assert result["media_type"] == "text/csv"
        assert result["format"] == "csv"
        # None values should also be included
        assert "access_service" in result
        assert result["access_service"] is None

    def test_distribution_json_serialization(self):
        """Test JSON serialization of DataProductDistribution."""
        distribution = DataProductDistribution(
            title="data.json", media_type="application/json", byte_size=512
        )

        json_str = distribution.json()
        assert "data.json" in json_str
        assert "application/json" in json_str
        assert "512" in json_str

    def test_distribution_exclude_none_serialization(self):
        """Test serialization excluding None values."""
        distribution = DataProductDistribution(title="test.txt", byte_size=1024)

        # Serialize excluding None values
        result = distribution.dict(exclude_none=True)

        assert "title" in result
        assert "byte_size" in result
        assert "access_service" not in result
        assert "checksum" not in result

    def test_distribution_update_values(self):
        """Test updating distribution values."""
        distribution = DataProductDistribution(title="original.txt")

        # Create new distribution with updated values
        updated_data = distribution.dict()
        updated_data.update({"title": "updated.txt", "byte_size": 2048})

        updated_distribution = DataProductDistribution(**updated_data)

        assert updated_distribution.title == "updated.txt"
        assert updated_distribution.byte_size == 2048


class TestDataProductItem:
    """Test cases for DataProductItem model."""

    def test_data_product_item_creation(self):
        """Test creating DataProductItem."""
        distributions = [
            DataProductDistribution(title="file1.txt", byte_size=100),
            DataProductDistribution(title="file2.csv", byte_size=200),
        ]

        item = DataProductItem(distribution=distributions, region="us-east-1")

        assert len(item.distribution) == 2
        assert item.region == "us-east-1"
        assert item.distribution[0].title == "file1.txt"
        assert item.distribution[1].title == "file2.csv"

    def test_data_product_item_default_region(self):
        """Test DataProductItem with default region."""
        distributions = [DataProductDistribution(title="test.txt")]

        item = DataProductItem(distribution=distributions)

        assert item.region == ""  # Default empty string
        assert len(item.distribution) == 1

    def test_data_product_item_empty_distributions(self):
        """Test DataProductItem with empty distributions list."""
        item = DataProductItem(distribution=[], region="test-region")

        assert len(item.distribution) == 0
        assert item.region == "test-region"

    def test_data_product_item_to_dict(self):
        """Test converting DataProductItem to dictionary."""
        distributions = [DataProductDistribution(title="test.txt", byte_size=512)]

        item = DataProductItem(distribution=distributions, region="eu-central-1")

        result = item.dict()

        assert "distribution" in result
        assert "region" in result
        assert result["region"] == "eu-central-1"
        assert len(result["distribution"]) == 1
        assert result["distribution"][0]["title"] == "test.txt"

    def test_data_product_item_json_serialization(self):
        """Test JSON serialization of DataProductItem."""
        distributions = [
            DataProductDistribution(
                title="api-data.json", media_type="application/json"
            )
        ]

        item = DataProductItem(distribution=distributions, region="global")

        json_str = item.json()
        assert "api-data.json" in json_str
        assert "global" in json_str
        assert "application/json" in json_str

    def test_data_product_item_nested_validation(self):
        """Test validation of nested DataProductDistribution objects."""
        # Valid nested objects
        distributions = [DataProductDistribution(title="valid.txt", byte_size=100)]

        item = DataProductItem(distribution=distributions)
        assert len(item.distribution) == 1

    def test_data_product_item_complex_structure(self):
        """Test DataProductItem with complex nested structure."""
        distributions = [
            DataProductDistribution(
                title="dataset.csv",
                byte_size=1048576,  # 1MB
                media_type="text/csv",
                format="csv",
                description="Large dataset file",
                issued="2023-01-01T00:00:00Z",
                modified="2023-01-15T12:30:00Z",
                checksum="abc123",
            ),
            DataProductDistribution(
                title="metadata.json",
                byte_size=512,
                media_type="application/json",
                format="json",
                description="Metadata for dataset",
                checksum="def456",
            ),
        ]

        item = DataProductItem(distribution=distributions, region="multi-region")

        assert len(item.distribution) == 2
        assert item.distribution[0].byte_size == 1048576
        assert item.distribution[1].byte_size == 512
        assert all(d.checksum is not None for d in item.distribution)


class TestSerializerIntegration:
    """Integration tests for serializers working together."""

    def test_full_api_response_structure(self):
        """Test creating a complete API response structure."""
        # Create distributions
        distributions = [
            DataProductDistribution(
                title="sales_data.csv",
                byte_size=2048,
                media_type="text/csv",
                format="csv",
                description="Sales data for Q1 2023",
            )
        ]

        # Create data product item
        product_item = DataProductItem(distribution=distributions, region="us-west-2")

        # Create connector metadata
        connector = ConnectorMetadata(
            connector_id="sales-fs-connector",
            region="us-west-2",
            supported_interfaces=["REST"],
            status="active",
            version="1.0.0",
        )

        # Verify all components work together
        assert product_item.region == connector.region
        assert len(product_item.distribution) == 1
        assert connector.status == "active"

    def test_serialization_round_trip(self):
        """Test serialization and deserialization round trip."""
        original_distribution = DataProductDistribution(
            title="roundtrip.txt",
            byte_size=1024,
            media_type="text/plain",
            checksum="test123",
        )

        # Serialize to dict and back
        data = original_distribution.dict()
        reconstructed = DataProductDistribution(**data)

        assert reconstructed.title == original_distribution.title
        assert reconstructed.byte_size == original_distribution.byte_size
        assert reconstructed.checksum == original_distribution.checksum

    def test_partial_data_handling(self):
        """Test handling of partial data in serializers."""
        # Create distribution with only some fields
        partial_distribution = DataProductDistribution(
            title="partial.txt",
            byte_size=256
            # Other fields will be None
        )

        # Should work fine with partial data
        item = DataProductItem(distribution=[partial_distribution])

        assert item.distribution[0].title == "partial.txt"
        assert item.distribution[0].byte_size == 256
        assert item.distribution[0].media_type is None
