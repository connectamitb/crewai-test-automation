"""Models for integrations."""
from typing import Dict, List, Optional
from pydantic import BaseModel

class TestStep(BaseModel):
    """Model for a test step"""
    step: str
    test_data: Optional[str] = None
    expected_result: str

class TestCaseFormat(BaseModel):
    """Model for test case format"""
    given: List[str]
    when: List[str]
    then: List[str]

class TestCase(BaseModel):
    """Test case model with full functionality"""
    title: str
    description: str
    format: TestCaseFormat
    tags: Optional[List[str]] = None
    priority: str = "Normal"
    metadata: Optional[Dict] = None

    def to_weaviate_format(self) -> Dict:
        """Convert to Weaviate-compatible format"""
        metadata = {}
        if self.metadata:
            metadata.update(self.metadata)
        metadata.update({
            "tags": self.tags,
            "priority": self.priority
        })

        return {
            "title": self.title,
            "description": self.description,
            "format": {
                "given": self.format.given,
                "when": self.format.when,
                "then": self.format.then
            },
            "metadata": metadata
        }

class TestSuite(BaseModel):
    """Test suite model"""
    name: str
    description: str
    test_cases: List[TestCase]