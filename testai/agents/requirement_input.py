"""RequirementInputAgent implementation for handling test requirements and wireframes."""
from typing import Dict, List, Optional, Any
import logging
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentConfig

class RequirementInput(BaseModel):
    """Model for requirement input"""
    raw_text: str
    wireframe_paths: Optional[List[str]] = None
    project_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RequirementData(BaseModel):
    """Model for requirement data validation"""
    raw_text: str
    wireframe_paths: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class RequirementInputAgent(BaseAgent):
    """Agent responsible for processing and validating incoming test requirements"""

    def __init__(self):
        """Initialize the requirement input agent with its configuration"""
        config = AgentConfig(
            agent_id="requirement_input_001",
            role="Requirement Input Processor",
            goal="Process and validate incoming test requirements",
            backstory="Expert in requirements analysis and validation",
            verbose=True
        )
        super().__init__(config)
        self.processed_requirements = []

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a requirement processing task"""
        try:
            raw_data = RequirementData(**task)
            self.logger.info(f"Processing requirement: {raw_data.raw_text[:100]}...")

            # Clean and validate the requirement
            cleaned_text = self._clean_requirement(raw_data.raw_text)
            validated = self._validate_requirement(cleaned_text)

            # Process wireframes if provided
            wireframe_info = []
            if raw_data.wireframe_paths:
                wireframe_info = self._process_wireframes(raw_data.wireframe_paths)

            result = {
                "status": "success",
                "processed_requirement": {
                    "text": cleaned_text,
                    "wireframes": wireframe_info,
                    "metadata": raw_data.metadata or {},
                    "validation_status": validated
                }
            }

            self.processed_requirements.append(result)
            self.logger.info("Requirement processed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error processing requirement: {str(e)}")
            raise

    def _clean_requirement(self, text: str) -> str:
        """Clean and normalize requirement text"""
        # Basic cleaning operations
        cleaned = text.strip()
        cleaned = " ".join(cleaned.split())  # Normalize whitespace
        return cleaned

    def _validate_requirement(self, text: str) -> Dict[str, Any]:
        """Validate requirement text"""
        validation_results = {
            "is_valid": True,
            "checks": {
                "has_minimum_length": len(text) >= 10,
                "has_actionable_content": any(word in text.lower() for word in ["should", "must", "will", "verify", "check"]),
                "has_clear_subject": True  # Placeholder for more complex subject validation
            },
            "warnings": []
        }

        # Add warnings for any failed checks
        for check, passed in validation_results["checks"].items():
            if not passed:
                validation_results["warnings"].append(f"Failed check: {check}")
                validation_results["is_valid"] = False

        return validation_results

    def _process_wireframes(self, wireframe_paths: List[str]) -> List[Dict[str, Any]]:
        """Process and validate wireframe files"""
        wireframe_info = []
        for path in wireframe_paths:
            try:
                # Basic file validation
                info = {
                    "path": path,
                    "status": "processed",
                    "metadata": {
                        "original_filename": path.split("/")[-1]
                    }
                }
                wireframe_info.append(info)
            except Exception as e:
                self.logger.error(f"Error processing wireframe {path}: {str(e)}")
                wireframe_info.append({
                    "path": path,
                    "status": "error",
                    "error": str(e)
                })

        return wireframe_info

    def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle requirement-related events"""
        event_type = event.get('type')
        if event_type == 'requirement_update':
            self.logger.info("Handling requirement update event")
            requirement = event.get('requirement')
            if requirement:
                self.execute_task({"raw_text": requirement})
        elif event_type == 'config_update':
            self.logger.info("Handling configuration update event")

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "requirements_processed": len(self.processed_requirements),
            "last_requirement": self.processed_requirements[-1] if self.processed_requirements else None
        })
        return status