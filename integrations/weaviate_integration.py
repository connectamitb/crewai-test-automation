"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
import weaviate
from typing import Optional, Dict, List, Any
from weaviate.classes.init import Auth

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

            # Validate URL format
            if not weaviate_url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid WEAVIATE_URL format: {weaviate_url}. Must start with http:// or https://")

            self.logger.info(f"Attempting to connect to Weaviate at URL: {weaviate_url}")

            # Initialize client with cloud connection
            try:
                self.client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=weaviate_url,
                    auth_credentials=Auth.api_key(weaviate_api_key),
                    headers={
                        "X-OpenAI-Api-Key": openai_api_key
                    }
                )
                self.logger.info("✅ Successfully connected to Weaviate Cloud")

                # Verify connection immediately
                if not self.client.is_ready():
                    raise ConnectionError("Weaviate client created but not ready")

                # Create schema if it doesn't exist
                self._create_schema()

            except Exception as conn_error:
                self.logger.error(f"❌ Failed to connect to Weaviate: {str(conn_error)}")
                self.logger.exception("Detailed connection error:")
                raise

        except Exception as e:
            self.logger.error(f"❌ Weaviate initialization failed: {str(e)}")
            self.logger.exception("Detailed initialization error:")
            raise

    def _create_schema(self):
        """Create a simple test case schema in Weaviate"""
        schema = {
            "class": "TestCase",
            "description": "A test case for software testing",
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
                    "description": "The name of the test case",
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
                    "description": "The description of the test case",
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
                    "description": "Test execution steps",
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
                    "description": "Expected results for each step",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "skip": False,
                            "vectorizePropertyName": True
                        }
                    }
                }
            ]
        }

        try:
            # Check if schema exists
            self.logger.debug("Checking existing schema...")
            current_schema = self.client.schema.get()
            existing_classes = [c["class"] for c in current_schema.get("classes", [])]

            if "TestCase" not in existing_classes:
                self.logger.info("Creating TestCase schema...")
                self.client.schema.create_class(schema)
                self.logger.info("✅ Created TestCase schema in Weaviate")
            else:
                self.logger.info("✅ TestCase schema already exists")

        except Exception as e:
            self.logger.error(f"❌ Error creating schema: {str(e)}")
            raise

    def is_healthy(self) -> bool:
        """Check if Weaviate is responding"""
        try:
            self.logger.debug("Checking Weaviate health status...")

            # First check basic client readiness
            try:
                is_ready = self.client.is_ready()
                self.logger.info(f"Basic client readiness check: {'✅ Ready' if is_ready else '❌ Not ready'}")
                if not is_ready:
                    return False
            except Exception as e:
                self.logger.error(f"❌ Basic client readiness check failed: {str(e)}")
                return False

            # Test connection by attempting to get schema
            try:
                schema = self.client.schema.get()
                self.logger.debug(f"Retrieved schema: {schema}")

                if not schema:
                    self.logger.error("❌ Retrieved empty schema")
                    return False

                if not isinstance(schema, dict) or 'classes' not in schema:
                    self.logger.error(f"❌ Invalid schema format: {schema}")
                    return False

                if any(c["class"] == "TestCase" for c in schema.get("classes", [])):
                    self.logger.info("✅ TestCase schema exists and is accessible")
                    return True
                else:
                    self.logger.error("❌ TestCase schema not found in schema")
                    self._create_schema()  # Attempt to create schema
                    return self.is_healthy()  # Recursive check after schema creation

            except Exception as schema_error:
                self.logger.error(f"❌ Schema verification failed: {str(schema_error)}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Health check failed with error: {str(e)}")
            # Log the full error details for debugging
            self.logger.exception("Detailed error information:")
            return False

    def store_test_case(self, test_case) -> Optional[str]:
        """Store a test case in Weaviate"""
        try:
            # Convert to Weaviate format
            test_case_data = test_case.to_weaviate_format()
            self.logger.debug(f"Attempting to store test case: {test_case_data}")

            # Verify health before storing
            if not self.is_healthy():
                self.logger.error("❌ Weaviate is not healthy, cannot store test case")
                return None

            # Store in Weaviate
            try:
                # Create the object
                uuid = self.client.data_object.create(
                    class_name="TestCase",
                    properties=test_case_data
                )

                if uuid:
                    self.logger.info(f"✅ Successfully stored test case with ID: {uuid}")
                    return uuid
                else:
                    self.logger.error("❌ No UUID returned from create operation")
                    return None

            except Exception as e:
                self.logger.error(f"❌ Error storing test case: {str(e)}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Failed to store test case: {str(e)}")
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        try:
            self.logger.debug(f"Searching for test cases with query: {query}")

            # Perform semantic search
            result = (
                self.client.query
                .get("TestCase", ["name", "description", "steps", "expectedResults"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            self.logger.debug(f"Search result: {result}")

            if result and "data" in result and "Get" in result["data"]:
                test_cases = result["data"]["Get"]["TestCase"]
                return test_cases
            return []

        except Exception as e:
            self.logger.error(f"❌ Search error: {str(e)}")
            return []

    def get_test_case(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a test case by name"""
        try:
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