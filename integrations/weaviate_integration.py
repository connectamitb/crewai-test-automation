"""Weaviate integration for storing and retrieving test cases."""
import os
import time
import logging
from typing import Optional, Dict, List, Any

try:
    import weaviate
except ImportError:
    raise ImportError(
        "Weaviate package not found. Please install using: pip install weaviate-client==3.15.5"
    )

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self, max_retries: int = 3):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self._client = None
        self.max_retries = max_retries
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Weaviate client with retries"""
        self.api_key = os.environ.get('WEAVIATE_API_KEY')
        if not self.api_key:
            self.logger.error("WEAVIATE_API_KEY not found in environment variables")
            raise ValueError("WEAVIATE_API_KEY environment variable is required")

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.logger.info(f"Attempting to initialize Weaviate client (attempt {retry_count + 1})")

                # Initialize with correct auth method for version 3.15.5
                self._client = weaviate.Client(
                    url="https://test-cases-crewai-b5c7k1op.weaviate.network",
                    auth_client_secret=self.api_key,  # Pass API key directly as string
                    timeout_config=(30, 120)  # Increased timeouts
                )

                # Test connection
                if self._test_connection():
                    self._ensure_schema()
                    self.logger.info("Weaviate client initialized successfully")
                    return

            except Exception as e:
                self.logger.error(f"Weaviate initialization attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(2 ** retry_count)  # Exponential backoff

        self.logger.error(f"Failed to initialize Weaviate client after {self.max_retries} attempts")
        raise RuntimeError("Failed to initialize Weaviate client after multiple attempts")

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
            classes = self._client.schema.get()
            if "TestCase" not in [c["class"] for c in classes["classes"]]:
                self.logger.info("Creating TestCase schema in Weaviate")
                self._client.schema.create_class(schema)
                self.logger.info("Created TestCase schema successfully")
            else:
                self.logger.info("TestCase schema already exists")
        except Exception as e:
            self.logger.error(f"Schema creation failed: {str(e)}")
            raise

    def store_test_case(self, test_case: Any) -> Optional[str]:
        """Store a test case in Weaviate"""
        if not self._client:
            self.logger.error("Weaviate client not initialized")
            return None

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                weaviate_data = test_case.to_weaviate_format()
                self.logger.debug(f"Attempting to store test case (attempt {retry_count + 1}): {weaviate_data}")

                # Use the correct method signature for version 3.15.5
                uuid = self._client.data_object.create(
                    data_object=weaviate_data,
                    class_name="TestCase"
                )

                if uuid:
                    self.logger.info(f"Successfully stored test case with ID: {uuid}")
                    return uuid

            except Exception as e:
                self.logger.error(f"Store attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(2 ** retry_count)

        self.logger.error(f"Failed to store test case after {self.max_retries} attempts")
        return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        if not self._client:
            self.logger.error("Weaviate client not initialized")
            return []

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.logger.debug(f"Searching for test cases (attempt {retry_count + 1}): {query}")

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
                self.logger.error(f"Search attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(2 ** retry_count)

        self.logger.error(f"Failed to search test cases after {self.max_retries} attempts")
        return []

    def get_test_case(self, title: str) -> Optional[Dict[str, Any]]:
        """Get a test case by title with retries"""
        if not self._client:
            self.logger.error("Weaviate client not initialized")
            return None

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                self.logger.debug(f"Getting test case (attempt {retry_count + 1}): {title}")
                result = (
                    self._client.query
                    .get("TestCase", ["title", "description", "format", "metadata"])
                    .with_where({
                        "path": ["title"],
                        "operator": "Equal",
                        "valueString": title
                    })
                    .do()
                )

                if result and "data" in result and "Get" in result["data"]:
                    cases = result["data"]["Get"]["TestCase"]
                    if cases:
                        self.logger.info(f"Found test case: {title}")
                        return cases[0]

                self.logger.warning(f"No test case found with title: {title}")
                return None

            except Exception as e:
                self.logger.error(f"Get attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(2 ** retry_count)

        self.logger.error(f"Failed to get test case after {self.max_retries} attempts")
        return None