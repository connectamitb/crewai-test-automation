"""Test suite for WeaviateIntegration."""
import pytest
import os
from integrations.weaviate_integration import WeaviateIntegration
from integrations.models import TestCase

@pytest.fixture
def weaviate_client():
    return WeaviateIntegration()

def test_weaviate_connection():
    """Test basic Weaviate connection"""
    integration = WeaviateIntegration()
    # If no exception is raised, connection is successful
    assert integration.client is not None

def test_store_and_retrieve_test_case(weaviate_client):
    """Test storing and retrieving a test case"""
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
    test_case_id = weaviate_client.store_test_case(test_case)
    assert test_case_id is not None
    
    # Retrieve the test case
    retrieved = weaviate_client.get_test_case_by_name("Login Test")
    assert retrieved is not None
    assert retrieved["name"] == test_case.name
    assert retrieved["objective"] == test_case.objective
    assert len(retrieved["steps"]) == len(test_case.steps)

def test_search_test_cases(weaviate_client):
    """Test searching for test cases"""
    # Search for login-related test cases
    results = weaviate_client.search_test_cases("login authentication")
    assert isinstance(results, list)
    
    # Search should return results if test case was stored in previous test
    if results:
        assert any("login" in result["name"].lower() for result in results)

def test_create_and_search_test_case(weaviate_client):
    """Test creating and searching a test case"""
    # Create a test case
    test_case = TestCase(
        name="Login Feature Test",
        objective="Verify user can login with valid credentials",
        precondition="User has valid account",
        steps=["Navigate to login page", "Enter valid credentials", "Click login button"],
        requirement="""
        As a user
        I want to log in to the application
        So that I can access my account
        
        Acceptance Criteria:
        - User can login with valid email/password
        - User sees error with invalid credentials
        - User can reset password if forgotten
        """,
        gherkin="""
        Feature: User Login
        
        Scenario: Successful login with valid credentials
          Given I am on the login page
          When I enter valid email and password
          And I click the login button
          Then I should be logged in successfully
          And I should see my dashboard
        """
    )

    # Store the test case
    case_id = weaviate_client.store_test_case(test_case)
    assert case_id is not None, "Failed to store test case"

    # Search for the test case
    results = weaviate_client.search_test_cases("login user valid credentials")
    assert len(results) > 0, "No test cases found"
    
    found_case = results[0]
    assert "login" in found_case["title"].lower(), "Expected test case not found"
