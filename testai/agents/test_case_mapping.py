"""TestCaseMappingAgent implementation for generating formatted test cases."""
import os
import logging
from typing import Dict, List, Optional, Any
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
    priority: str = "Normal"

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
        self.logger = logging.getLogger(__name__)
        self.generated_cases = []
        self.zephyr_api_key = os.environ.get("ZEPHYR_API_KEY")
        self.zephyr_project_key = os.environ.get("ZEPHYR_PROJECT_KEY", "QADEMO")
        self.zephyr_base_url = "https://api.zephyrscale.smartbear.com/v2/testcases"

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test case mapping task"""
        try:
            self.logger.debug(f"Received task: {task}")

            # Extract requirement from task
            requirement = task.get('requirement')
            if not requirement:
                raise ValueError("Requirement data is required")

            # Create test case based on requirement
            if isinstance(requirement, dict):
                # If requirement is already structured
                test_case = TestCaseOutput(
                    title=requirement.get('title', 'Untitled Test Case'),
                    description=requirement.get('description', ''),
                    format=TestCaseFormat(
                        given=requirement.get('format', {}).get('given', []),
                        when=requirement.get('format', {}).get('when', []),
                        then=requirement.get('format', {}).get('then', []),
                        tags=requirement.get('format', {}).get('tags', []),
                        priority=requirement.get('format', {}).get('priority', 'Normal')
                    )
                )
            else:
                # If requirement is a string or other format
                is_login = "login" in str(requirement).lower()
                test_case = self._generate_login_test_case(requirement) if is_login else self._generate_generic_test_case(requirement)

            # Convert to dict for response
            test_case_dict = test_case.model_dump()
            self.logger.debug(f"Generated test case: {test_case_dict}")

            # Store locally for search
            self.generated_cases.append(test_case_dict)

            # Store in Zephyr Scale if available
            zephyr_result = self._store_in_zephyr(test_case_dict)
            storage_info = {"memory": True, "zephyr": bool(zephyr_result)}

            return {
                "status": "success",
                "test_case": test_case_dict,
                "storage": storage_info
            }

        except Exception as e:
            self.logger.error(f"Error in test case mapping: {str(e)}", exc_info=True)
            raise

    def _store_in_zephyr(self, test_case: Dict[str, Any]) -> bool:
        """Store test case in Zephyr Scale"""
        try:
            if not self.zephyr_api_key:
                self.logger.warning("ZEPHYR_API_KEY not set, skipping Zephyr storage")
                return False

            headers = {
                "Authorization": f"Bearer {self.zephyr_api_key}",
                "Content-Type": "application/json"
            }

            # Format steps for Zephyr Scale
            steps = []
            for when_step, then_step in zip(
                test_case["format"]["when"],
                test_case["format"]["then"]
            ):
                steps.append({
                    "description": when_step,
                    "expectedResult": then_step,
                    "testData": ""
                })

            payload = {
                "projectKey": self.zephyr_project_key,
                "name": test_case["title"],
                "objective": test_case["description"],
                "priorityName": test_case["format"]["priority"].upper(),
                "statusName": "Draft",
                "steps": steps
            }

            # Add preconditions if present
            if test_case["format"]["given"]:
                payload["precondition"] = "\n".join(test_case["format"]["given"])

            # Add labels if present
            if test_case["format"]["tags"]:
                payload["labels"] = test_case["format"]["tags"]

            response = requests.post(
                self.zephyr_base_url,
                headers=headers,
                json=payload
            )

            if response.status_code in (200, 201):
                result = response.json()
                self.logger.info(f"Successfully created test case in Zephyr Scale: {result.get('key')}")
                return True
            else:
                self.logger.error(f"Failed to create test case in Zephyr Scale: {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Error storing test case in Zephyr Scale: {str(e)}")
            return False

    def _generate_login_test_case(self, requirement: str) -> TestCaseOutput:
        """Generate a login-specific test case"""
        return TestCaseOutput(
            title="Test: Login Functionality",
            description=str(requirement),
            format=TestCaseFormat(
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
                ],
                tags=["authentication", "login", "critical-path", "smoke-test"],
                priority="high"
            )
        )

    def _generate_generic_test_case(self, requirement: str) -> TestCaseOutput:
        """Generate a generic test case"""
        return TestCaseOutput(
            title=f"Test: {str(requirement)[:50]}",
            description=str(requirement),
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
            )
        )

    def query_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases in memory"""
        try:
            matched_cases = []
            query = query.lower()

            for case in self.generated_cases:
                score = 0

                # Match title
                if query in case['title'].lower():
                    score += 0.4

                # Match description
                if query in case['description'].lower():
                    score += 0.3

                # Match steps
                steps = case['format']['given'] + case['format']['when'] + case['format']['then']
                if any(query in step.lower() for step in steps):
                    score += 0.3

                if score > 0:
                    matched_cases.append({
                        'test_case': case,
                        'score': score
                    })

            # Sort by score and return top matches
            matched_cases.sort(key=lambda x: x['score'], reverse=True)
            return [x['test_case'] for x in matched_cases[:limit]]

        except Exception as e:
            self.logger.error(f"Error querying test cases: {str(e)}")
            return []

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "test_cases_generated": len(self.generated_cases),
            "last_test_case": self.generated_cases[-1] if self.generated_cases else None
        })
        return status