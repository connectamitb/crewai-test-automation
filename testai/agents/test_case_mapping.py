"""TestCaseMappingAgent implementation for generating formatted test cases."""
from typing import Dict, List, Optional, Any
import logging
import os
import json
import requests
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
        self.zephyr_api_key = os.environ.get("ZEPHYR_API_KEY")
        self.zephyr_project_key = os.environ.get("ZEPHYR_PROJECT_KEY", "QADEMO")
        # Updated base URL to use the correct endpoint
        self.zephyr_base_url = "https://api.zephyrscale.smartbear.com/v2/testcases"

    def _store_in_zephyr(self, test_case: Dict[str, Any]) -> bool:
        """Store test case in Zephyr Scale

        Args:
            test_case: Test case data to store

        Returns:
            bool indicating success
        """
        try:
            # Verify credentials
            if not self.zephyr_api_key:
                logging.error("ZEPHYR_API_KEY environment variable is not set")
                return False

            logging.info(f"Using Zephyr Scale project key: {self.zephyr_project_key}")
            logging.info(f"Using Zephyr Scale API URL: {self.zephyr_base_url}")

            # Format test case for Zephyr Scale API
            zephyr_test_case = {
                "projectKey": self.zephyr_project_key,
                "name": test_case["title"],
                "objective": test_case["description"],
                "priorityName": test_case["format"]["priority"].upper(),
                "statusName": "Draft"
            }

            # Add preconditions (Given)
            if test_case["format"]["given"]:
                zephyr_test_case["precondition"] = "\n".join(test_case["format"]["given"])

            # Add test steps (When + Then)
            steps = []
            for step, expected in zip(test_case["format"]["when"], test_case["format"]["then"]):
                steps.append({
                    "description": step,
                    "expectedResult": expected,
                    "testData": ""
                })
            zephyr_test_case["steps"] = steps

            # Add labels if tags exist
            if test_case["format"].get("tags"):
                zephyr_test_case["labels"] = test_case["format"]["tags"]

            # Log the request details
            logging.info(f"Sending request to Zephyr Scale with data: {json.dumps(zephyr_test_case, indent=2)}")

            # Prepare headers - Using API key as bearer token
            headers = {
                "Authorization": f"Bearer {self.zephyr_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # Make the API request
            response = requests.post(
                self.zephyr_base_url,
                headers=headers,
                json=zephyr_test_case
            )

            # Log response details
            logging.info(f"Zephyr Scale API Response Status: {response.status_code}")
            logging.info(f"Zephyr Scale API Response Headers: {dict(response.headers)}")
            logging.info(f"Zephyr Scale API Response Body: {response.text}")

            if response.status_code in (200, 201):
                response_data = response.json()
                test_case_key = response_data.get('key', 'unknown')
                logging.info(f"Successfully created test case in Zephyr Scale with key: {test_case_key}")
                return True
            else:
                logging.error(f"Failed to create test case in Zephyr Scale. Status: {response.status_code}")
                logging.error(f"Error response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while calling Zephyr Scale API: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error in Zephyr Scale integration: {str(e)}")
            return False

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

            # Store in Zephyr Scale
            zephyr_result = self._store_in_zephyr(test_case_dict)
            if zephyr_result:
                logging.info(f"Test case successfully stored in Zephyr Scale: {test_case_dict['title']}")
            else:
                logging.warning(f"Failed to store test case in Zephyr Scale: {test_case_dict['title']}")

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

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "test_cases_generated": len(self.generated_cases),
            "last_test_case": self.generated_cases[-1] if self.generated_cases else None
        })
        return status