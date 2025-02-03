from typing import Dict, List, Optional
from crewai import Agent, Task
from pydantic import BaseModel
from .base_agent import BaseAgent
from .storage_integration_agent import StorageIntegrationAgent

class TestCase(BaseModel):
    """Test case data model"""
    title: str
    description: str
    steps: List[str]
    expected_results: List[str]
    prerequisites: Optional[List[str]] = []
    tags: Optional[List[str]] = []

class ManualTestAgent(BaseAgent):
    """
    Agent responsible for creating and managing manual test cases
    using AI-driven recommendations
    """
    
    def __init__(self):
        super().__init__()
        self.storage = StorageIntegrationAgent()
        self.agent = Agent(
            role="Manual Test Case Designer",
            goal="Create comprehensive manual test cases from requirements",
            backstory="Expert in test case design with deep understanding of testing principles",
            allow_delegation=True,
            verbose=True
        )
        
    async def create_test_case(self, requirement: str) -> TestCase:
        """Create a test case from a requirement"""
        
        # Create task for requirement analysis
        analysis_task = Task(
            description=f"Analyze requirement: {requirement}",
            expected_output="Structured test case components"
        )
        
        # Execute task with memory management
        with self.memory_context():
            result = await self.agent.execute(analysis_task)
            
        # Transform result into TestCase model
        test_case = self._parse_result(result)
        
        # Validate and store test case
        await self._validate_and_store(test_case)
        
        return test_case
    
    def _parse_result(self, result: Dict) -> TestCase:
        """Parse agent result into TestCase model"""
        return TestCase(
            title=result.get("title", ""),
            description=result.get("description", ""),
            steps=result.get("steps", []),
            expected_results=result.get("expected_results", []),
            prerequisites=result.get("prerequisites", []),
            tags=result.get("tags", [])
        )
    
    async def _validate_and_store(self, test_case: TestCase):
        """Validate and store the test case"""
        # Implement validation logic
        validation_task = Task(
            description="Validate test case completeness and clarity",
            expected_output="Validation results"
        )
        
        validation_result = await self.agent.execute(validation_task)
        
        if validation_result.get("is_valid"):
            await self.storage.store_test_case(test_case) 