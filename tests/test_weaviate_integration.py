"""Test suite for WeaviateIntegration."""
import pytest
from integrations.weaviate_integration import WeaviateIntegration, TestCase

def test_weaviate_connection():
    """Test basic Weaviate connection"""
    integration = WeaviateIntegration()
    # If no exception is raised, connection is successful
    assert integration.client is not None

def test_store_and_retrieve_test_case():
    """Test storing and retrieving a test case"""
    integration = WeaviateIntegration()
    
    # Create a test case
    test_case = TestCase(
        name="Login Test",
        objective="Verify user can login successfully",
        precondition="User exists in the system",
        automation_needed="Yes",
        steps=[
            {
                "step": "Navigate to login page",
                "test_data": "URL: /login",
                "expected_result": "Login page is displayed"
            },
            {
                "step": "Enter credentials and submit",
                "test_data": "Username: test@example.com, Password: testpass",
                "expected_result": "User is logged in successfully"
            }
        ]
    )
    
    # Store the test case
    test_case_id = integration.store_test_case(test_case)
    assert test_case_id is not None
    
    # Retrieve the test case
    retrieved = integration.get_test_case_by_name("Login Test")
    assert retrieved is not None
    assert retrieved["name"] == test_case.name
    assert retrieved["objective"] == test_case.objective
    assert len(retrieved["steps"]) == len(test_case.steps)

def test_search_test_cases():
    """Test searching for test cases"""
    integration = WeaviateIntegration()
    
    # Search for login-related test cases
    results = integration.search_test_cases("login authentication")
    assert isinstance(results, list)
    
    # Search should return results if test case was stored in previous test
    if results:
        assert any("login" in result["name"].lower() for result in results)
