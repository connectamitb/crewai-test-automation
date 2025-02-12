"""RequirementInputAgent for processing test requirements."""
import logging
from pydantic import BaseModel
from typing import List, Optional

class RequirementInput(BaseModel):
    """Model for raw test requirements input"""
    raw_text: str
    wireframe_paths: Optional[List[str]] = None
    project_key: Optional[str] = None

class CleanedRequirement(BaseModel):
    """Model for cleaned test requirements"""
    title: str
    description: str
    acceptance_criteria: List[str]
    prerequisites: Optional[List[str]] = None

class RequirementInputAgent:
    """Agent for cleaning and processing test requirements"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def clean_requirement(self, requirement: RequirementInput) -> CleanedRequirement:
        """Clean and structure raw test requirements"""
        try:
            # Split the raw text into sections
            lines = requirement.raw_text.strip().split('\n')
            title = lines[0].strip()
            
            # Extract description and acceptance criteria
            description = ""
            acceptance_criteria = []
            prerequisites = []
            
            current_section = "description"
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                    
                if line.lower().startswith("acceptance criteria:"):
                    current_section = "acceptance"
                    continue
                elif line.lower().startswith("prerequisites:"):
                    current_section = "prerequisites"
                    continue
                
                if current_section == "description":
                    description += line + " "
                elif current_section == "acceptance":
                    acceptance_criteria.append(line)
                elif current_section == "prerequisites":
                    prerequisites.append(line)
            
            return CleanedRequirement(
                title=title,
                description=description.strip(),
                acceptance_criteria=acceptance_criteria,
                prerequisites=prerequisites if prerequisites else None
            )
            
        except Exception as e:
            self.logger.error(f"Error cleaning requirement: {str(e)}")
            raise
