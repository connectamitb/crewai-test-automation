"""NLPParsingAgent implementation for parsing and structuring test requirements."""
from typing import Dict, List, Optional, Any
import logging
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentConfig

class ParsedRequirement(BaseModel):
    """Model for parsed requirement data"""
    primary_action: str
    target_object: str
    expected_outcome: str
    additional_context: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0

class NLPParsingAgent(BaseAgent):
    """Agent responsible for parsing requirements using NLP"""

    def __init__(self):
        """Initialize the NLP parsing agent with its configuration"""
        config = AgentConfig(
            agent_id="nlp_parsing_001",
            role="NLP Parser",
            goal="Extract structured information from requirements",
            backstory="Specialist in natural language processing and requirement analysis",
            verbose=True
        )
        super().__init__(config)
        self.parsed_requirements = []

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a requirement parsing task
        
        Args:
            task: Task containing cleaned requirement text
            
        Returns:
            Dict containing parsed requirement structure
        """
        try:
            requirement_text = task.get('cleaned_requirement')
            if not requirement_text:
                raise ValueError("Cleaned requirement text is required")

            self.logger.info(f"Parsing requirement: {requirement_text[:100]}...")
            
            # Parse the requirement text
            parsed = self._parse_requirement(requirement_text)
            
            # Validate the parsed structure
            validation_result = self._validate_parsed_structure(parsed)
            
            result = {
                "status": "success",
                "parsed_requirement": parsed.model_dump(),
                "validation": validation_result
            }
            
            self.parsed_requirements.append(result)
            self.logger.info("Requirement successfully parsed")
            return result

        except Exception as e:
            self.logger.error(f"Error parsing requirement: {str(e)}")
            raise

    def _parse_requirement(self, text: str) -> ParsedRequirement:
        """Parse requirement text into structured format
        
        Args:
            text: Cleaned requirement text
            
        Returns:
            ParsedRequirement object
        """
        # Basic parsing logic - to be enhanced with actual NLP processing
        words = text.split()
        
        # Simple extraction based on common patterns
        action = next((w for w in words if w.lower() in ["verify", "check", "validate", "test"]), "verify")
        target = " ".join(words[words.index(action) + 1:words.index(action) + 3])
        outcome = " ".join(words[words.index(action) + 3:])

        return ParsedRequirement(
            primary_action=action,
            target_object=target,
            expected_outcome=outcome,
            additional_context={
                "original_text": text,
                "word_count": len(words)
            },
            confidence_score=0.8  # Placeholder score
        )

    def _validate_parsed_structure(self, parsed: ParsedRequirement) -> Dict[str, Any]:
        """Validate the parsed requirement structure
        
        Args:
            parsed: ParsedRequirement to validate
            
        Returns:
            Dict containing validation results
        """
        validation = {
            "is_valid": True,
            "checks": {
                "has_action": bool(parsed.primary_action),
                "has_target": bool(parsed.target_object),
                "has_outcome": bool(parsed.expected_outcome),
                "confidence_acceptable": parsed.confidence_score >= 0.7
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
        """Handle requirement-related events
        
        Args:
            event: Event data to process
        """
        event_type = event.get('type')
        if event_type == 'requirement_update':
            self.logger.info("Handling requirement update event")
            requirement = event.get('requirement')
            if requirement:
                self.execute_task({"cleaned_requirement": requirement})
        elif event_type == 'config_update':
            self.logger.info("Handling configuration update event")
            # Handle configuration updates if needed

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "requirements_parsed": len(self.parsed_requirements),
            "last_parsed": self.parsed_requirements[-1] if self.parsed_requirements else None
        })
        return status
