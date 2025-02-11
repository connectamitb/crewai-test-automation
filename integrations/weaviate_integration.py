"""Weaviate integration for storing and retrieving test cases."""
import os
from typing import Dict, List, Any, Optional
import weaviate
from weaviate.auth import AuthApiKey
from pydantic import BaseModel

class TestCase(BaseModel):
    """Test case model with required fields"""
    name: str
    objective: str
    precondition: str
    automation_needed: str  # Values: Yes/No/TBD
    steps: List[Dict[str, str]]  # List of {step, test_data, expected_result}

class WeaviateIntegration:
    """Handles interaction with Weaviate vector database"""

    def __init__(self):
        """Initialize Weaviate client with configuration"""
        try:
            # Create auth config
            auth_config = AuthApiKey(
                api_key=os.environ.get('WEAVIATE_API_KEY', "SmLT0gm7xrJSWeBt2zaX0UE3EU9s6zC5lmub")
            )

            # Initialize connection parameters
            connection_params = weaviate.connect.ConnectionParams.from_params(
                http_host="mtkcafmlsuso0nc3pcaujg.c0.us-west3.gcp.weaviate.cloud",
                http_port=443,
                http_secure=True,
                grpc_host="grpc-mtkcafmlsuso0nc3pcaujg.c0.us-west3.gcp.weaviate.cloud",
                grpc_port=443,
                grpc_secure=True
            )

            # Connect to Weaviate with authentication
            self.client = weaviate.WeaviateClient(
                connection_params=connection_params,
                auth_client_secret=auth_config
            )

            # Explicitly connect the client
            self.client.connect()
            print("Successfully connected to Weaviate")

            # Ensure schema exists
            self._ensure_schema()

        except Exception as e:
            print(f"Error connecting to Weaviate: {str(e)}")
            raise

    def _ensure_schema(self):
        """Ensure the required schema exists in Weaviate"""
        try:
            # Check if class exists
            collection = self.client.collections.get("TestCase")
            if collection is None:
                # Create the class if it doesn't exist
                collection = self.client.collections.create(
                    name="TestCase",
                    description="Test case with requirements and steps",
                    vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_openai(),
                    properties=[
                        weaviate.classes.properties.Property(
                            name="name",
                            data_type=weaviate.classes.properties.DataType.TEXT,
                            description="Name of the test case"
                        ),
                        weaviate.classes.properties.Property(
                            name="objective",
                            data_type=weaviate.classes.properties.DataType.TEXT,
                            description="Test case objective"
                        ),
                        weaviate.classes.properties.Property(
                            name="precondition",
                            data_type=weaviate.classes.properties.DataType.TEXT,
                            description="Preconditions for the test case"
                        ),
                        weaviate.classes.properties.Property(
                            name="automationNeeded",
                            data_type=weaviate.classes.properties.DataType.TEXT,
                            description="Whether automation is needed (Yes/No/TBD)"
                        ),
                        weaviate.classes.properties.Property(
                            name="steps",
                            data_type=weaviate.classes.properties.DataType.TEXT_ARRAY,
                            description="Test steps with data and expected results"
                        )
                    ]
                )
                print("Created TestCase collection")
        except Exception as e:
            print(f"Error ensuring schema: {str(e)}")
            raise

    def store_test_case(self, test_case: TestCase) -> str:
        """Store a test case in Weaviate

        Args:
            test_case: TestCase object to store

        Returns:
            str: ID of the stored test case
        """
        # Convert steps to string array for storage
        steps_str = [
            f"Step: {step['step']}\nTest Data: {step['test_data']}\nExpected Result: {step['expected_result']}"
            for step in test_case.steps
        ]

        try:
            # Ensure client is connected
            if not self.client.is_connected():
                self.client.connect()

            # Create data object
            collection = self.client.collections.get("TestCase")
            if collection is None:
                raise Exception("TestCase collection not found")

            result = collection.data.insert({
                "name": test_case.name,
                "objective": test_case.objective,
                "precondition": test_case.precondition,
                "automationNeeded": test_case.automation_needed,
                "steps": steps_str
            })

            # For v4 client, the UUID is returned directly
            return str(result)

        except Exception as e:
            raise Exception(f"Failed to store test case: {str(e)}")

    def search_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using semantic search

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching test cases
        """
        try:
            # Ensure client is connected
            if not self.client.is_connected():
                self.client.connect()

            collection = self.client.collections.get("TestCase")
            if collection is None:
                raise Exception("TestCase collection not found")

            results = (collection.query
                .near_text(query)
                .with_limit(limit)
                .with_fields("name objective precondition automationNeeded steps")
                .do()
            )

            return results.objects

        except Exception as e:
            raise Exception(f"Failed to search test cases: {str(e)}")

    def get_test_case_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a test case by its name

        Args:
            name: Name of the test case to retrieve

        Returns:
            Test case data if found, None otherwise
        """
        try:
            # Ensure client is connected
            if not self.client.is_connected():
                self.client.connect()

            collection = self.client.collections.get("TestCase")
            if collection is None:
                raise Exception("TestCase collection not found")

            results = (collection.query
                .with_where({
                    "path": ["name"],
                    "operator": "Equal",
                    "valueString": name
                })
                .with_fields("name objective precondition automationNeeded steps")
                .do()
            )

            if results.objects:
                return results.objects[0]
            return None

        except Exception as e:
            raise Exception(f"Failed to retrieve test case: {str(e)}")