"""Zephyr Scale integration for test case management."""
import os
import logging
import json
from typing import Dict, List, Any, Optional
import requests
from pydantic import BaseModel

class ZephyrTestCase(BaseModel):
    """Model for Zephyr Scale test case"""
    name: str
    objective: str
    precondition: Optional[str] = None
    steps: List[Dict[str, str]]
    priority: str = "Normal"
    labels: Optional[List[str]] = None

class ZephyrIntegration:
    """Handles interaction with Zephyr Scale API"""

    def __init__(self):
        """Initialize Zephyr Scale client with configuration"""
        # Configure logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Add console handler if not already added
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - ZEPHYR - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        self.api_key = os.environ.get("ZEPHYR_API_KEY")
        self.project_key = os.environ.get("ZEPHYR_PROJECT_KEY", "QADEMO")
        self.base_url = "https://api.zephyrscale.smartbear.com/v2"

        if not self.api_key:
            self.logger.warning("⚠️ ZEPHYR_API_KEY not set in environment variables")
        else:
            self.logger.info("✅ Zephyr Scale integration initialized with API key")

    def create_test_case(self, test_case: ZephyrTestCase) -> Optional[str]:
        """Create a test case in Zephyr Scale"""
        try:
            if not self.api_key:
                self.logger.error("❌ Cannot create test case: ZEPHYR_API_KEY not set")
                return None

            self.logger.info(f"📝 Creating test case in Zephyr Scale: {test_case.name}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Format steps for Zephyr Scale
            formatted_steps = []
            for step in test_case.steps:
                formatted_step = {
                    "description": step.get("step", ""),
                    "testData": step.get("test_data", ""),
                    "expectedResult": step.get("expected_result", "")
                }
                self.logger.debug(f"Step formatted: {json.dumps(formatted_step, indent=2)}")
                formatted_steps.append(formatted_step)

            payload = {
                "projectKey": self.project_key,
                "name": test_case.name,
                "objective": test_case.objective,
                "priorityName": test_case.priority.upper(),
                "statusName": "Draft",
                "steps": formatted_steps
            }

            if test_case.precondition:
                payload["precondition"] = test_case.precondition

            if test_case.labels:
                payload["labels"] = test_case.labels

            self.logger.info("🚀 Sending request to Zephyr Scale API")
            self.logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                f"{self.base_url}/testcases",
                headers=headers,
                json=payload,
                timeout=30
            )

            self.logger.info(f"📨 Zephyr Scale response status: {response.status_code}")
            self.logger.debug(f"Response body: {response.text}")

            if response.status_code in (200, 201):
                result = response.json()
                self.logger.info(f"✅ Successfully created test case in Zephyr Scale: {result.get('key')}")
                return result.get("key")
            else:
                self.logger.error(f"❌ Failed to create test case in Zephyr Scale: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Network error creating test case in Zephyr Scale: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error creating test case in Zephyr Scale: {str(e)}")
            return None

    def get_test_case(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a test case from Zephyr Scale by key
        
        Args:
            key: Test case key
            
        Returns:
            dict: Test case data if found, None otherwise
        """
        try:
            if not self.api_key:
                self.logger.error("Cannot get test case: ZEPHYR_API_KEY not set")
                return None

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }

            response = requests.get(
                f"{self.base_url}/testcases/{key}",
                headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get test case from Zephyr Scale: {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting test case from Zephyr Scale: {str(e)}")
            return None

    def search_test_cases(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for test cases in Zephyr Scale
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            list: List of matching test cases
        """
        try:
            if not self.api_key:
                self.logger.error("Cannot search test cases: ZEPHYR_API_KEY not set")
                return []

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }

            params = {
                "projectKey": self.project_key,
                "text": query,
                "maxResults": max_results
            }

            response = requests.get(
                f"{self.base_url}/testcases/search",
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                return response.json()["values"]
            else:
                self.logger.error(f"Failed to search test cases in Zephyr Scale: {response.text}")
                return []

        except Exception as e:
            self.logger.error(f"Error searching test cases in Zephyr Scale: {str(e)}")
            return []