"""Weaviate integration for storing and retrieving test cases."""
import os
import time
import logging
from typing import Optional, Dict, List, Any

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self, max_retries: int = 3, startup_period: int = 120):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self._client = None
        self.max_retries = max_retries
        self.startup_period = startup_period

        try:
            import weaviate
            self._weaviate = weaviate
        except ImportError:
            self.logger.error("Failed to import weaviate package")
            self._weaviate = None
            return

        try:
            self._initialize_client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Weaviate client: {str(e)}")
            # Continue without client, allowing degraded functionality

    def _initialize_client(self) -> None:
        """Initialize the Weaviate client with retries"""
        if not self._weaviate:
            return

        self.api_key = os.environ.get('WEAVIATE_API_KEY')
        if not self.api_key:
            self.logger.warning("WEAVIATE_API_KEY not found, running in mock mode")
            return

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.logger.info(f"Attempting to initialize Weaviate client (attempt {retry_count + 1})")

                # Create auth config
                auth_config = self._weaviate.auth.AuthApiKey(api_key=self.api_key)

                # Initialize client with increased timeout and startup period
                self._client = self._weaviate.Client(
                    url="https://test-cases-crewai-b5c7k1op.weaviate.network",
                    auth_client_secret=auth_config,
                    timeout_config=(60, 180),  # Further increased timeouts (connect, read)
                    startup_period=self.startup_period  # Use the provided startup period
                )

                # Test connection
                if self._test_connection():
                    self.logger.info("Weaviate client initialized successfully")
                    return

            except Exception as e:
                self.logger.error(f"Weaviate initialization attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    wait_time = min(2 ** retry_count, 30)
                    self.logger.info(f"Waiting {wait_time} seconds before retry")
                    time.sleep(wait_time)

        self.logger.error(f"Failed to initialize Weaviate client after {self.max_retries} attempts")
        self._client = None

    def is_healthy(self) -> bool:
        """Check if the Weaviate client is healthy and connected"""
        try:
            return bool(self._client and self._test_connection())
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    def _test_connection(self) -> bool:
        """Test the Weaviate connection"""
        try:
            if not self._client:
                return False
            self._client.schema.get()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

    def _ensure_schema(self) -> None:
        """Ensure the required schema exists"""
        if not self._client:
            return

        schema = {
            "class": "TestCase",
            "description": "Test case information",
            "vectorizer": "text2vec-openai",
            "properties": [
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Test case title"
                },
                {
                    "name": "description",
                    "dataType": ["text"],
                    "description": "Test case description"
                },
                {
                    "name": "format",
                    "dataType": ["object"],
                    "description": "Test case format",
                    "properties": [
                        {
                            "name": "given",
                            "dataType": ["text[]"]
                        },
                        {
                            "name": "when",
                            "dataType": ["text[]"]
                        },
                        {
                            "name": "then",
                            "dataType": ["text[]"]
                        }
                    ]
                },
                {
                    "name": "metadata",
                    "dataType": ["object"],
                    "description": "Additional test case metadata"
                }
            ]
        }

        try:
            self.logger.debug("Checking for existing TestCase schema")
            existing_schema = self._client.schema.get()
            if existing_schema and "classes" in existing_schema:
                existing_classes = [c["class"] for c in existing_schema["classes"]]
                if "TestCase" not in existing_classes:
                    self.logger.info("Creating TestCase schema in Weaviate")
                    self._client.schema.create_class(schema)
                    self.logger.info("Created TestCase schema successfully")
                else:
                    self.logger.info("TestCase schema already exists")
            else:
                self.logger.warning("Could not verify schema, response format unexpected")

        except Exception as e:
            self.logger.error(f"Schema creation failed: {str(e)}")
            # Continue without schema creation

    def store_test_case(self, test_case: Any) -> Optional[str]:
        """Store a test case in Weaviate"""
        if not self.is_healthy():
            self.logger.error("Weaviate client not healthy")
            return None

        try:
            weaviate_data = test_case.to_weaviate_format()
            self.logger.debug(f"Attempting to store test case: {weaviate_data}")

            # Only attempt to store if client is available
            if self._client:
                uuid = self._client.data_object.create(
                    data_object=weaviate_data,
                    class_name="TestCase"
                )
                if uuid:
                    self.logger.info(f"Successfully stored test case with ID: {uuid}")
                    return uuid
            else:
                self.logger.warning("Store operation skipped - client unavailable")

        except Exception as e:
            self.logger.error(f"Failed to store test case: {str(e)}")

        return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        if not self.is_healthy():
            self.logger.error("Weaviate client not healthy")
            return []

        try:
            if not self._client:
                self.logger.warning("Search operation skipped - client unavailable")
                return []

            result = (
                self._client.query
                .get("TestCase", ["title", "description", "format", "metadata"])
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
            if not self._client:
                self.logger.warning("Get operation skipped - client unavailable")
                return None

            result = (
                self._client.query
                .get("TestCase", ["title", "description", "format", "metadata"])
                .with_where({
                    "path": ["title"],
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