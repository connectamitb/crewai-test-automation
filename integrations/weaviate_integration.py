"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
from typing import Optional, Dict, List

# Import models before weaviate to prevent circular imports
from .models import TestCase

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""
    _instance = None
    _initialized = False
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WeaviateIntegration, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        if self._initialized:
            return

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def _lazy_init(self):
        """Lazy initialization of Weaviate client to avoid import issues"""
        if self._initialized:
            return

        try:
            # Import weaviate here to avoid circular imports
            import weaviate
            from weaviate import Client

            # Get API key from environment
            self.api_key = os.environ.get('WEAVIATE_API_KEY')
            if not self.api_key:
                raise ValueError("WEAVIATE_API_KEY environment variable not set")

            # Initialize client with configuration
            self._client = Client(
                url="https://mtkcafmlsuso0nc3pcaujg.c0.us-west3.gcp.weaviate.cloud",
                auth_client_secret=weaviate.auth.AuthApiKey(api_key=self.api_key),
                additional_headers={
                    "X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY", "")
                }
            )

            # Test connection
            self._client.schema.get()
            self.logger.info("Successfully connected to Weaviate")

            # Initialize schema
            self._ensure_schema()

            self._initialized = True
            self.logger.info("Successfully initialized Weaviate client")

        except ImportError as e:
            self.logger.error(f"Failed to import Weaviate: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize Weaviate client: {str(e)}")
            self._initialized = False
            raise

    def _ensure_schema(self):
        """Ensure the required schema exists in Weaviate"""
        try:
            schema = {
                "class": "TestCase",
                "description": "Test case with requirements and steps",
                "vectorizer": "text2vec-openai",
                "properties": [
                    {
                        "name": "name",
                        "dataType": ["text"],
                        "description": "Name of the test case"
                    },
                    {
                        "name": "objective",
                        "dataType": ["text"],
                        "description": "Test case objective"
                    },
                    {
                        "name": "precondition",
                        "dataType": ["text"],
                        "description": "Preconditions for the test case"
                    },
                    {
                        "name": "automationNeeded",
                        "dataType": ["text"],
                        "description": "Whether automation is needed"
                    },
                    {
                        "name": "steps",
                        "dataType": ["text[]"],
                        "description": "Test steps"
                    }
                ]
            }

            # Check if schema exists
            existing_classes = self._client.schema.get()
            class_names = [c["class"] for c in existing_classes.get("classes", [])]

            if "TestCase" not in class_names:
                self._client.schema.create_class(schema)
                self.logger.info("Created TestCase schema in Weaviate")

        except Exception as e:
            self.logger.error(f"Error ensuring schema: {str(e)}")
            raise

    def store_test_case(self, test_case: TestCase) -> Optional[str]:
        """Store a test case in Weaviate"""
        try:
            self._lazy_init()  # Ensure client is initialized

            steps_str = [
                f"Step: {step['step']}\nTest Data: {step['test_data']}\nExpected Result: {step['expected_result']}"
                for step in test_case.steps
            ]

            data_object = {
                "name": test_case.name,
                "objective": test_case.objective,
                "precondition": test_case.precondition,
                "automationNeeded": test_case.automation_needed,
                "steps": steps_str
            }

            result = self._client.data_object.create(
                class_name="TestCase",
                data_object=data_object,
                consistency_level="ALL"
            )

            self.logger.info(f"Successfully stored test case: {test_case.name}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to store test case: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for test cases using semantic search"""
        try:
            self._lazy_init()  # Ensure client is initialized
            self.logger.info(f"Searching test cases with query: {query}")

            result = (
                self._client.query
                .get("TestCase", ["name", "objective", "precondition", "automationNeeded", "steps"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            self.logger.debug(f"Raw search response: {result}")

            if result and "data" in result and "Get" in result["data"]:
                test_cases = result["data"]["Get"]["TestCase"]
                self.logger.info(f"Found {len(test_cases)} test cases")
                return test_cases

            self.logger.warning("No test cases found or invalid response format")
            return []

        except Exception as e:
            self.logger.error(f"Failed to search test cases: {str(e)}", exc_info=True)
            return []

    def get_test_case_by_name(self, name: str) -> Optional[Dict]:
        """Retrieve a test case by its name"""
        try:
            self._lazy_init()  # Ensure client is initialized

            result = (
                self._client.query
                .get("TestCase", ["name", "objective", "precondition", "automationNeeded", "steps"])
                .with_where({
                    "path": ["name"],
                    "operator": "Equal",
                    "valueString": name
                })
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                cases = result["data"]["Get"]["TestCase"]
                return cases[0] if cases else None
            return None

        except Exception as e:
            self.logger.error(f"Failed to retrieve test case: {str(e)}")
            return None