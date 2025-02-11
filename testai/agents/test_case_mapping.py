"""TestCaseMappingAgent implementation for generating formatted test cases."""
from typing import Dict, List, Optional, Any
import logging
from pydantic import BaseModel
import weaviate
from weaviate.util import generate_uuid5

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

        # Initialize Weaviate client with v4 API
        try:
            self.weaviate_client = weaviate.WeaviateClient(
                connection_params=weaviate.connect.ConnectionParams.from_url(
                    url="http://localhost:8080",
                    grpc_port=50051
                )
            )
        except Exception as e:
            logging.warning(f"Weaviate initialization warning: {str(e)}")
            self.weaviate_client = None

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

            # Analyze the requirement text for login-specific details
            is_login = "login" in requirement.lower()
            if is_login:
                test_case = self._generate_login_test_case(requirement)
            else:
                test_case = self._generate_generic_test_case(requirement)

            # Convert to dict and structure the response
            test_case_dict = test_case.model_dump()

            # Store in Weaviate
            self._store_in_weaviate(test_case_dict)

            # Store in Zephyr Scale (mock for now)
            self._store_in_zephyr(test_case_dict)

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

    def _generate_login_test_case(self, requirement: str) -> TestCaseOutput:
        """Generate a login-specific test case"""
        return TestCaseOutput(
            title="Test: Login Functionality",
            description=requirement,
            format=TestCaseFormat(
                given=[
                    "User is on the login page",
                    "User has valid credentials",
                    "The system is accessible"
                ],
                when=[
                    "User enters their username/email",
                    "User enters their password",
                    "User clicks the login button"
                ],
                then=[
                    "User is successfully logged in",
                    "User is redirected to the dashboard",
                    "Welcome message is displayed with user's name"
                ],
                tags=["authentication", "login", "critical-path", "smoke-test"],
                priority="high"
            ),
            metadata={
                "source": "requirement",
                "type": "authentication",
                "created_at": "2025-02-11",
                "requirement_text": requirement
            }
        )

    def _generate_generic_test_case(self, requirement: str) -> TestCaseOutput:
        """Generate a generic test case"""
        return TestCaseOutput(
            title=f"Test: {requirement[:50]}",
            description=requirement,
            format=TestCaseFormat(
                given=[
                    "User is logged into the system",
                    "Required permissions are granted",
                    "System is in a known good state"
                ],
                when=[
                    "User navigates to the required page",
                    "User performs the necessary actions",
                    "User submits the changes"
                ],
                then=[
                    "Operation completes successfully",
                    "Expected results are verified",
                    "System state is updated correctly"
                ],
                tags=["functional", "regression"],
                priority="medium"
            ),
            metadata={
                "source": "requirement",
                "created_at": "2025-02-11",
                "requirement_text": requirement
            }
        )

    def _store_in_weaviate(self, test_case: Dict[str, Any]) -> None:
        """Store test case in Weaviate vector database"""
        try:
            if self.weaviate_client:
                uuid = generate_uuid5(test_case["title"])
                properties = {
                    "title": test_case["title"],
                    "description": test_case["description"],
                    "steps": {
                        "given": test_case["format"]["given"],
                        "when": test_case["format"]["when"],
                        "then": test_case["format"]["then"]
                    },
                    "tags": test_case["format"]["tags"],
                    "metadata": test_case["metadata"]
                }
                self.weaviate_client.data.create(
                    uuid=uuid,
                    class_name="TestCase",
                    properties=properties
                )
                logging.info(f"Test case stored in Weaviate: {test_case['title']}")
        except Exception as e:
            logging.error(f"Error storing in Weaviate: {str(e)}")

    def _store_in_zephyr(self, test_case: Dict[str, Any]) -> None:
        """Store test case in Zephyr Scale (mock implementation)"""
        try:
            # Mock Zephyr Scale storage for now
            logging.info(f"Test case would be stored in Zephyr Scale: {test_case['title']}")
        except Exception as e:
            logging.error(f"Error storing in Zephyr Scale: {str(e)}")

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "test_cases_generated": len(self.generated_cases),
            "last_test_case": self.generated_cases[-1] if self.generated_cases else None
        })
        return status