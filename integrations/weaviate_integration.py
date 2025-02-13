"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
from weaviate.client import WeaviateClient
from weaviate.auth import AuthApiKey
from weaviate.embedded import EmbeddedOptions
from typing import Optional, Dict, List, Any
import uuid
from integrations.models import TestCase

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self, max_retries: int = 3):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries

        try:
            # Get credentials from environment
            self.api_key = os.getenv("WEAVIATE_API_KEY")
            openai_api_key = os.getenv("OPENAI_API_KEY")

            # Connect to existing Weaviate instance
            self.client = WeaviateClient(
                embedded_options=EmbeddedOptions(
                    hostname="0.0.0.0",
                    port=8079,
                    grpc_port=50060
                ),
                auth_client_secret=AuthApiKey(api_key=self.api_key),
                additional_headers={
                    "X-OpenAI-Api-Key": openai_api_key
                }
            )

            if self.is_healthy():
                self.logger.info("✅ Weaviate client initialized successfully")
                self._create_schema()
            else:
                self.logger.warning("❌ Weaviate health check failed")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Weaviate client: {str(e)}")
            self.client = None

    def is_healthy(self) -> bool:
        """Check if Weaviate is responding"""
        try:
            if not self.client:
                return False
            return self.client.is_ready()
        except Exception:
            return False

    def _create_schema(self):
        """Create the test case schema in Weaviate"""
        schema = {
            "class": "TestCase",
            "vectorizer": "text2vec-openai",
            "properties": [
                {"name": "name", "dataType": ["text"]},
                {"name": "objective", "dataType": ["text"]},
                {"name": "precondition", "dataType": ["text"]},
                {"name": "steps", "dataType": ["text[]"]},
                {"name": "requirement", "dataType": ["text"]},
                {"name": "gherkin", "dataType": ["text"]}
            ]
        }

        try:
            self.client.schema.create_class(schema)
            self.logger.info("Schema created successfully")
        except Exception as e:
            self.logger.warning(f"Schema creation skipped: {str(e)}")

    def store_test_case(self, test_case: TestCase) -> Optional[str]:
        """Store a test case in Weaviate"""
        if not self.is_healthy():
            self.logger.error("Weaviate client not healthy")
            return None

        try:
            # Convert test case to Weaviate format
            weaviate_data = test_case.to_weaviate_format()

            # Generate UUID for the test case
            test_case_id = str(uuid.uuid4())

            # Store in Weaviate
            self.client.data_object.create(
                data_object=weaviate_data,
                class_name="TestCase",
                uuid=test_case_id
            )

            self.logger.info(f"✅ Stored test case: {test_case.name}")
            return test_case_id

        except Exception as e:
            self.logger.error(f"❌ Failed to store test case: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        if not self.is_healthy():
            self.logger.error("Weaviate client not healthy")
            return []

        try:
            result = (
                self.client.query
                .get("TestCase", [
                    "name", 
                    "objective", 
                    "precondition", 
                    "steps", 
                    "requirement",
                    "gherkin"
                ])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                cases = result["data"]["Get"]["TestCase"]
                self.logger.info(f"Found {len(cases)} test cases matching query")
                return cases

            return []

        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []

    def get_test_case(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a test case by name"""
        if not self.is_healthy():
            self.logger.error("Weaviate client not healthy")
            return None

        try:
            result = (
                self.client.query
                .get("TestCase", ["name", "objective", "precondition", "steps", "requirement", "gherkin"])
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
                    self.logger.info(f"Found test case: {name}")
                    return cases[0]

            self.logger.warning(f"No test case found with name: {name}")
            return None

        except Exception as e:
            self.logger.error(f"Error retrieving test case: {str(e)}")
            return None