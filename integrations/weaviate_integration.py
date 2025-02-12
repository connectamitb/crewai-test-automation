"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
from typing import Optional, Dict, List
import json

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

        # Add console handler if not already added
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - WEAVIATE - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

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

            self.logger.info("🔑 Initializing Weaviate with API key")

            # Initialize client with configuration
            self._client = Client(
                url="https://mtkcafmlsuso0nc3pcaujg.c0.us-west3.gcp.weaviate.cloud",
                auth_client_secret=weaviate.auth.AuthApiKey(api_key=self.api_key),
                additional_headers={
                    "X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY", "")
                }
            )

            # Test connection
            self.logger.info("🔄 Testing Weaviate connection...")
            self._client.schema.get()
            self.logger.info("✅ Successfully connected to Weaviate")

            # Initialize schema
            self._ensure_schema()
            self._initialized = True
            self.logger.info("✅ Weaviate client fully initialized")

        except ImportError as e:
            self.logger.error(f"❌ Failed to import Weaviate: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Weaviate client: {str(e)}")
            self._initialized = False
            raise

    def _ensure_schema(self):
        """Ensure the required schema exists in Weaviate"""
        try:
            schema = {
                "class": "TestCase",
                "description": "Test case with requirements and steps",
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "model": "ada",
                        "modelVersion": "002",
                        "type": "text"
                    }
                },
                "properties": [
                    {
                        "name": "name",
                        "dataType": ["text"],
                        "description": "Name of the test case",
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": False,
                                "vectorizePropertyName": False
                            }
                        }
                    },
                    {
                        "name": "objective",
                        "dataType": ["text"],
                        "description": "Test case objective",
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": False,
                                "vectorizePropertyName": False
                            }
                        }
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
            self.logger.debug(f"Existing schema classes: {json.dumps(existing_classes, indent=2)}")

            class_names = [c["class"] for c in existing_classes.get("classes", [])]

            if "TestCase" not in class_names:
                self.logger.info("📝 Creating TestCase schema in Weaviate")
                self._client.schema.create_class(schema)
                self.logger.info("✅ Successfully created TestCase schema")
            else:
                self.logger.info("✅ TestCase schema already exists")

        except Exception as e:
            self.logger.error(f"❌ Error ensuring schema: {str(e)}")
            raise

    def store_test_case(self, test_case: TestCase) -> Optional[str]:
        """Store a test case in Weaviate"""
        try:
            self._lazy_init()  # Ensure client is initialized
            self.logger.info(f"📥 Storing test case: {test_case.name}")

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

            self.logger.debug(f"Test case data: {json.dumps(data_object, indent=2)}")

            result = self._client.data_object.create(
                class_name="TestCase",
                data_object=data_object,
                consistency_level="ALL"
            )

            self.logger.info(f"✅ Successfully stored test case with ID: {result}")
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to store test case: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for test cases using semantic search"""
        try:
            self._lazy_init()  # Ensure client is initialized
            self.logger.info(f"Searching test cases with query: {query}")

            # First check if we have any test cases
            count_result = (
                self._client.query
                .aggregate("TestCase")
                .with_meta_count()
                .do()
            )

            total_count = count_result.get("data", {}).get("Aggregate", {}).get("TestCase", [{}])[0].get("meta", {}).get("count", 0)
            self.logger.info(f"Total test cases in database: {total_count}")

            # Perform the search
            result = (
                self._client.query
                .get("TestCase", ["name", "objective", "precondition", "automationNeeded", "steps"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                test_cases = result["data"]["Get"]["TestCase"]
                self.logger.info(f"Found {len(test_cases)} matching test cases")
                return test_cases

            self.logger.warning("No test cases found")
            return []

        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []

    def get_test_case_by_name(self, name: str) -> Optional[Dict]:
        """Retrieve a test case by its name"""
        try:
            self._lazy_init()  # Ensure client is initialized
            self.logger.info(f"🔍 Looking up test case by name: {name}")

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
                if cases:
                    self.logger.info("✅ Found matching test case")
                    return cases[0]

            self.logger.warning("⚠️ No matching test case found")
            return None

        except Exception as e:
            self.logger.error(f"❌ Failed to retrieve test case: {str(e)}")
            return None