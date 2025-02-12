"""NLPParsingAgent for extracting structured test details."""
import logging
from typing import List, Dict
from pydantic import BaseModel
from agents.requirement_input import CleanedRequirement

class TestStep(BaseModel):
    """Model for a structured test step"""
    step: str
    test_data: str
    expected_result: str

class ParsedTestCase(BaseModel):
    """Model for parsed test case details"""
    name: str
    objective: str
    precondition: str
    automation_needed: str
    steps: List[Dict[str, str]]

class NLPParsingAgent:
    """Agent for parsing cleaned requirements into structured test cases"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_requirement(self, requirement: CleanedRequirement) -> ParsedTestCase:
        """Parse cleaned requirement into structured test case"""
        try:
            # Create test steps from acceptance criteria
            steps = []
            for criteria in requirement.acceptance_criteria:
                # Split criteria into steps if it contains multiple actions
                test_step = {
                    "step": criteria,
                    "test_data": "TBD",  # To be enhanced with actual test data extraction
                    "expected_result": criteria  # Using criteria as initial expected result
                }
                steps.append(test_step)
            
            # Determine if automation is needed based on complexity
            automation_needed = "Yes" if len(steps) > 2 else "TBD"
            
            # Create precondition string from prerequisites
            precondition = "\n".join(requirement.prerequisites) if requirement.prerequisites else ""
            
            return ParsedTestCase(
                name=requirement.title,
                objective=requirement.description,
                precondition=precondition,
                automation_needed=automation_needed,
                steps=steps
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing requirement: {str(e)}")
            raise
