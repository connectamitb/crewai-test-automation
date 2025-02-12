"""Models for integrations."""
from typing import Dict, List, Optional
from pydantic import BaseModel

class TestCase(BaseModel):
    """Test case model with required fields"""
    name: str
    objective: str
    precondition: str
    automation_needed: str  # Values: Yes/No/TBD
    steps: List[Dict[str, str]]  # List of {step, test_data, expected_result}

class TestSuite(BaseModel):
    """Test suite model"""
    name: str
    description: str
    test_cases: List[TestCase]
