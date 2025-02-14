"""Weaviate integration for storing and retrieving test cases."""
import os
import logging
import weaviate
from typing import Optional, Dict, List, Any
import uuid
from integrations.models import TestCase
import time
import traceback

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        self.logger = logging.getLogger(__name__)
        self.client = None

        try:
            # Get credentials from environment
            weaviate_url = os.getenv("WEAVIATE_URL")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

            self.logger.info("Initializing Weaviate with URL: %s", weaviate_url)
            if not weaviate_url or not weaviate_api_key:
                raise ValueError("Missing required Weaviate credentials")

            # Initialize client with retry logic
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    self.logger.debug("Attempting to connect to Weaviate (attempt %d/%d)", retry_count + 1, max_retries)
                    self.client = weaviate.Client(
                        url=weaviate_url,
                        auth_client_secret=weaviate.AuthApiKey(api_key=weaviate_api_key),
                        timeout_config=(10, 60)
                    )

                    # Verify connection is working
                    if self.is_healthy():
                        self.logger.info("✅ Successfully connected to Weaviate")
                        # Create schema if it doesn't exist
                        self._create_schema()
                        break
                    else:
                        raise ConnectionError("Weaviate health check failed")

                except Exception as e:
                    retry_count += 1
                    self.logger.error("Connection attempt %d failed: %s\n%s", 
                                    retry_count, str(e), traceback.format_exc())
                    if retry_count == max_retries:
                        raise
                    time.sleep(2)

        except Exception as e:
            self.logger.error("❌ Failed to initialize Weaviate: %s\n%s", 
                            str(e), traceback.format_exc())
            self.client = None
            raise

    def _create_schema(self):
        """Create the test case schema in Weaviate"""
        try:
            self.logger.info("Checking if schema exists...")
            current_schema = self.client.schema.get()
            if any(c["class"] == "TestCase" for c in current_schema.get("classes", [])):
                self.logger.info("Schema already exists")
                return

            schema = {
                "class": "TestCase",
                "vectorizer": "text2vec-contextionary",
                "properties": [
                    {
                        "name": "name",
                        "dataType": ["string"],
                        "description": "The name of the test case"
                    },
                    {
                        "name": "objective",
                        "dataType": ["text"],
                        "description": "The objective of the test case"
                    },
                    {
                        "name": "precondition",
                        "dataType": ["text"],
                        "description": "Required preconditions for the test"
                    },
                    {
                        "name": "steps",
                        "dataType": ["text[]"],
                        "description": "Test execution steps"
                    },
                    {
                        "name": "requirement",
                        "dataType": ["text"],
                        "description": "Original requirement text"
                    },
                    {
                        "name": "gherkin",
                        "dataType": ["text"],
                        "description": "Gherkin format of the test case"
                    }
                ]
            }

            self.client.schema.create_class(schema)
            self.logger.info("✅ Schema created successfully")

        except Exception as e:
            self.logger.error("Schema creation failed: %s\n%s", 
                            str(e), traceback.format_exc())
            raise

    def is_healthy(self) -> bool:
        """Check if Weaviate is responding"""
        try:
            if not self.client:
                self.logger.error("No Weaviate client available")
                return False

            is_live = self.client.is_live()
            is_ready = self.client.is_ready()

            self.logger.info("Weaviate health check - Live: %s, Ready: %s", is_live, is_ready)

            if not is_live:
                self.logger.error("Weaviate is not live")
            if not is_ready:
                self.logger.error("Weaviate is not ready")

            return is_live and is_ready

        except Exception as e:
            self.logger.error("Health check failed: %s\n%s", 
                            str(e), traceback.format_exc())
            return False

    def store_test_case(self, test_case: TestCase) -> Optional[str]:
        """Store a test case in Weaviate"""
        if not self.is_healthy():
            self.logger.error("❌ Weaviate client not healthy")
            return None

        try:
            # Convert test case to Weaviate format
            weaviate_data = test_case.to_weaviate_format()
            self.logger.debug("Storing test case data: %s", weaviate_data)

            # Generate UUID for the test case
            test_case_id = str(uuid.uuid4())

            # Store in Weaviate
            self.logger.info("Attempting to store test case with ID: %s", test_case_id)
            self.client.data_object.create(
                data_object=weaviate_data,
                class_name="TestCase",
                uuid=test_case_id
            )

            self.logger.info("✅ Successfully stored test case: %s with ID: %s", test_case.name, test_case_id)

            # Verify storage by attempting to retrieve
            verification = self.get_test_case(test_case.name)
            if verification:
                self.logger.info("✅ Verified test case storage - retrieval successful")
            else:
                self.logger.error("❌ Failed to verify test case storage - could not retrieve stored case")
                return None

            return test_case_id

        except Exception as e:
            self.logger.error("❌ Failed to store test case: %s\n%s", str(e), traceback.format_exc())
            return None

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using vector similarity"""
        if not self.is_healthy():
            self.logger.error("❌ Weaviate client not healthy")
            return []

        try:
            result = (
                self.client.query
                .get("TestCase", [
                    "name", 
                    "objective", 
                    "precondition", 
                    "steps", 
                    "requirement",
                    "gherkin"
                ])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"]:
                cases = result["data"]["Get"]["TestCase"]
                self.logger.info(f"✅ Found {len(cases)} test cases matching query")
                return cases

            return []

        except Exception as e:
            self.logger.error(f"❌ Search error: {str(e)}")
            return []

    def get_test_case(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a test case by name"""
        if not self.is_healthy():
            self.logger.error("❌ Weaviate client not healthy")
            return None

        try:
            result = (
                self.client.query
                .get("TestCase", [
                    "name", 
                    "objective", 
                    "precondition", 
                    "steps", 
                    "requirement",
                    "gherkin"
                ])
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
                    self.logger.info(f"Found test case: {name}")
                    return cases[0]

            self.logger.warning(f"No test case found with name: {name}")
            return None

        except Exception as e:
            self.logger.error(f"Error retrieving test case: {str(e)}")
            return None