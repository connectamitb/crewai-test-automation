"""Unit tests for test case generation functionality."""
import unittest
from unittest.mock import patch, MagicMock
from flask import json
from app import create_app
from agents.requirement_input import RequirementInputAgent, RequirementInput
from agents.nlp_parsing import NLPParsingAgent

class TestCaseGenerationTest(unittest.TestCase):
    """Test suite for test case generation functionality."""

    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.client = self.app.test_client()
        self.requirement_agent = RequirementInputAgent()
        self.nlp_agent = NLPParsingAgent()

    @patch('routes.test_cases.weaviate_client')
    @patch('routes.test_cases.zephyr_client')
    def test_create_test_case(self, mock_zephyr, mock_weaviate):
        """Test creating a test case from requirements."""
        # Configure mocks
        mock_weaviate.store_test_case.return_value = "test-weaviate-id"
        mock_zephyr.create_test_case.return_value = "TEST-123"

        # Sample test requirement
        test_requirement = """Login Feature Test
Description: Verify that users can successfully log in to the application using valid credentials.

Prerequisites:
- User account exists in the system
- User has valid credentials
- System is accessible via web browser

Acceptance Criteria:
- User can access login page
- System validates email format
- System validates password requirements
- User receives error message for invalid credentials
- User is redirected to dashboard after successful login"""

        # Create test case through API
        response = self.client.post('/api/v1/test-cases',
            json={
                'requirement_text': test_requirement,
                'project_key': 'TEST-123'
            },
            content_type='application/json'
        )

        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)

        # Verify response structure
        self.assertIn('weaviate_id', data)
        self.assertIn('zephyr_key', data)
        self.assertIn('parsed_test_case', data)

        parsed_test_case = data['parsed_test_case']

        # Verify test case content
        self.assertEqual(parsed_test_case['name'], 'Login Feature Test')
        self.assertIn('valid credentials', parsed_test_case['objective'].lower())
        self.assertGreater(len(parsed_test_case['steps']), 0)

        # Print generated test case details for verification
        print("\nGenerated Test Case:")
        print(f"Name: {parsed_test_case['name']}")
        print(f"Objective: {parsed_test_case['objective']}")
        print(f"Precondition: {parsed_test_case.get('precondition', 'None')}")
        print("\nSteps:")
        for step in parsed_test_case['steps']:
            print(f"- Step: {step['step']}")
            if step.get('test_data'):
                print(f"  Test Data: {step['test_data']}")
            print(f"  Expected Result: {step['expected_result']}")
        print(f"\nWeaviate ID: {data['weaviate_id']}")
        print(f"Zephyr Key: {data['zephyr_key']}")

if __name__ == '__main__':
    unittest.main()