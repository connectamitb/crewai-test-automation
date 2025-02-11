"""TestCaseMappingAgent implementation for generating formatted test cases."""
from typing import Dict, List, Optional, Any
import logging
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentConfig

class TestCaseFormat(BaseModel):
    """Model for test case format"""
    given: List[str]
    when: List[str]
    then: List[str]
    tags: Optional[List[str]] = None
    priority: str = "medium"

class TestCaseOutput(BaseModel):
    """Model for complete test case output"""
    title: str
    description: str
    format: TestCaseFormat
    metadata: Optional[Dict[str, Any]] = None

class TestCaseMappingAgent(BaseAgent):
    """Agent responsible for mapping parsed requirements to formatted test cases"""

    def __init__(self):
        """Initialize the test case mapping agent with its configuration"""
        config = AgentConfig(
            agent_id="test_case_mapping_001",
            role="Test Case Designer",
            goal="Generate comprehensive test cases from structured requirements",
            backstory="Expert in test case design and automation",
            verbose=True
        )
        super().__init__(config)
        self.generated_cases = []

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test case mapping task

        Args:
            task: Task containing requirement data

        Returns:
            Dict containing generated test case
        """
        try:
            requirement = task.get('requirement')
            if not requirement:
                raise ValueError("Requirement data is required")

            # Generate a structured test case
            test_case = TestCaseOutput(
                title=f"Test: {requirement[:50]}",
                description=requirement,
                format=TestCaseFormat(
                    given=[
                        "User has valid credentials",
                        "System is accessible",
                        "Required permissions are granted"
                    ],
                    when=[
                        "User submits test requirement",
                        "System processes the input",
                        "Test case is generated"
                    ],
                    then=[
                        "Test case is created successfully",
                        "All required fields are populated",
                        "Test case is stored in the system"
                    ],
                    tags=["automated", "functional", "generated"],
                    priority="high"
                ),
                metadata={
                    "source": "requirement",
                    "created_at": task.get('timestamp', "2025-02-11"),
                    "version": "1.0"
                }
            )

            # Convert to dict and structure the response
            test_case_dict = test_case.model_dump()

            # Log successful generation
            logging.info(f"Generated test case: {test_case_dict['title']}")

            return {
                "status": "success",
                "test_case": test_case_dict
            }

        except Exception as e:
            logging.error(f"Error generating test case: {str(e)}")
            raise

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "test_cases_generated": len(self.generated_cases),
            "last_test_case": self.generated_cases[-1] if self.generated_cases else None
        })
        return status