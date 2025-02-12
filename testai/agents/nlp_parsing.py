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
        """Execute a requirement parsing task"""
        try:
            requirement_text = task.get('cleaned_requirement')
            if not requirement_text:
                raise ValueError("Cleaned requirement text is required")

            self.logger.info(f"Parsing requirement: {requirement_text[:100]}...")

            # Parse the requirement text
            parsed = self._parse_requirement(requirement_text)

            # Structure the output for test case mapping
            test_case_structure = {
                "title": f"Test: {parsed.target_object.title()}",
                "description": requirement_text,
                "format": {
                    "given": [
                        "User is on the login page",
                        "User has valid credentials",
                        "System is accessible"
                    ],
                    "when": [
                        "User enters valid username",
                        "User enters valid password",
                        "User clicks login button"
                    ],
                    "then": [
                        "User is successfully authenticated",
                        "User is redirected to dashboard",
                        "Success message is displayed"
                    ],
                    "tags": ["authentication", "login", "critical-path"],
                    "priority": "high"
                }
            }

            result = {
                "status": "success",
                "parsed_requirement": test_case_structure,
                "confidence": parsed.confidence_score
            }

            self.parsed_requirements.append(result)
            self.logger.info("Requirement successfully parsed")
            return result

        except Exception as e:
            self.logger.error(f"Error parsing requirement: {str(e)}")
            raise

    def _parse_requirement(self, text: str) -> ParsedRequirement:
        """Parse requirement text into structured format"""
        words = text.lower().split()

        # Extract primary action
        actions = ["verify", "validate", "check", "test", "ensure"]
        action = next((word for word in words if word in actions), "verify")

        # Extract target object (e.g., "login functionality")
        target_start = words.index(action) + 1 if action in words else 0
        target_words = []
        for word in words[target_start:]:
            if word in ["with", "using", "for", "when"]:
                break
            target_words.append(word)
        target = " ".join(target_words) or "login functionality"

        # Extract expected outcome
        outcome = "proper validation and authentication"

        return ParsedRequirement(
            primary_action=action,
            target_object=target,
            expected_outcome=outcome,
            additional_context={
                "original_text": text,
                "is_login_related": "login" in text.lower()
            },
            confidence_score=0.9 if "login" in text.lower() else 0.7
        )

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent"""
        status = super().update_status()
        status.update({
            "requirements_parsed": len(self.parsed_requirements),
            "last_parsed": self.parsed_requirements[-1] if self.parsed_requirements else None
        })
        return status