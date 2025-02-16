"""RequirementInputAgent for processing test requirements."""
import logging
from pydantic import BaseModel, Field
from typing import List, Optional

class RequirementInput(BaseModel):
    """Model for raw test requirements input"""
    raw_text: str
    wireframe_paths: Optional[List[str]] = None
    project_key: Optional[str] = None

class CleanedRequirement(BaseModel):
    """Model for cleaned requirement input"""
    title: str = Field(..., description="Title of the test case")
    description: str = Field(..., description="Description of what needs to be tested")
    acceptance_criteria: List[str] = Field(default_factory=list, description="List of acceptance criteria")
    prerequisites: Optional[List[str]] = Field(default_factory=list, description="List of prerequisites")
    
    @classmethod
    def from_text(cls, text: str):
        """Create from raw text input"""
        # Basic parsing logic - you can enhance this
        lines = text.strip().split('\n')
        title = lines[0] if lines else "Untitled Test Case"
        description = lines[1] if len(lines) > 1 else ""
        
        return cls(
            title=title,
            description=description,
            acceptance_criteria=[],
            prerequisites=[]
        )

class RequirementInputAgent:
    """Agent for cleaning and processing test requirements"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def clean_requirement(self, requirement: RequirementInput) -> CleanedRequirement:
        """Clean and structure raw test requirements"""
        try:
            # Split the raw text into sections
            lines = requirement.raw_text.strip().split('\n')
            title = lines[0].strip() if lines else "Untitled Test Case"

            # Initialize lists with default empty values
            description = ""
            acceptance_criteria = []
            prerequisites = []

            current_section = "description"
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue

                # Check for section headers
                if "acceptance criteria:" in line.lower():
                    current_section = "acceptance"
                    continue
                elif "prerequisites:" in line.lower():
                    current_section = "prerequisites"
                    continue

                # Add content to appropriate section
                if current_section == "description":
                    description += line + " "
                elif current_section == "acceptance":
                    if line.startswith("-"):
                        acceptance_criteria.append(line[1:].strip())
                    else:
                        acceptance_criteria.append(line)
                elif current_section == "prerequisites":
                    if line.startswith("-"):
                        prerequisites.append(line[1:].strip())
                    else:
                        prerequisites.append(line)

            # Ensure we have at least empty lists
            return CleanedRequirement(
                title=title,
                description=description.strip(),
                acceptance_criteria=acceptance_criteria or [],  # Ensure we have at least an empty list
                prerequisites=prerequisites or []  # Ensure we have at least an empty list
            )

        except Exception as e:
            self.logger.error(f"Error cleaning requirement: {str(e)}")
            raise