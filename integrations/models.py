"""Models for integrations."""
from typing import Dict, List, Optional
from pydantic import BaseModel

class TestStep(BaseModel):
    """Model for a test step"""
    step: str
    test_data: Optional[str] = None
    expected_result: str

class WeaviateTestCase(BaseModel):
    """Test case model with format matching Weaviate schema"""
    title: str
    description: str
    format: Dict[str, List[str]]  # Contains given/when/then lists
    metadata: Optional[Dict] = None

class TestCase(WeaviateTestCase):
    """Test case model with full functionality"""
    given: List[str]
    when: List[str]
    then: List[str]
    tags: Optional[List[str]] = None
    priority: str = "Normal"

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
                "given": self.given,
                "when": self.when,
                "then": self.then
            },
            "metadata": metadata
        }

class TestSuite(BaseModel):
    """Test suite model"""
    name: str
    description: str
    test_cases: List[TestCase]