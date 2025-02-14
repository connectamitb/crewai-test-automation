"""Models for integrations."""
from typing import List, Optional
from pydantic import BaseModel

class TestCase(BaseModel):
    """Simple test case data model"""
    name: str
    description: str
    steps: List[str]
    expected_results: List[str]

    def to_weaviate_format(self) -> dict:
        """Convert to Weaviate data format"""
        return {
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "expectedResults": self.expected_results
        }