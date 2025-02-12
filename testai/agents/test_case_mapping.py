"""TestCaseMappingAgent implementation for generating formatted test cases."""
import os
import logging
from typing import Dict, List, Optional, Any
import json
import requests
from pydantic import BaseModel
from itertools import zip_longest
from integrations.weaviate_integration import WeaviateIntegration, TestCase

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
        self.generated_cases = []
        self.zephyr_api_key = os.environ.get("ZEPHYR_API_KEY")
        self.zephyr_project_key = os.environ.get("ZEPHYR_PROJECT_KEY", "QADEMO")
        self.zephyr_base_url = "https://api.zephyrscale.smartbear.com/v2/testcases"

        # Initialize vector database integration
        try:
            self.vector_db = WeaviateIntegration()
            logging.info("Successfully initialized Weaviate integration")
        except Exception as e:
            logging.error(f"Failed to initialize Weaviate integration: {str(e)}")
            self.vector_db = None

    def query_test_cases(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases using semantic search with fallback"""
        try:
            # Try vector search first
            if self.vector_db:
                similar_cases = self.vector_db.search_test_cases(query, limit)
                if similar_cases:
                    logging.info(f"Found {len(similar_cases)} test cases using vector search")
                    return similar_cases

            # Fallback to in-memory search
            return self._in_memory_search(query, limit)

        except Exception as e:
            logging.error(f"Error querying test cases: {str(e)}")
            return self._in_memory_search(query, limit)

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test case mapping task"""
        try:
            # Generate or use provided test case
            if isinstance(task, TestCaseOutput):
                test_case = task
            else:
                requirement = task.get('requirement')
                if not requirement:
                    raise ValueError("Requirement data is required")

                is_login = "login" in requirement.lower()
                test_case = self._generate_login_test_case(requirement) if is_login else self._generate_generic_test_case(requirement)

            # Convert to dict for storage
            test_case_dict = test_case.model_dump()

            # Store in memory for local search
            self.generated_cases.append(test_case_dict)
            logging.info(f"Stored test case in memory: {test_case_dict['title']}")

            # Store in Zephyr Scale
            zephyr_result = self._store_in_zephyr(test_case_dict)
            if zephyr_result:
                logging.info(f"Successfully stored test case in Zephyr Scale: {test_case_dict['title']}")
            else:
                logging.warning(f"Failed to store test case in Zephyr Scale: {test_case_dict['title']}")

            # Store in vector database
            if self.vector_db:
                try:
                    # Convert to TestCase model for Weaviate
                    weaviate_test_case = TestCase(
                        name=test_case_dict["title"],
                        objective=test_case_dict["description"],
                        precondition="\n".join(test_case_dict["format"]["given"]),
                        automation_needed="Yes",
                        steps=[{
                            "step": step,
                            "test_data": "",
                            "expected_result": expected
                        } for step, expected in zip_longest(
                            test_case_dict["format"]["when"],
                            test_case_dict["format"]["then"],
                            fillvalue=""
                        )]
                    )
                    self.vector_db.store_test_case(weaviate_test_case)
                    logging.info(f"Successfully stored test case in vector database: {test_case_dict['title']}")
                except Exception as e:
                    logging.error(f"Failed to store test case in vector database: {str(e)}")

            return {
                "status": "success",
                "test_case": test_case_dict,
                "storage": {
                    "memory": True,
                    "zephyr": bool(zephyr_result),
                    "vector_db": self.vector_db is not None
                }
            }

        except Exception as e:
            logging.error(f"Error in test case mapping task: {str(e)}")
            raise

    def _in_memory_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform in-memory search when vector search is unavailable"""
        try:
            matches = []
            query_terms = [term.lower() for term in query.split() 
                         if len(term) > 2 and term.lower() not in {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'test', 'case'}]

            if not query_terms:
                return []

            for case in self.generated_cases:
                score = 0
                title_lower = case["title"].lower()
                desc_lower = case["description"].lower()

                # Title matching (highest weight)
                title_matches = sum(1 for term in query_terms if term in title_lower)
                if title_matches:
                    score += 0.8 * (title_matches / len(query_terms))

                # Description matching
                desc_matches = sum(1 for term in query_terms if term in desc_lower)
                if desc_matches:
                    score += 0.5 * (desc_matches / len(query_terms))

                # Consider significant matches only
                if score > 0.3:
                    matches.append({
                        "test_case": case,
                        "score": min(score, 1.0)
                    })

            matches.sort(key=lambda x: x["score"], reverse=True)
            return matches[:limit]

        except Exception as e:
            logging.error(f"Error in memory search: {str(e)}")
            return []

    def _store_in_zephyr(self, test_case: Dict[str, Any]) -> bool:
        """Store test case in Zephyr Scale"""
        try:
            # Verify credentials
            if not self.zephyr_api_key:
                logging.error("ZEPHYR_API_KEY environment variable is not set")
                return False

            # Format test case for Zephyr Scale API
            zephyr_test_case = {
                "projectKey": self.zephyr_project_key,
                "name": test_case["title"],
                "objective": test_case["description"],
                "priorityName": test_case["format"]["priority"].upper(),
                "statusName": "Draft",
                "customFields": {
                    "Automation": "TBD"
                }
            }

            # Add preconditions (Given)
            if test_case["format"]["given"]:
                zephyr_test_case["precondition"] = "\n".join(test_case["format"]["given"])

            # Combine when and then steps
            steps = []
            for step, expected in zip_longest(
                test_case["format"].get("when", []), 
                test_case["format"].get("then", [])
            ):
                steps.append({
                    "description": step if step else "",
                    "expectedResult": expected if expected else "",
                    "testData": ""
                })
            zephyr_test_case["steps"] = steps

            # Add labels if tags exist
            if test_case["format"].get("tags"):
                zephyr_test_case["labels"] = test_case["format"]["tags"]

            # Prepare headers
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
            logging.error(f"Error in Zephyr Scale integration: {str(e)}")
            return False

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
                "created_at": "2025-02-12",
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
                "created_at": "2025-02-12",
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