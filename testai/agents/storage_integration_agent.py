from typing import Dict, Optional, List
import requests
from pydantic import BaseModel
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class ZephyrTestStep(BaseModel):
    """Zephyr Scale test step model"""
    description: str
    expectedResult: str
    data: Optional[str] = None

class ZephyrTestCase(BaseModel):
    """Zephyr Scale test case model"""
    projectKey: str
    name: str
    objective: str
    precondition: Optional[str]
    testScript: Optional[Dict[str, List[ZephyrTestStep]]] = None
    labels: Optional[List[str]] = []
    priority: Optional[str] = "Normal"
    status: str = "Draft"

class StorageIntegrationAgent:
    """Handles test case storage in Zephyr Scale"""
    
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.ZEPHYR_SCALE_TOKEN}",
            "Content-Type": "application/json"
        }
    
    async def store_test_case(self, test_case: Dict) -> bool:
        """Store test case in Zephyr Scale"""
        try:
            # Convert test steps to Zephyr format
            steps = []
            for step, expected in zip(test_case["steps"], test_case["expected_results"]):
                steps.append(
                    ZephyrTestStep(
                        description=step,
                        expectedResult=expected
                    )
                )
            
            # Create Zephyr test case payload
            payload = ZephyrTestCase(
                projectKey=settings.PROJECT_KEY,
                name=test_case["title"],
                objective=test_case["description"],
                precondition="\n".join(test_case.get("prerequisites", [])),
                testScript={
                    "type": "plain",
                    "steps": steps
                },
                labels=test_case.get("tags", [])
            )

            # Make API request
            response = requests.post(
                settings.STORAGE_API_ENDPOINT,
                json=payload.dict(exclude_none=True),
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Test case '{test_case['title']}' stored successfully in Zephyr Scale")
                return True
            else:
                logger.error(
                    f"Failed to store test case in Zephyr Scale. Status: {response.status_code}, "
                    f"Response: {response.text}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error storing test case in Zephyr Scale: {str(e)}")
            return False 