import logging
from weaviate.collections.classes.config import Configure, Property, DataType

class WeaviateSchema:
    def __init__(self, client):
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.current_version = "1.0"

    def ensure_schema(self):
        """Initialize schema if it doesn't exist"""
        try:
            # Check if TestCase collection exists
            if not self.client.collections.exists("TestCase"):
                self._create_test_case_schema()
                self.logger.info("Created TestCase schema")
            else:
                self.logger.info("TestCase schema already exists")
                
            # Initialize metadata collection if needed
            if not self.client.collections.exists("Metadata"):
                self._create_metadata_schema()
                self._store_schema_version()
                
        except Exception as e:
            self.logger.error(f"Schema initialization failed: {e}")
            raise

    def _create_test_case_schema(self):
        """Create TestCase collection schema"""
        self.client.collections.create(
            name="TestCase",
            properties=[
                Property(name="name", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="requirement", data_type=DataType.TEXT),
                Property(name="precondition", data_type=DataType.TEXT),
                Property(name="steps", data_type=DataType.TEXT_ARRAY),
                Property(name="expected_results", data_type=DataType.TEXT_ARRAY),
                Property(name="priority", data_type=DataType.TEXT),
                Property(name="tags", data_type=DataType.TEXT_ARRAY),
                Property(name="automation_status", data_type=DataType.TEXT),
                Property(name="created_at", data_type=DataType.DATE),
                Property(name="updated_at", data_type=DataType.DATE)
            ]
        )

    def _create_metadata_schema(self):
        """Create Metadata collection for schema versioning"""
        self.client.collections.create(
            name="Metadata",
            properties=[
                Property(name="key", data_type=DataType.TEXT),
                Property(name="value", data_type=DataType.TEXT)
            ]
        )

    def _store_schema_version(self):
        """Store current schema version in metadata"""
        metadata = self.client.collections.get("Metadata")
        metadata.data.insert({
            "key": "schema_version",
            "value": self.current_version
        }) 