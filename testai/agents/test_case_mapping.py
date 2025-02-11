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
            task: Task containing parsed requirement data

        Returns:
            Dict containing generated test case
        """
        try:
            parsed_data = task.get('parsed_requirement')
            if not parsed_data:
                raise ValueError("Parsed requirement data is required")

            self.logger.info("Generating test case from parsed requirement")

            # Generate test case from parsed data
            test_case = self._generate_test_case(parsed_data, task.get('timestamp'))

            # Validate the generated test case
            validation = self._validate_test_case(test_case)

            result = {
                "status": "success",
                "test_case": test_case.model_dump(),
                "validation": validation
            }

            self.generated_cases.append(result)
            self.logger.info(f"Successfully generated test case: {test_case.title}")
            return result

        except Exception as e:
            self.logger.error(f"Error generating test case: {str(e)}")
            raise

    def _generate_test_case(self, parsed_data: Dict[str, Any], timestamp: Optional[str] = None) -> TestCaseOutput:
        """Generate a formatted test case from parsed requirement data

        Args:
            parsed_data: Parsed requirement data
            timestamp: Optional timestamp for metadata

        Returns:
            TestCaseOutput object
        """
        # Extract key components from parsed data
        action = parsed_data.get('primary_action', '')
        target = parsed_data.get('target_object', '')
        outcome = parsed_data.get('expected_outcome', '')

        # Generate title and description
        title = f"Test {action} of {target}"
        description = f"Verify that {target} {action} results in {outcome}"

        # Create Gherkin-style test steps
        test_format = TestCaseFormat(
            given=[
                f"The system is ready for {target}",
                f"User has necessary permissions for {action}"
            ],
            when=[
                f"User attempts to {action} the {target}",
                "System processes the request"
            ],
            then=[
                f"System should {outcome}",
                "User should receive appropriate feedback"
            ],
            tags=[action.lower(), target.lower(), "automated"],
            priority="high" if "security" in target.lower() or "critical" in parsed_data.get('additional_context', {}).get('tags', []) else "medium"
        )

        return TestCaseOutput(
            title=title,
            description=description,
            format=test_format,
            metadata={
                "source_requirement": parsed_data.get('original_text', ''),
                "confidence_score": parsed_data.get('confidence_score', 0.0),
                "generated_timestamp": timestamp
            }
        )

    def _validate_test_case(self, test_case: TestCaseOutput) -> Dict[str, Any]:
        """Validate the generated test case

        Args:
            test_case: TestCaseOutput to validate

        Returns:
            Dict containing validation results
        """
        validation = {
            "is_valid": True,
            "checks": {
                "has_title": bool(test_case.title),
                "has_description": bool(test_case.description),
                "has_given_steps": len(test_case.format.given) > 0,
                "has_when_steps": len(test_case.format.when) > 0,
                "has_then_steps": len(test_case.format.then) > 0,
                "has_tags": bool(test_case.format.tags)
            },
            "warnings": []
        }

        # Add warnings for any failed checks
        for check, passed in validation["checks"].items():
            if not passed:
                validation["warnings"].append(f"Failed check: {check}")
                validation["is_valid"] = False

        return validation

    def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle test case-related events

        Args:
            event: Event data to process
        """
        event_type = event.get('type')
        if event_type == 'requirement_parsed':
            self.logger.info("Handling parsed requirement event")
            parsed_data = event.get('parsed_requirement')
            if parsed_data:
                self.execute_task({"parsed_requirement": parsed_data})
        elif event_type == 'config_update':
            self.logger.info("Handling configuration update event")
            # Handle configuration updates if needed

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "test_cases_generated": len(self.generated_cases),
            "last_generated": self.generated_cases[-1] if self.generated_cases else None
        })
        return status