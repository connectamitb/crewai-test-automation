from typing import Dict, List, Optional
import logging
from pydantic import BaseModel
from crewai import Agent, Task, Crew

class TestCase(BaseModel):
    """Test case data model"""
    title: str
    description: str
    steps: List[str]
    expected_results: List[str]
    prerequisites: Optional[List[str]] = []
    tags: Optional[List[str]] = []

class ManualTestAgent:
    """Agent responsible for creating and managing manual test cases"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agent = Agent(
            name="Test Case Designer",
            role="Manual Test Case Designer",
            goal="Create comprehensive manual test cases from requirements",
            backstory="Expert in test case design with deep understanding of testing principles",
            verbose=True
        )
        self.crew = Crew(
            agents=[self.agent],
            tasks=[],
            verbose=True
        )

    async def create_test_case(self, requirement: str) -> TestCase:
        """Create a test case from a requirement"""
        try:
            # Create task for requirement analysis
            analysis_task = Task(
                description=f"Analyze requirement: {requirement}",
                agent=self.agent
            )

            # Execute task
            result = await self.crew.kickoff(analysis_task) #Corrected this line to pass the task

            # Create a sample test case (replace this with actual AI generation)
            test_case = TestCase(
                title="Login Functionality Test",
                description="Verify user can successfully log in to the application",
                steps=[
                    "Navigate to login page",
                    "Enter valid credentials",
                    "Click login button"
                ],
                expected_results=[
                    "Login page loads successfully",
                    "Input fields accept the credentials",
                    "User is redirected to dashboard"
                ],
                prerequisites=["Valid user account exists"],
                tags=["authentication", "login", "user-access"]
            )

            return test_case

        except Exception as e:
            self.logger.error(f"Error creating test case: {str(e)}")
            raise