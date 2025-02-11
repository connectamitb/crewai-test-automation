"""ValidationAgent implementation for validating test case quality and completeness."""
from typing import Dict, List, Optional, Any
import logging
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentConfig

class ValidationCriteria(BaseModel):
    """Model for validation criteria"""
    required_fields: List[str]
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
            goal="Ensure test cases meet quality standards and contain required elements",
            backstory="Quality assurance expert with focus on test case standardization",
            verbose=True
        )
        super().__init__(config)
        self.validation_history = []
        self.criteria = ValidationCriteria(
            required_fields=["title", "description", "steps"],
            min_steps=2,
            min_description_length=20,
            required_sections=["given", "when", "then"]
        )

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

            self.logger.info(f"Validating test case: {test_case.get('title', 'Untitled')}")
            
            # Perform validation checks
            validation_result = self._validate_test_case(test_case)
            
            result = {
                "status": "success",
                "validation_result": validation_result.model_dump()
            }
            
            self.validation_history.append(result)
            self.logger.info(f"Validation completed with score: {validation_result.score}")
            return result

        except Exception as e:
            self.logger.error(f"Error in validation: {str(e)}")
            raise

    def _validate_test_case(self, test_case: Dict[str, Any]) -> ValidationResult:
        """Validate a test case against defined criteria
        
        Args:
            test_case: Test case to validate
            
        Returns:
            ValidationResult object
        """
        checks = {
            "has_title": bool(test_case.get('title')),
            "has_description": bool(test_case.get('description')),
            "description_length": len(str(test_case.get('description', ''))) >= self.criteria.min_description_length,
            "has_all_sections": all(
                section in test_case.get('format', {}).keys() 
                for section in self.criteria.required_sections
            ),
            "min_steps_met": all(
                len(test_case.get('format', {}).get(section, [])) >= self.criteria.min_steps
                for section in self.criteria.required_sections
            )
        }
        
        # Calculate validation score
        score = sum(checks.values()) / len(checks)
        
        # Generate improvement suggestions
        suggestions = []
        if not checks["has_title"]:
            suggestions.append("Add a clear and descriptive title")
        if not checks["description_length"]:
            suggestions.append(f"Expand description to at least {self.criteria.min_description_length} characters")
        if not checks["has_all_sections"]:
            missing = [s for s in self.criteria.required_sections if s not in test_case.get('format', {})]
            suggestions.append(f"Add missing sections: {', '.join(missing)}")
        if not checks["min_steps_met"]:
            suggestions.append(f"Ensure each section has at least {self.criteria.min_steps} steps")

        return ValidationResult(
            is_valid=all(checks.values()),
            checks=checks,
            score=score,
            suggestions=suggestions
        )

    def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle validation-related events
        
        Args:
            event: Event data to process
        """
        event_type = event.get('type')
        if event_type == 'test_case_created':
            self.logger.info("Handling test case creation event")
            test_case = event.get('test_case')
            if test_case:
                self.execute_task({"test_case": test_case})
        elif event_type == 'config_update':
            self.logger.info("Handling configuration update event")
            config = event.get('config')
            if config:
                self.criteria = ValidationCriteria(**config)

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "validations_performed": len(self.validation_history),
            "last_validation": self.validation_history[-1] if self.validation_history else None,
            "current_criteria": self.criteria.model_dump()
        })
        return status
