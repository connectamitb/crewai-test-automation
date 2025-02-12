"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
from typing import Optional, Dict, List, Any

try:
    import weaviate
    from weaviate.client import Client
except ImportError:
    weaviate = None
    Client = None

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self._client = None

        if weaviate is None:
            self.logger.warning("Weaviate package not installed")
            return

        # Initialize client
        self.api_key = os.environ.get('WEAVIATE_API_KEY')
        if not self.api_key:
            self.logger.warning("WEAVIATE_API_KEY not set")
            return

        try:
            self.logger.info("Initializing Weaviate client with API key")
            self._client = Client(
                url="https://test-cases-b5c7k1op.weaviate.network",
                auth_client_secret=weaviate.auth.AuthApiKey(api_key=self.api_key),
                additional_headers={
                    "X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY", "")  # Optional for better vectorization
                }
            )
            self._ensure_schema()
            self.logger.info("Weaviate client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Weaviate: {str(e)}")
            self._client = None

    def _ensure_schema(self) -> None:
        """Ensure the required schema exists"""
        if not self._client:
            return

        schema = {
            "class": "TestCase",
            "vectorizer": "text2vec-openai",
            "properties": [
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Test case title",
                    "vectorizePropertyName": True
                },
                {
                    "name": "description",
                    "dataType": ["text"],
                    "description": "Test case description",
                    "vectorizePropertyName": True
                },
                {
                    "name": "format",
                    "dataType": ["object"],
                    "description": "Test case format",
                    "nestedProperties": [
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
                }
            ]
        }

        try:
            self.logger.debug("Checking for existing TestCase schema")
            classes = self._client.schema.get()
            if "TestCase" not in [c["class"] for c in classes.get("classes", [])]:
                self.logger.info("Creating TestCase schema in Weaviate")
                self._client.schema.create_class(schema)
                self.logger.info("Created TestCase schema successfully")
            else:
                self.logger.info("TestCase schema already exists")
        except Exception as e:
            self.logger.error(f"Schema creation failed: {str(e)}")

    def store_test_case(self, test_case: Any) -> Optional[str]:
        """Store a test case in Weaviate"""
        if not self._client:
            self.logger.error("Weaviate client not initialized")
            return None

        try:
            # Convert to Weaviate format
            weaviate_data = test_case.to_weaviate_format()
            self.logger.debug(f"Storing test case in Weaviate: {weaviate_data}")

            result = self._client.data_object.create(
                "TestCase",
                weaviate_data,
                "ALL"
            )
            self.logger.info(f"Successfully stored test case in Weaviate with ID: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Store failed: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        if not self._client:
            self.logger.error("Weaviate client not initialized")
            return []

        try:
            self.logger.debug(f"Searching Weaviate for query: {query}")
            result = (
                self._client.query
                .get("TestCase", ["title", "description", "format", "metadata"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                cases = result["data"]["Get"]["TestCase"]
                self.logger.info(f"Found {len(cases)} test cases in Weaviate")
                return cases

            self.logger.warning("No test cases found in Weaviate")
            return []
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []

    def get_test_case(self, title: str) -> Optional[Dict[str, Any]]:
        """Get a test case by title"""
        if not self._client:
            self.logger.error("Weaviate client not initialized")
            return None

        try:
            self.logger.debug(f"Getting test case with title: {title}")
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
            self.logger.error(f"Get failed: {str(e)}")
            return None