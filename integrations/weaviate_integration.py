"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
from typing import Optional, Dict, List, Any
import weaviate
from weaviate.auth import AuthApiKey
from weaviate.connect import ConnectionParams

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        try:
            # Get credentials from environment
            weaviate_url = os.getenv("WEAVIATE_URL")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
            openai_api_key = os.getenv("OPENAI_API_KEY")

            # Validate credentials
            if not weaviate_url:
                raise ValueError("WEAVIATE_URL is not set")
            if not weaviate_api_key:
                raise ValueError("WEAVIATE_API_KEY is not set")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY is not set")

            self.logger.info(f"Attempting to connect to Weaviate at: {weaviate_url}")

            # Initialize client with v4 syntax and proper auth
            auth = AuthApiKey(api_key=weaviate_api_key)
            connection_params = ConnectionParams.from_params(
                url=weaviate_url,
                auth_credentials=auth,
                headers={
                    "X-OpenAI-Api-Key": openai_api_key
                }
            )
            self.client = weaviate.WeaviateClient(connection_params=connection_params)

            self.logger.info("✅ Successfully initialized Weaviate client")

            # Create schema if it doesn't exist
            self._create_schema()

        except Exception as e:
            self.logger.error(f"❌ Weaviate initialization failed: {str(e)}")
            self.logger.exception("Detailed initialization error:")
            raise

    def _create_schema(self):
        """Create test case schema in Weaviate"""
        try:
            # Check if schema exists
            schema = self.client.schema.get()

            if not any(c.get("class") == "TestCase" for c in schema.get("classes", [])):
                class_obj = {
                    "class": "TestCase",
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
                            "dataType": ["string"],
                            "moduleConfig": {
                                "text2vec-openai": {
                                    "skip": False,
                                    "vectorizePropertyName": True
                                }
                            }
                        },
                        {
                            "name": "description",
                            "dataType": ["text"],
                            "moduleConfig": {
                                "text2vec-openai": {
                                    "skip": False,
                                    "vectorizePropertyName": True
                                }
                            }
                        },
                        {
                            "name": "steps",
                            "dataType": ["text[]"],
                            "moduleConfig": {
                                "text2vec-openai": {
                                    "skip": False,
                                    "vectorizePropertyName": True
                                }
                            }
                        },
                        {
                            "name": "expectedResults",
                            "dataType": ["text[]"],
                            "moduleConfig": {
                                "text2vec-openai": {
                                    "skip": False,
                                    "vectorizePropertyName": True
                                }
                            }
                        }
                    ]
                }

                self.client.schema.create(class_obj)
                self.logger.info("✅ Created TestCase schema")
            else:
                self.logger.info("✅ TestCase schema already exists")

        except Exception as e:
            self.logger.error(f"❌ Error creating schema: {str(e)}")
            raise

    def is_healthy(self) -> bool:
        """Check if Weaviate is responding"""
        try:
            self.logger.debug("Checking Weaviate health status...")
            return self.client.is_ready()

        except Exception as e:
            self.logger.error(f"❌ Health check failed: {str(e)}")
            self.logger.exception("Detailed error:")
            return False

    def store_test_case(self, test_case) -> Optional[str]:
        """Store a test case in Weaviate"""
        try:
            if not self.is_healthy():
                raise Exception("Weaviate is not healthy")

            test_case_data = test_case.to_weaviate_format()
            self.logger.debug(f"Storing test case: {test_case_data}")

            # Create data object using v4 syntax
            result = self.client.objects.create(
                class_name="TestCase",
                properties=test_case_data
            )

            if result:
                case_id = result.uuid
                self.logger.info(f"✅ Stored test case with ID: {case_id}")
                return case_id
            else:
                raise Exception("No ID returned from storage operation")

        except Exception as e:
            self.logger.error(f"❌ Failed to store test case: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        try:
            if not self.is_healthy():
                raise Exception("Weaviate is not healthy")

            # Use v4 query syntax
            response = (
                self.client.collections.get("TestCase")
                .query
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .with_fields("name", "description", "steps", "expectedResults")
                .do()
            )

            if response and response.objects:
                return [obj.properties for obj in response.objects]
            return []

        except Exception as e:
            self.logger.error(f"❌ Search error: {str(e)}")
            return []

    def get_test_case(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a test case by name"""
        try:
            if not self.is_healthy():
                raise Exception("Weaviate is not healthy")

            # Use v4 query syntax
            response = (
                self.client.collections.get("TestCase")
                .query
                .with_fields("name", "description", "steps", "expectedResults")
                .with_where({
                    "path": ["name"],
                    "operator": "Equal",
                    "valueString": name
                })
                .do()
            )

            if response and response.objects:
                return response.objects[0].properties
            return None

        except Exception as e:
            self.logger.error(f"❌ Error retrieving test case: {str(e)}")
            return None