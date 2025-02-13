"""Models for integrations."""
from typing import Dict, List, Optional
from pydantic import BaseModel

class TestStep(BaseModel):
    """Model for a test step"""
    step: str
    test_data: Optional[str] = None
    expected_result: str

class TestCase(BaseModel):
    """Test case model with full functionality"""
    name: str
    objective: str
    precondition: Optional[str] = None
    automation_needed: Optional[str] = "TBD"
    steps: List[Dict[str, str]]
    tags: Optional[List[str]] = None
    priority: str = "Normal"
    metadata: Optional[Dict] = None

    def to_weaviate_format(self) -> Dict:
        """Convert to Weaviate-compatible format"""
        metadata_dict = {
            "tags": self.tags or [],
            "priority": self.priority,
            "automation_needed": self.automation_needed
        }
        if self.metadata:
            metadata_dict.update(self.metadata)

        return {
            "title": self.name,
            "description": self.objective,
            "format": {
                "given": [self.precondition] if self.precondition else [],
                "when": [step["step"] for step in self.steps],
                "then": [step["expected_result"] for step in self.steps]
            },
            "metadata": metadata_dict
        }

class TestSuite(BaseModel):
    """Test suite model"""
    name: str
    description: str
    test_cases: List[TestCase]