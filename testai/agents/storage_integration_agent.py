"""StorageIntegrationAgent implementation for storing test cases."""
from typing import Dict, List, Any
import logging
from .base_agent import BaseAgent, AgentConfig

class StorageIntegrationAgent(BaseAgent):
    """Agent responsible for storing test cases in multiple backends"""

    def __init__(self):
        """Initialize the storage integration agent with its configuration"""
        config = AgentConfig(
            agent_id="storage_integration_001",
            role="Storage Integration Manager",
            goal="Store and manage test cases across multiple backends",
            backstory="Expert in data persistence and integration systems",
            verbose=True
        )
        super().__init__(config)
        self.stored_cases = []

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a storage task

        Args:
            task: Task containing test case to store

        Returns:
            Dict containing storage results
        """
        try:
            # Check if test_case key exists
            if 'test_case' not in task:
                raise ValueError("Test case is required")

            test_case = task['test_case']

            # Check if test_case is a dictionary
            if not isinstance(test_case, dict):
                raise ValueError("Test case must be a dictionary")

            # Validate test case format and required fields
            if not self._validate_test_case(test_case):
                raise ValueError("Invalid test case format")

            self.logger.info(f"Storing test case: {test_case.get('title', 'Untitled')}")

            # Store test case locally
            stored_case = {
                "title": test_case.get("title", ""),
                "description": test_case.get("description", ""),
                "steps": test_case.get("steps", []),
                "expected_results": test_case.get("expected_results", []),
                "metadata": test_case.get("metadata", {})
            }

            self.stored_cases.append(stored_case)

            return {
                "status": "success",
                "stored_case": stored_case
            }

        except Exception as e:
            self.logger.error(f"Error storing test case: {str(e)}")
            raise

    def _validate_test_case(self, test_case: Dict[str, Any]) -> bool:
        """Validate test case format

        Args:
            test_case: Test case to validate

        Returns:
            bool indicating if test case is valid
        """
        required_fields = ["title", "description"]
        return all(test_case.get(field) for field in required_fields)

    def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle storage-related events

        Args:
            event: Event data to process
        """
        event_type = event.get('type')
        if event_type == 'test_case_validated':
            self.logger.info("Handling validated test case event")
            test_case = event.get('test_case')
            if test_case:
                self.execute_task({"test_case": test_case})

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "cases_stored": len(self.stored_cases),
            "last_stored": self.stored_cases[-1] if self.stored_cases else None
        })
        return status