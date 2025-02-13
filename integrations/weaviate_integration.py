"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
import weaviate
from typing import Optional, Dict, List, Any
import uuid
from integrations.models import TestCase

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)
        self.client = None

        try:
            # Get credentials from environment
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

            if not weaviate_api_key:
                raise ValueError("WEAVIATE_API_KEY environment variable is required")

            # Initialize client with v3.25.3 compatible configuration
            self.client = weaviate.Client(
                url=weaviate_url,
                auth_client_secret=weaviate.AuthApiKey(api_key=weaviate_api_key)
            )

            if self.is_healthy():
                self.logger.info("✅ Weaviate client initialized successfully")
                self._create_schema()
            else:
                self.logger.error("❌ Weaviate health check failed")
                self.client = None

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Weaviate client: {str(e)}")
            self.client = None
            raise

    def is_healthy(self) -> bool:
        """Check if Weaviate is responding"""
        try:
            if not self.client:
                return False
            return self.client.is_ready()
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    def _create_schema(self):
        """Create the test case schema in Weaviate"""
        try:
            current_schema = self.client.schema.get()
            if any(c["class"] == "TestCase" for c in current_schema.get("classes", [])):
                self.logger.info("Schema already exists")
                return

            schema = {
                "class": "TestCase",
                "vectorizer": "text2vec-openai",  # This can be changed based on your needs
                "properties": [
                    {
                        "name": "name",
                        "dataType": ["string"],
                        "description": "The name of the test case"
                    },
                    {
                        "name": "objective",
                        "dataType": ["text"],
                        "description": "The objective of the test case"
                    },
                    {
                        "name": "precondition",
                        "dataType": ["text"],
                        "description": "Required preconditions for the test"
                    },
                    {
                        "name": "steps",
                        "dataType": ["text[]"],
                        "description": "Test execution steps"
                    },
                    {
                        "name": "requirement",
                        "dataType": ["text"],
                        "description": "Original requirement text"
                    },
                    {
                        "name": "gherkin",
                        "dataType": ["text"],
                        "description": "Gherkin format of the test case"
                    }
                ]
            }

            self.client.schema.create_class(schema)
            self.logger.info("✅ Schema created successfully")

        except Exception as e:
            self.logger.error(f"Schema creation failed: {str(e)}")
            raise

    def store_test_case(self, test_case: TestCase) -> Optional[str]:
        """Store a test case in Weaviate"""
        if not self.is_healthy():
            self.logger.error("❌ Weaviate client not healthy")
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
            self.logger.error("❌ Weaviate client not healthy")
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
                self.logger.info(f"✅ Found {len(cases)} test cases matching query")
                return cases

            return []

        except Exception as e:
            self.logger.error(f"❌ Search error: {str(e)}")
            return []

    def get_test_case(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a test case by name"""
        if not self.is_healthy():
            self.logger.error("❌ Weaviate client not healthy")
            return None

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