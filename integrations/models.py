"""Models for integrations."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class TestCase(BaseModel):
    """Test case data model"""
    name: str
    description: str
    requirement: Optional[str] = None
    precondition: Optional[str] = None
    steps: List[str]
    expected_results: List[str]
    priority: Optional[str] = "Medium"
    tags: Optional[List[str]] = []
    automation_status: Optional[str] = "Not Started"
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

    def to_weaviate_format(self) -> dict:
        """Convert to Weaviate data format"""
        return {
            "name": self.name,
            "description": self.description,
            "requirement": self.requirement,
            "precondition": self.precondition,
            "steps": self.steps,
            "expected_results": self.expected_results,
            "priority": self.priority,
            "tags": self.tags,
            "automation_status": self.automation_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }