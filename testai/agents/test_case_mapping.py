"""TestCaseMappingAgent implementation for generating formatted test cases."""
import logging
from typing import Dict, List, Optional, Any

from integrations.models import TestCase, TestCaseFormat
from .base_agent import BaseAgent, AgentConfig
from integrations.weaviate_integration import WeaviateIntegration

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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        try:
            # Initialize Weaviate client
            self.weaviate_client = WeaviateIntegration()
        except Exception as e:
            self.logger.error(f"Failed to initialize Weaviate client: {str(e)}")
            raise RuntimeError(f"Weaviate client initialization failed: {str(e)}")

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test case mapping task"""
        try:
            self.logger.info(f"Received task: {task}")

            # Extract requirement from task
            requirement = task.get('requirement')
            if not requirement:
                raise ValueError("Requirement data is required")

            # Create test case based on requirement
            test_case = self._generate_test_case(requirement)
            test_case_dict = test_case.to_weaviate_format()
            self.logger.debug(f"Generated test case: {test_case_dict}")

            # Store in Weaviate
            try:
                weaviate_id = self.weaviate_client.store_test_case(test_case)
                if not weaviate_id:
                    raise Exception("Failed to store test case in Weaviate")

                self.logger.info(f"Successfully stored test case in Weaviate with ID: {weaviate_id}")
                weaviate_stored = True
            except Exception as e:
                self.logger.error(f"Failed to store in Weaviate: {str(e)}")
                raise Exception(f"Vector database storage failed: {str(e)}")

            # Return result
            return {
                "status": "success",
                "test_case": test_case_dict,
                "storage": {
                    "weaviate": weaviate_stored
                }
            }

        except Exception as e:
            self.logger.error(f"Error in test case mapping: {str(e)}", exc_info=True)
            raise

    def query_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases exclusively in vector database"""
        try:
            self.logger.info(f"Searching for test cases with query: {query}")

            # Search in Weaviate
            results = self.weaviate_client.search_test_cases(query, limit)
            self.logger.info(f"Found {len(results)} test cases in Weaviate")
            self.logger.debug(f"Search results: {results}")
            return results

        except Exception as e:
            self.logger.error(f"Query error: {str(e)}")
            return []

    def _generate_test_case(self, requirement: Dict[str, Any]) -> TestCase:
        """Generate a test case based on requirement"""
        is_login = "login" in str(requirement).lower()
        return self._generate_login_test_case(requirement) if is_login else self._generate_generic_test_case(requirement)

    def _generate_login_test_case(self, requirement: Dict[str, Any]) -> TestCase:
        """Generate a login-specific test case"""
        format = TestCaseFormat(
            given=[
                "User is on the login page",
                "User has valid credentials",
                "System is accessible"
            ],
            when=[
                "User enters valid username",
                "User enters valid password",
                "User clicks the login button"
            ],
            then=[
                "User is successfully authenticated",
                "User is redirected to dashboard",
                "Success message is displayed"
            ]
        )

        return TestCase(
            title="Test: Login Functionality",
            description=str(requirement.get('description', '')),
            format=format,
            tags=["authentication", "login", "critical-path", "smoke-test"],
            priority="high"
        )

    def _generate_generic_test_case(self, requirement: Dict[str, Any]) -> TestCase:
        """Generate a generic test case"""
        format = TestCaseFormat(
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
            ]
        )

        return TestCase(
            title=f"Test: {str(requirement.get('description', ''))[:50]}",
            description=str(requirement.get('description', '')),
            format=format,
            tags=["functional", "regression"],
            priority="medium"
        )

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "weaviate_connected": bool(self.weaviate_client._client)
        })
        return status