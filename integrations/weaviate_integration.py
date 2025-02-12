"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
from typing import Optional, Dict, List
try:
    import weaviate
    from weaviate import Client
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

from .models import TestCase

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WeaviateIntegration, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        if self._initialized:
            return

        # Configure logging first
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        try:
            if not WEAVIATE_AVAILABLE:
                raise ImportError("Weaviate client not installed")

            # Get API key from environment
            self.api_key = os.environ.get('WEAVIATE_API_KEY')
            if not self.api_key:
                raise ValueError("WEAVIATE_API_KEY environment variable not set")

            # Initialize client
            self.client = Client(
                url="https://mtkcafmlsuso0nc3pcaujg.c0.us-west3.gcp.weaviate.cloud",
                auth_client_secret=weaviate.AuthApiKey(api_key=self.api_key)
            )

            self._initialized = True
            self.logger.info("Successfully initialized Weaviate client")

            # Ensure schema exists
            self._ensure_schema()

        except Exception as e:
            self.logger.error(f"Failed to initialize Weaviate client: {str(e)}")
            raise

    def _ensure_schema(self) -> None:
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
                        "description": "Whether automation is needed (Yes/No/TBD)"
                    },
                    {
                        "name": "steps",
                        "dataType": ["text[]"],
                        "description": "Test steps with data and expected results"
                    }
                ]
            }

            existing_classes = [c["class"] for c in self.client.schema.get()["classes"]]
            if "TestCase" not in existing_classes:
                self.client.schema.create_class(schema)
                self.logger.info("Created TestCase schema")

        except Exception as e:
            self.logger.error(f"Error ensuring schema: {str(e)}")
            raise

    def store_test_case(self, test_case: TestCase) -> Optional[str]:
        """Store a test case in Weaviate"""
        try:
            # Convert steps to string array for storage
            steps_str = [
                f"Step: {step['step']}\nTest Data: {step['test_data']}\nExpected Result: {step['expected_result']}"
                for step in test_case.steps
            ]

            # Create data object
            data_object = {
                "name": test_case.name,
                "objective": test_case.objective,
                "precondition": test_case.precondition,
                "automationNeeded": test_case.automation_needed,
                "steps": steps_str
            }

            result = self.client.data_object.create(
                class_name="TestCase",
                data_object=data_object
            )

            self.logger.info(f"Successfully stored test case: {test_case.name}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to store test case: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for test cases using semantic search"""
        try:
            result = (
                self.client.query
                .get("TestCase", ["name", "objective", "precondition", "automationNeeded", "steps"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                return result["data"]["Get"]["TestCase"]
            return []

        except Exception as e:
            self.logger.error(f"Failed to search test cases: {str(e)}")
            return []

    def get_test_case_by_name(self, name: str) -> Optional[Dict]:
        """Retrieve a test case by its name"""
        try:
            result = (
                self.client.query
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