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

            # Analyze the requirement text
            words = requirement.lower().split()
            action_words = ["login", "access", "create", "update", "delete", "view"]
            action = next((word for word in words if word in action_words), "perform action")

            # Generate a more specific test case based on the requirement
            test_case = TestCaseOutput(
                title=f"Test: {action.capitalize()} Functionality",
                description=requirement,
                format=TestCaseFormat(
                    given=[
                        "User is on the required page",
                        "System is in a known good state",
                        "Required test data is available"
                    ],
                    when=[
                        f"User initiates the {action} operation",
                        "User provides all required inputs",
                        "User submits the request"
                    ],
                    then=[
                        "Operation completes successfully",
                        "System displays appropriate success message",
                        "Data is properly persisted"
                    ],
                    tags=["automated", "functional", "regression", action],
                    priority="high"
                ),
                metadata={
                    "source": "requirement",
                    "created_at": task.get('timestamp', "2025-02-11"),
                    "version": "1.0",
                    "requirement_text": requirement
                }
            )

            # Convert to dict and structure the response
            test_case_dict = test_case.model_dump()

            # Log successful generation
            logging.info(f"Generated test case: {test_case_dict['title']}")

            self.generated_cases.append(test_case_dict)

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