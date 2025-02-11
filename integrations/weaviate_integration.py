"""Weaviate integration for storing and retrieving test cases."""
import os
from typing import Dict, List, Any, Optional
import weaviate
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
        self.client = weaviate.Client(
            url="https://mtkcafmlsuso0nc3pcaujg.c0.us-west3.gcp.weaviate.cloud",
            auth_client_secret=weaviate.AuthApiKey(api_key="SmLT0gm7xrJSWeBt2zaX0UE3EU9s6zC5lmub"),
        )
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Ensure the required schema exists in Weaviate"""
        class_obj = {
            "class": "TestCase",
            "description": "Test case with requirements and steps",
            "properties": [
                {
                    "name": "name",
                    "dataType": ["string"],
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
                    "dataType": ["string"],
                    "description": "Whether automation is needed (Yes/No/TBD)"
                },
                {
                    "name": "steps",
                    "dataType": ["text[]"],
                    "description": "Test steps with data and expected results"
                }
            ],
            "vectorizer": "text2vec-openai"
        }
        
        try:
            self.client.schema.create_class(class_obj)
        except weaviate.exceptions.UnexpectedStatusCodeException:
            # Schema might already exist
            pass
    
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
            result = self.client.data_object.create(
                data_object={
                    "name": test_case.name,
                    "objective": test_case.objective,
                    "precondition": test_case.precondition,
                    "automationNeeded": test_case.automation_needed,
                    "steps": steps_str
                },
                class_name="TestCase"
            )
            return result
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
            result = (
                self.client.query
                .get("TestCase", ["name", "objective", "precondition", "automationNeeded", "steps"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            return result.get("data", {}).get("Get", {}).get("TestCase", [])
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
            
            test_cases = result.get("data", {}).get("Get", {}).get("TestCase", [])
            return test_cases[0] if test_cases else None
        except Exception as e:
            raise Exception(f"Failed to retrieve test case: {str(e)}")
