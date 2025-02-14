"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
import weaviate
from typing import Optional, Dict, List, Any
import uuid

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)

        # Get credentials from environment
        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

        if not weaviate_url or not weaviate_api_key:
            raise ValueError("Missing required Weaviate credentials")

        # Initialize client
        self.client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=weaviate.AuthApiKey(api_key=weaviate_api_key)
        )

        # Create schema if it doesn't exist
        self._create_schema()

    def _create_schema(self):
        """Create a simple test case schema in Weaviate"""
        schema = {
            "class": "TestCase",
            "vectorizer": "text2vec-contextionary",
            "properties": [
                {
                    "name": "name",
                    "dataType": ["string"],
                    "description": "The name of the test case"
                },
                {
                    "name": "description",
                    "dataType": ["text"],
                    "description": "The description of the test case"
                },
                {
                    "name": "steps",
                    "dataType": ["text[]"],
                    "description": "Test execution steps"
                },
                {
                    "name": "expectedResults",
                    "dataType": ["text[]"],
                    "description": "Expected results for each step"
                }
            ]
        }

        # Create schema if it doesn't exist
        if not any(c["class"] == "TestCase" for c in self.client.schema.get().get("classes", [])):
            self.client.schema.create_class(schema)

    def is_healthy(self) -> bool:
        """Check if Weaviate is responding"""
        try:
            return self.client.is_ready()
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    def store_test_case(self, test_case) -> Optional[str]:
        """Store a test case in Weaviate"""
        try:
            # Generate UUID for the test case
            test_case_id = str(uuid.uuid4())

            # Store in Weaviate
            self.client.data_object.create(
                data_object=test_case.to_weaviate_format(),
                class_name="TestCase",
                uuid=test_case_id
            )

            return test_case_id
        except Exception as e:
            self.logger.error(f"Failed to store test case: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        try:
            result = (
                self.client.query
                .get("TestCase", ["name", "description", "steps", "expectedResults"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                return result["data"]["Get"]["TestCase"]
            return []

        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []

    def get_test_case(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a test case by name"""
        try:
            result = (
                self.client.query
                .get("TestCase", ["name", "description", "steps", "expectedResults"])
                .with_where({
                    "path": ["name"],
                    "operator": "Equal",
                    "valueString": name
                })
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                cases = result["data"]["Get"]["TestCase"]
                if cases:
                    return cases[0]
            return None

        except Exception as e:
            self.logger.error(f"Error retrieving test case: {str(e)}")
            return None