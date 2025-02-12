"""TestCaseMappingAgent implementation for generating formatted test cases."""
import os
import logging
from typing import Dict, List, Optional, Any
import json
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentConfig
from integrations.weaviate_integration import WeaviateIntegration
from integrations.zephyr_integration import ZephyrIntegration, ZephyrTestCase

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

        # Initialize integrations
        self.weaviate_client = WeaviateIntegration()
        self.zephyr_client = ZephyrIntegration()

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test case mapping task"""
        try:
            self.logger.debug(f"Received task: {task}")

            # Extract requirement from task
            requirement = task.get('requirement')
            if not requirement:
                raise ValueError("Requirement data is required")

            # Create test case based on requirement
            test_case = self._generate_test_case(requirement)
            test_case_dict = test_case.model_dump()
            self.logger.debug(f"Generated test case: {test_case_dict}")

            # Store locally for search
            self.generated_cases.append(test_case_dict)

            # Store in Weaviate
            weaviate_stored = False
            try:
                weaviate_id = self.weaviate_client.store_test_case(test_case_dict)
                weaviate_stored = bool(weaviate_id)
                self.logger.info(f"Stored test case in Weaviate: {weaviate_id}")
            except Exception as e:
                self.logger.error(f"Failed to store in Weaviate: {str(e)}")

            # Store in Zephyr Scale
            zephyr_stored = False
            try:
                # Convert to Zephyr format
                zephyr_test_case = ZephyrTestCase(
                    name=test_case.title,
                    objective=test_case.description,
                    precondition="\n".join(test_case.format.given),
                    steps=[{
                        "step": step,
                        "test_data": "",
                        "expected_result": expected
                    } for step, expected in zip(test_case.format.when, test_case.format.then)],
                    priority=test_case.format.priority,
                    labels=test_case.format.tags
                )

                # Store in Zephyr
                zephyr_key = self.zephyr_client.create_test_case(zephyr_test_case)
                zephyr_stored = bool(zephyr_key)
                self.logger.info(f"Stored test case in Zephyr Scale: {zephyr_key}")
            except Exception as e:
                self.logger.error(f"Failed to store in Zephyr Scale: {str(e)}")

            storage_info = {
                "memory": True,
                "weaviate": weaviate_stored,
                "zephyr": zephyr_stored
            }

            return {
                "status": "success",
                "test_case": test_case_dict,
                "storage": storage_info
            }

        except Exception as e:
            self.logger.error(f"Error in test case mapping: {str(e)}", exc_info=True)
            raise

    def _generate_test_case(self, requirement: str) -> TestCaseOutput:
        """Generate a test case based on requirement"""
        is_login = "login" in str(requirement).lower()
        return self._generate_login_test_case(requirement) if is_login else self._generate_generic_test_case(requirement)

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
        """Search for test cases in memory and vector database"""
        try:
            self.logger.info(f"🔍 Starting search for query: {query}")
            matched_cases = []

            # Search in Weaviate
            try:
                self.logger.info("📊 Attempting Weaviate search...")
                weaviate_results = self.weaviate_client.search_test_cases(query, limit)
                if weaviate_results:
                    self.logger.info(f"✅ Found {len(weaviate_results)} results in Weaviate")
                    matched_cases.extend(weaviate_results)
                else:
                    self.logger.warning("⚠️ No results found in Weaviate")
            except Exception as e:
                self.logger.error(f"❌ Error searching Weaviate: {str(e)}", exc_info=True)

            # Search in memory as backup
            self.logger.info("🔄 Searching in memory cache...")
            memory_results = self._search_memory(query, limit)
            if memory_results:
                self.logger.info(f"✅ Found {len(memory_results)} results in memory")
                matched_cases.extend(memory_results)
            else:
                self.logger.warning("⚠️ No results found in memory")

            # Deduplicate by title
            seen_titles = set()
            unique_cases = []
            for case in matched_cases:
                title = case.get('title', '')
                if title not in seen_titles:
                    seen_titles.add(title)
                    unique_cases.append(case)

            self.logger.info(f"✅ Returning {len(unique_cases)} unique test cases")
            return unique_cases[:limit]

        except Exception as e:
            self.logger.error(f"❌ Error querying test cases: {str(e)}", exc_info=True)
            return []

    def _search_memory(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search for test cases in memory"""
        matched_cases = []
        query = query.lower()

        for case in self.generated_cases:
            score = 0
            title = case.get('title', '').lower()
            desc = case.get('description', '').lower()

            if query in title:
                score += 0.4
            if query in desc:
                score += 0.3

            if case.get('format'):
                steps = (
                    case['format'].get('given', []) +
                    case['format'].get('when', []) +
                    case['format'].get('then', [])
                )
                if any(query in step.lower() for step in steps):
                    score += 0.3

            if score > 0:
                matched_cases.append({
                    'test_case': case,
                    'score': score
                })

        matched_cases.sort(key=lambda x: x['score'], reverse=True)
        return [x['test_case'] for x in matched_cases[:limit]]

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "test_cases_generated": len(self.generated_cases),
            "last_test_case": self.generated_cases[-1] if self.generated_cases else None
        })
        return status