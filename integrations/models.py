"""Models for integrations."""
from typing import Dict, List, Optional
from pydantic import BaseModel

class TestFormat(BaseModel):
    """Format for test steps in Given/When/Then format"""
    given: List[str]
    when: List[str]
    then: List[str]

class TestCase(BaseModel):
    """Test case data model"""
    name: str
    objective: str
    precondition: str
    steps: List[str]
    requirement: str
    gherkin: str
    format: Optional[TestFormat] = None

    def to_weaviate_format(self) -> Dict:
        """Convert to Weaviate data format"""
        return {
            "name": self.name,
            "objective": self.objective,
            "precondition": self.precondition,
            "steps": self.steps,
            "requirement": self.requirement,
            "gherkin": self.gherkin,
            "format": self.format.dict() if self.format else None
        }

class TestSuite(BaseModel):
    """Test suite model"""
    name: str
    description: str
    test_cases: List[TestCase]