"""Models for integrations."""
from typing import Dict, List, Optional
from pydantic import BaseModel

class TestStep(BaseModel):
    """Model for a test step"""
    step: str
    test_data: Optional[str] = None
    expected_result: str

class TestCase(BaseModel):
    """Test case data model"""
    name: str
    objective: str
    precondition: str
    steps: List[str]
    requirement: str
    gherkin: str

    def to_weaviate_format(self) -> Dict:
        """Convert to Weaviate data format"""
        return {
            "name": self.name,
            "objective": self.objective,
            "precondition": self.precondition,
            "steps": self.steps,
            "requirement": self.requirement,
            "gherkin": self.gherkin
        }

class TestSuite(BaseModel):
    """Test suite model"""
    name: str
    description: str
    test_cases: List[TestCase]