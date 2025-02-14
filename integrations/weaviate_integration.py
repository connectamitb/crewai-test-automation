"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
from typing import Optional, Dict, List, Any
import weaviate

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

            self.logger.info(f"Attempting to connect to Weaviate at URL: {weaviate_url}")

            # Initialize client
            auth_config = weaviate.auth.AuthApiKey(api_key=weaviate_api_key)

            self.client = weaviate.Client(
                url=weaviate_url,
                auth_client_secret=auth_config,
                additional_headers={
                    "X-OpenAI-Api-Key": openai_api_key
                }
            )

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

                self.client.schema.create_class(class_obj)
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

            # Check if client is ready
            if not self.client.is_ready():
                self.logger.error("❌ Weaviate client not ready")
                return False

            # Verify schema exists
            schema = self.client.schema.get()
            if not schema:
                self.logger.error("❌ Could not retrieve schema")
                return False

            # Check if TestCase class exists
            if not any(c.get("class") == "TestCase" for c in schema.get("classes", [])):
                self.logger.error("❌ TestCase schema not found")
                return False

            self.logger.info("✅ Weaviate is healthy")
            return True

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

            try:
                with self.client.batch as batch:
                    batch.configure(batch_size=1)
                    result = batch.add_data_object(
                        data_object=test_case_data,
                        class_name="TestCase"
                    )

                if result:
                    self.logger.info(f"✅ Stored test case with ID: {result}")
                    return result
                else:
                    raise Exception("No ID returned from storage operation")

            except Exception as store_error:
                self.logger.error(f"❌ Storage error: {str(store_error)}")
                raise

        except Exception as e:
            self.logger.error(f"❌ Failed to store test case: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        try:
            if not self.is_healthy():
                raise Exception("Weaviate is not healthy")

            result = (
                self.client.query
                .get("TestCase", ["name", "description", "steps", "expectedResults"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                return result["data"]["Get"]["TestCase"]
            return []

        except Exception as e:
            self.logger.error(f"❌ Search error: {str(e)}")
            return []

    def get_test_case(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a test case by name"""
        try:
            if not self.is_healthy():
                raise Exception("Weaviate is not healthy")

            result = (
                self.client.query
                .get("TestCase", ["name", "description", "steps", "expectedResults"])
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
                    return cases[0]
            return None

        except Exception as e:
            self.logger.error(f"❌ Error retrieving test case: {str(e)}")
            return None