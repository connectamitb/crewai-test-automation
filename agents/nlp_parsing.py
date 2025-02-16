"""NLPParsingAgent for extracting structured test details using OpenAI."""
import logging
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from agents.requirement_input import CleanedRequirement

class TestStep(BaseModel):
    """Model for a single test step"""
    step: str
    test_data: str
    expected_result: str

class ParsedTestCase(BaseModel):
    """Model for parsed test case output"""
    name: str = Field(..., description="Name/title of the test case")
    objective: str = Field(..., description="Test case objective/description")
    precondition: str = Field(default="None", description="Preconditions for the test")
    automation_needed: bool = Field(default=False, description="Whether automation is recommended")
    steps: List[TestStep] = Field(default_factory=list, description="Test steps")
    expected_results: List[str] = Field(default_factory=list, description="Expected results")

    def get_expected_results(self) -> List[str]:
        """Extract expected results from steps"""
        return [step.expected_result for step in self.steps]

class NLPParsingAgent:
    """Agent for parsing cleaned requirements into structured test cases"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_test_case_prompt(self, requirement: CleanedRequirement) -> str:
        """Generate a prompt for OpenAI to create a test case"""
        return f"""Generate a structured test case from the following requirement:

Title: {requirement.title}
Description: {requirement.description}

Prerequisites:
{chr(10).join('- ' + prereq for prereq in requirement.prerequisites)}

Acceptance Criteria:
{chr(10).join('- ' + criteria for criteria in requirement.acceptance_criteria)}

Please provide a structured test case with:
1. A clear test objective
2. Preconditions
3. Step-by-step test procedures with test data
4. Expected results for each step
5. Whether automation is recommended based on complexity

Format your response as JSON with the following structure:
{{
    "name": "string",
    "objective": "string",
    "precondition": "string",
    "automation_needed": boolean,
    "steps": [
        {{
            "step": "string",
            "test_data": "string",
            "expected_result": "string"
        }}
    ]
}}"""

    def parse_requirement(self, requirement: CleanedRequirement) -> ParsedTestCase:
        """Parse cleaned requirement into structured test case using OpenAI"""
        try:
            # Generate prompt for OpenAI
            prompt = self.generate_test_case_prompt(requirement)

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a test case generation expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7  # Add some temperature for creativity while maintaining structure
            )

            # Parse the response
            test_case_data = response.choices[0].message.content.strip()
            self.logger.debug(f"Generated test case data: {test_case_data}")

            # Create ParsedTestCase object
            parsed_case = ParsedTestCase.parse_raw(test_case_data)
            
            # Set expected results from steps
            parsed_case.expected_results = parsed_case.get_expected_results()
            
            self.logger.info(f"Successfully parsed test case: {parsed_case.name}")

            return parsed_case

        except Exception as e:
            self.logger.error(f"Error parsing requirement: {str(e)}")
            raise