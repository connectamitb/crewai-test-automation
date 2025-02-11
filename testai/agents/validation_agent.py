"""ValidationAgent implementation for validating test case quality and completeness."""
from typing import Dict, List, Optional, Any
import logging
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentConfig

class ValidationCriteria(BaseModel):
    """Model for validation criteria"""
    required_fields: List[str] = ["title", "description"]
    min_steps: int = 1
    min_description_length: int = 10
    required_sections: List[str] = ["given", "when", "then"]

class ValidationResult(BaseModel):
    """Model for validation results"""
    is_valid: bool
    checks: Dict[str, bool]
    score: float
    suggestions: List[str]

class ValidationAgent(BaseAgent):
    """Agent responsible for validating test case quality and completeness"""

    def __init__(self):
        """Initialize the validation agent with its configuration"""
        config = AgentConfig(
            agent_id="validation_001",
            role="Test Case Validator",
            goal="Ensure test cases meet quality standards",
            backstory="Quality assurance expert focused on test standardization",
            verbose=True
        )
        super().__init__(config)
        self.validation_history = []
        self.criteria = ValidationCriteria()

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test case validation task

        Args:
            task: Task containing test case to validate

        Returns:
            Dict containing validation results
        """
        try:
            test_case = task.get('test_case')
            if not test_case:
                raise ValueError("Test case is required for validation")

            logging.info(f"Validating test case: {test_case.get('title', 'Untitled')}")

            # Perform validation checks
            validation_result = self._validate_test_case(test_case)

            # Format response based on validation outcome
            result = validation_result.model_dump()

            # Log validation results
            if result["is_valid"]:
                logging.info(f"Test case validation successful with score: {result['score']}")
            else:
                logging.warning(f"Test case validation failed with score: {result['score']}")
                logging.warning(f"Validation suggestions: {', '.join(result['suggestions'])}")

            return result

        except Exception as e:
            logging.error(f"Error in validation: {str(e)}")
            raise

    def _validate_test_case(self, test_case: Dict[str, Any]) -> ValidationResult:
        """Validate a test case against defined criteria"""
        # Basic field presence checks
        checks = {
            "has_title": bool(test_case.get('title')),
            "has_description": bool(test_case.get('description')),
            "has_format": isinstance(test_case.get('format'), dict),
        }

        # Format section checks
        format_data = test_case.get('format', {})
        if checks["has_format"]:
            checks.update({
                f"has_{section}": bool(format_data.get(section))
                for section in self.criteria.required_sections
            })

            # Step count checks
            checks.update({
                f"{section}_steps": len(format_data.get(section, [])) >= self.criteria.min_steps
                for section in self.criteria.required_sections
            })

        # Calculate validation score
        valid_checks = sum(checks.values())
        total_checks = len(checks)
        score = valid_checks / total_checks if total_checks > 0 else 0

        # Generate improvement suggestions
        suggestions = []
        if not checks["has_title"]:
            suggestions.append("Add a title to the test case")
        if not checks["has_description"]:
            suggestions.append("Add a description to the test case")
        if not checks["has_format"]:
            suggestions.append("Test case must include format with given/when/then sections")
        else:
            for section in self.criteria.required_sections:
                if not checks.get(f"has_{section}"):
                    suggestions.append(f"Add {section} section to the test case")
                elif not checks.get(f"{section}_steps"):
                    suggestions.append(f"Add more steps to the {section} section (minimum {self.criteria.min_steps})")

        return ValidationResult(
            is_valid=score >= 0.8,  # Allow some flexibility in validation
            checks=checks,
            score=score,
            suggestions=suggestions
        )

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "validations_performed": len(self.validation_history),
            "current_criteria": self.criteria.model_dump()
        })
        return status