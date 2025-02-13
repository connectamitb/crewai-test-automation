from typing import Dict, List, Optional
from crewai import Agent, Task, Crew
from pydantic import BaseModel, Field
from .base_agent import BaseAgent
from .storage_integration_agent import StorageIntegrationAgent
# ... rest of the code ... 

class TestCase(BaseModel):
    """Test case data model"""
    title: str = Field(default="")
    description: str = Field(default="")
    steps: List[str] = Field(default_factory=list)
    expected_results: List[str] = Field(default_factory=list)
    prerequisites: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)

class ManualTestAgent(BaseAgent):
    """Agent responsible for creating and managing manual test cases"""
    
    def __init__(self):
        super().__init__()
        self.storage = StorageIntegrationAgent()
        self.agent = Agent(
            name="Test Case Designer",
            role="Manual Test Case Designer",
            goal="Create comprehensive test cases in Gherkin format from requirements",
            backstory="Expert in BDD and test case design with deep understanding of Gherkin syntax",
            verbose=True,
            allow_delegation=False
        )
        
    async def create_test_case(self, requirement: str) -> Dict[str, str]:
        """Create a test case from a requirement"""
        try:
            gherkin_prompt = f"""
            Create a Gherkin format test case for the following requirement:
            {requirement}
            
            Follow this format:
            Feature: [Feature name]
            
              Background: (if needed)
                Given [preconditions]
            
              Scenario: [Scenario name]
                Given [initial context]
                When [action]
                Then [expected outcome]
            
            Make it detailed and specific.
            """
            
            task = Task(
                description=gherkin_prompt,
                expected_output="Gherkin format test case",
                agent=self.agent
            )
            
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                verbose=True
            )
            
            result = await crew.kickoff()
            
            # Store in Weaviate and Zephyr Scale
            await self._store_test_case(result, requirement)
            
            return {
                "gherkin": result,
                "requirement": requirement
            }
            
        except Exception as e:
            self.logger.error(f"Error creating test case: {str(e)}")
            raise
    
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
        validation_task = Task(
            description="Validate test case completeness and clarity",
            expected_output="Validation results",
            agent=self.agent,
            context=f"Validate the following test case:\n{test_case.dict()}",
            tools=[]
        )
        
        validation_result = await self.agent.kickoff(validation_task)
        
        if validation_result.get("is_valid"):
            await self.storage.store_test_case(test_case.dict()) 

    async def _store_test_case(self, gherkin: str, requirement: str):
        """Store test case in both Weaviate and Zephyr Scale"""
        # Convert Gherkin to TestCase model
        test_case = self._parse_gherkin(gherkin)
        
        # Store in Weaviate
        await self.storage.store_test_case(test_case, requirement, gherkin) 