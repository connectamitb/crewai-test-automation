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
            self._client = Client(
                url="https://test-cases-b5c7k1op.weaviate.network",
                auth_client_secret=weaviate.auth.AuthApiKey(api_key=self.api_key)
            )
            self._ensure_schema()
            self.logger.info("Weaviate client initialized")
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
            classes = self._client.schema.get()
            if "TestCase" not in [c["class"] for c in classes.get("classes", [])]:
                self._client.schema.create_class(schema)
                self.logger.info("Created TestCase schema")
        except Exception as e:
            self.logger.error(f"Schema creation failed: {str(e)}")

    def store_test_case(self, test_case: Any) -> Optional[str]:
        """Store a test case in Weaviate"""
        if not self._client:
            return None

        try:
            # Convert to Weaviate format
            weaviate_data = test_case.to_weaviate_format()

            result = self._client.data_object.create(
                "TestCase",
                weaviate_data,
                "ALL"
            )
            return result
        except Exception as e:
            self.logger.error(f"Store failed: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        if not self._client:
            return []

        try:
            result = (
                self._client.query
                .get("TestCase", ["title", "description", "format"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                return result["data"]["Get"]["TestCase"]
            return []
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return []

    def get_test_case(self, title: str) -> Optional[Dict[str, Any]]:
        """Get a test case by title"""
        if not self._client:
            return None

        try:
            result = (
                self._client.query
                .get("TestCase", ["title", "description", "format"])
                .with_where({
                    "path": ["title"],
                    "operator": "Equal",
                    "valueString": title
                })
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                cases = result["data"]["Get"]["TestCase"]
                return cases[0] if cases else None
            return None
        except Exception as e:
            self.logger.error(f"Get failed: {str(e)}")
            return None