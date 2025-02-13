"""Mock vector database integration for storing and retrieving test cases."""
import logging
import weaviate
import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class TestCase(BaseModel):
    """Test case model for Weaviate storage"""
    name: str
    objective: str
    precondition: str
    steps: List[Dict[str, str]]
    automation_needed: str = "TBD"

class WeaviateIntegration:
    """Mock implementation of vector database integration"""

    def __init__(self):
        """Initialize mock storage"""
        self.client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL", "http://localhost:8080"),
            auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),
        )
        self._create_schema()
        logging.info("Mock vector database initialized")

    def _create_schema(self):
        """Create the test case schema in Weaviate"""
        schema = {
            "class": "TestCase",
            "properties": [
                {"name": "name", "dataType": ["text"]},
                {"name": "objective", "dataType": ["text"]},
                {"name": "precondition", "dataType": ["text"]},
                {"name": "steps", "dataType": ["text[]"]},
                {"name": "requirement", "dataType": ["text"]},
                {"name": "gherkin", "dataType": ["text"]}
            ],
            "vectorizer": "text2vec-openai"
        }
        try:
            self.client.schema.create_class(schema)
        except Exception:
            pass  # Schema might already exist

    def store_test_case(self, test_case: TestCase, requirement: str, gherkin: str) -> str:
        """Store a test case in Weaviate"""
        properties = {
            "name": test_case.name,
            "objective": test_case.objective,
            "precondition": test_case.precondition,
            "steps": [f"{s['step']}: {s['expected_result']}" for s in test_case.steps],
            "requirement": requirement,
            "gherkin": gherkin
        }
        
        result = self.client.data_object.create(
            data_object=properties,
            class_name="TestCase"
        )
        return result["id"]

    def search_similar_test_cases(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar test cases in mock storage

        Args:
            query: Search query text
            limit: Maximum number of results to return

        Returns:
            List of similar test cases
        """
        try:
            logging.info(f"Searching for test cases with query: {query}")
            logging.info(f"Total test cases available: {len(self.test_cases)}")

            # Simple text-based search in mock implementation
            matched_cases = []
            query = query.lower()

            for case in self.test_cases:
                try:
                    if (query in case["title"].lower() or 
                        query in case["description"].lower() or 
                        any(query in step.lower() for step in case["format"]["given"] + 
                            case["format"]["when"] + case["format"]["then"])):
                        logging.info(f"Found matching test case: {case['title']}")
                        matched_cases.append(case)

                    if len(matched_cases) >= limit:
                        break
                except KeyError as ke:
                    logging.warning(f"Malformed test case in storage: {ke}")
                    continue

            logging.info(f"Found {len(matched_cases)} matching test cases")
            return matched_cases
        except Exception as e:
            logging.error(f"Error searching test cases: {str(e)}")
            return []

    def search_by_requirement(self, query: str, limit: int = 5) -> List[Dict]:
        """Search test cases by requirement text"""
        result = (
            self.client.query
            .get("TestCase", ["name", "objective", "gherkin", "requirement"])
            .with_near_text({"concepts": [query]})
            .with_limit(limit)
            .do()
        )
        return result["data"]["Get"]["TestCase"]