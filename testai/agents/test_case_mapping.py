"""TestCaseMappingAgent implementation for generating formatted test cases."""
from typing import Dict, List, Optional, Any
import logging
import os
import json
import requests
from pydantic import BaseModel
from itertools import zip_longest

from .base_agent import BaseAgent, AgentConfig

class TestCaseFormat(BaseModel):
    """Model for test case format"""
    given: List[str]
    when: List[str]
    then: List[str]
    tags: Optional[List[str]] = None
    priority: str = "Normal"  # Updated to use Zephyr Scale's standard priority

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

    def search_test_cases(self, query: str = None, labels: List[str] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases in Zephyr Scale

        Args:
            query: Optional search query text
            labels: Optional list of labels to filter by
            max_results: Maximum number of results to return (default: 10)

        Returns:
            List of matching test cases
        """
        try:
            if not self.zephyr_api_key:
                logging.error("ZEPHYR_API_KEY environment variable is not set")
                return []

            # Construct search URL with query parameters
            search_url = f"{self.zephyr_base_url}"
            params = {
                "projectKey": self.zephyr_project_key,
                "maxResults": max_results
            }

            if query:
                params["text"] = query
            if labels:
                params["label"] = labels

            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.zephyr_api_key}",
                "Accept": "application/json"
            }

            # Make the search request
            logging.info(f"Searching test cases with params: {params}")
            response = requests.get(search_url, headers=headers, params=params)

            if response.status_code == 200:
                results = response.json()
                logging.info(f"Found {len(results)} test cases")

                # Format results
                formatted_results = []
                for test_case in results:
                    formatted_case = {
                        "key": test_case.get("key"),
                        "name": test_case.get("name"),
                        "objective": test_case.get("objective"),
                        "priority": test_case.get("priorityName"),
                        "labels": test_case.get("labels", []),
                        "steps": len(test_case.get("script", {}).get("steps", [])) if test_case.get("script") else 0
                    }
                    formatted_results.append(formatted_case)

                return formatted_results
            else:
                logging.error(f"Failed to search test cases. Status: {response.status_code}")
                logging.error(f"Error response: {response.text}")
                return []

        except Exception as e:
            logging.error(f"Error searching test cases: {str(e)}")
            return []

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
            steps = []
            step_number = 1

            # Convert Given steps
            for given_step in test_case["format"]["given"]:
                steps.append({
                    "index": step_number,
                    "description": f"GIVEN: {given_step}",
                    "testData": "",
                    "expectedResult": "Precondition is satisfied"
                })
                step_number += 1

            # Convert When steps
            for when_step in test_case["format"]["when"]:
                steps.append({
                    "index": step_number,
                    "description": f"WHEN: {when_step}",
                    "testData": self._generate_test_data(when_step, step_number),
                    "expectedResult": ""  # Will be paired with Then steps
                })
                step_number += 1

            # Convert Then steps
            then_steps = test_case["format"]["then"]
            for i, then_step in enumerate(then_steps):
                # Find the corresponding When step if available
                when_step_index = i + len(test_case["format"]["given"])
                if when_step_index < len(steps):
                    # Update the expected result of the corresponding When step
                    steps[when_step_index]["expectedResult"] = f"THEN: {then_step}"
                else:
                    # Add as a separate verification step
                    steps.append({
                        "index": step_number,
                        "description": f"Verify: {then_step}",
                        "testData": "",
                        "expectedResult": f"THEN: {then_step}"
                    })
                    step_number += 1

            zephyr_test_case = {
                "projectKey": self.zephyr_project_key,
                "name": test_case["title"],
                "objective": test_case["description"],
                "priorityName": test_case["format"]["priority"],
                "statusName": "Draft",
                "labels": test_case["format"].get("tags", []),
                "customFields": {
                    "Automation": "TBD"
                },
                "script": {
                    "type": "STEP_BY_STEP",
                    "steps": steps
                }
            }

            # Add preconditions (Given) as a summary
            if test_case["format"]["given"]:
                zephyr_test_case["precondition"] = "Prerequisites:\n" + "\n".join([
                    f"- {step}" for step in test_case["format"]["given"]
                ])

            # Log the formatted request payload
            logging.info(f"Sending request to Zephyr Scale with data: {json.dumps(zephyr_test_case, indent=2)}")

            # Prepare headers with bearer token
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

        except Exception as e:
            logging.error(f"Error in Zephyr Scale integration: {str(e)}")
            return False

    def _generate_test_data(self, step: str, index: int) -> str:
        """Generate appropriate test data based on step description"""
        step_lower = step.lower()
        if "username" in step_lower or "email" in step_lower:
            return "testuser@example.com"
        elif "password" in step_lower:
            return "TestPassword123!"
        elif "date" in step_lower:
            return "2025-02-12"
        elif "number" in step_lower:
            return f"TEST{index:03d}"
        else:
            return f"Test data for step {index}"

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
                    "Username field accepts the input",
                    "Password field accepts the input",
                    "User is successfully logged in and redirected to the dashboard"
                ],
                tags=["authentication", "login", "critical-path", "smoke-test"],
                priority="Normal"
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
            title=f"Test: {requirement[:50]}...",
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
                priority="Normal"
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