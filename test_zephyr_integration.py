import os
import json
import logging
from unittest.mock import patch
import pytest
from testai.agents.test_case_mapping import TestCaseMappingAgent, TestCaseOutput, TestCaseFormat

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_create_simple_test_case():
    """Test creating a simple test case in Zephyr Scale"""
    try:
        # Initialize the agent
        agent = TestCaseMappingAgent()

        # Create a test case with multiple steps
        test_case = TestCaseOutput(
            title="Login Functionality Test",
            description="Verify user can successfully log in with valid credentials and appropriate error messages are shown for invalid attempts",
            format=TestCaseFormat(
                given=[
                    "User is on the login page",
                    "User has valid credentials",
                    "System is accessible"
                ],
                when=[
                    "User enters a valid username",
                    "User enters a valid password",
                    "User clicks the login button"
                ],
                then=[
                    "Username field accepts the input",
                    "Password field accepts the input",
                    "User is successfully logged in and redirected to dashboard"
                ],
                tags=["test", "login", "authentication"],
                priority="Normal"
            )
        )

        # Convert to dict
        test_case_dict = test_case.model_dump()

        # Log the test case we're about to send
        logger.info("Test Case to be sent:")
        logger.info(json.dumps(test_case_dict, indent=2))

        # Attempt to store in Zephyr Scale
        result = agent._store_in_zephyr(test_case_dict)

        if result:
            logger.info("Successfully created test case in Zephyr Scale")
        else:
            logger.error("Failed to create test case in Zephyr Scale")

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

def test_create_test_case_with_steps():
    """Test creating a test case with multiple steps in Zephyr Scale"""
    try:
        # Initialize the agent
        agent = TestCaseMappingAgent()

        # Create a test case with multiple detailed steps
        test_case = TestCaseOutput(
            title="Login Functionality Test Suite",
            description="Comprehensive test suite for login functionality including positive and negative scenarios",
            format=TestCaseFormat(
                given=[
                    "System is accessible and in a known good state",
                    "Test user credentials are available",
                    "Database is properly configured"
                ],
                when=[
                    "Navigate to the login page",
                    "Enter valid username: test@example.com",
                    "Enter valid password: Test123!",
                    "Click the login button"
                ],
                then=[
                    "Username field accepts the input correctly",
                    "Password field masks the input",
                    "Login button is clickable",
                    "User is successfully authenticated"
                ],
                tags=["authentication", "login", "critical-path"],
                priority="High"
            )
        )

        # Convert to dict
        test_case_dict = test_case.model_dump()

        # Log the test case structure before sending
        logger.info("Test Case Structure:")
        logger.info(json.dumps(test_case_dict, indent=2))

        # Store in Zephyr Scale
        result = agent._store_in_zephyr(test_case_dict)

        assert result is True, "Failed to store test case in Zephyr Scale"

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

def test_verify_zephyr_step_format():
    """Test the format of steps being sent to Zephyr Scale"""
    agent = TestCaseMappingAgent()

    test_case = TestCaseOutput(
        title="Step Format Verification Test",
        description="Verify that steps are formatted correctly for Zephyr Scale",
        format=TestCaseFormat(
            given=["System is accessible"],
            when=["Perform action A", "Perform action B"],
            then=["Verify result A", "Verify result B"],
            tags=["format-test"],
            priority="Normal"
        )
    )

    test_case_dict = test_case.model_dump()

    # Mock the requests.post call to capture the payload
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"key": "TEST-1"}

        agent._store_in_zephyr(test_case_dict)

        # Get the payload that would be sent to Zephyr
        calls = mock_post.call_args_list
        assert len(calls) > 0, "No API calls were made"

        actual_payload = calls[0].kwargs['json']
        logger.info("Actual payload sent to Zephyr Scale:")
        logger.info(json.dumps(actual_payload, indent=2))

        # Verify step format
        assert 'script' in actual_payload, "Missing 'script' in payload"
        assert 'steps' in actual_payload['script'], "Missing 'steps' in script"

        steps = actual_payload['script']['steps']
        for step in steps:
            assert 'description' in step, "Step missing 'description'"
            assert 'testData' in step, "Step missing 'testData'"
            assert 'expectedResult' in step, "Step missing 'expectedResult'"

def test_create_data_validation_test_case():
    """Test creating a data validation test case in Zephyr Scale"""
    try:
        # Initialize the agent
        agent = TestCaseMappingAgent()

        # Create a test case for data validation
        test_case = TestCaseOutput(
            title="Data Validation Test Suite",
            description="Verify data validation rules for user input fields",
            format=TestCaseFormat(
                given=[
                    "User is on the data entry form",
                    "Form validation rules are configured",
                    "Test data set is prepared"
                ],
                when=[
                    "Enter special characters in username field",
                    "Enter non-numeric data in phone field",
                    "Enter invalid email format",
                    "Submit the form"
                ],
                then=[
                    "Username field shows invalid character error",
                    "Phone field displays numeric only message",
                    "Email field indicates invalid format",
                    "Form submission is prevented"
                ],
                tags=["validation", "user-input", "error-handling"],
                priority="High"
            )
        )

        # Convert to dict
        test_case_dict = test_case.model_dump()

        # Log the test case structure
        logger.info("Data Validation Test Case Structure:")
        logger.info(json.dumps(test_case_dict, indent=2))

        # Store in Zephyr Scale
        result = agent._store_in_zephyr(test_case_dict)

        assert result is True, "Failed to store test case in Zephyr Scale"
        logger.info("Successfully created data validation test case")

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

def test_create_api_test_case():
    """Test creating an API test case with multiple steps in Zephyr Scale"""
    try:
        # Initialize the agent
        agent = TestCaseMappingAgent()

        # Create a test case for API testing
        test_case = TestCaseOutput(
            title="API Integration Test - User Management",
            description="Verify REST API endpoints for user management operations",
            format=TestCaseFormat(
                given=[
                    "API server is running and accessible",
                    "Test user credentials are available",
                    "Database is in a known state"
                ],
                when=[
                    "Send POST request to /api/users with valid user data",
                    "Send GET request to /api/users/{user_id}",
                    "Send PUT request to /api/users/{user_id} with updated data"
                ],
                then=[
                    "Receive 201 Created response with user details",
                    "Receive 200 OK response with correct user data",
                    "Receive 200 OK response with updated user details"
                ],
                tags=["api", "integration", "user-management"],
                priority="High"
            )
        )

        # Convert to dict
        test_case_dict = test_case.model_dump()

        # Log the test case structure
        logger.info("API Test Case Structure:")
        logger.info(json.dumps(test_case_dict, indent=2))

        # Store in Zephyr Scale
        result = agent._store_in_zephyr(test_case_dict)

        assert result is True, "Failed to store test case in Zephyr Scale"
        logger.info("Successfully created API test case")

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

def test_step_structure_validation():
    """Test to validate the step structure being sent to Zephyr Scale"""
    try:
        agent = TestCaseMappingAgent()

        # Create a simple test case with clear step structure
        test_case = TestCaseOutput(
            title="Step Structure Validation",
            description="Test case to verify step structure in Zephyr Scale",
            format=TestCaseFormat(
                given=[
                    "Test system is accessible",
                    "Required test data is loaded"
                ],
                when=[
                    "Execute step 1",
                    "Execute step 2",
                    "Execute step 3"
                ],
                then=[
                    "Verify result 1",
                    "Verify result 2",
                    "Verify result 3"
                ],
                tags=["test", "validation"],
                priority="Normal"
            )
        )

        test_case_dict = test_case.model_dump()

        # Mock the requests.post call to capture the payload
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"key": "TEST-1"}

            # Attempt to store in Zephyr Scale
            agent._store_in_zephyr(test_case_dict)

            # Get the payload that would be sent to Zephyr
            calls = mock_post.call_args_list
            assert len(calls) > 0, "No API calls were made"

            actual_payload = calls[0].kwargs['json']

            # Log the complete payload for debugging
            logger.info("Complete Zephyr Scale payload:")
            logger.info(json.dumps(actual_payload, indent=2))

            # Verify script and steps structure
            assert 'script' in actual_payload, "Missing 'script' in payload"
            assert 'steps' in actual_payload['script'], "Missing 'steps' in script"
            assert actual_payload['script']['type'] == "STEP_BY_STEP", "Incorrect script type"

            steps = actual_payload['script']['steps']
            assert len(steps) >= 5, "Not enough steps created"  # At least Given + When + Then steps

            # Verify step structure
            for step in steps:
                assert 'index' in step, "Step missing 'index'"
                assert 'description' in step, "Step missing 'description'"
                assert 'testData' in step, "Step missing 'testData'"
                assert 'expectedResult' in step, "Step missing 'expectedResult'"

                # Verify step prefixes
                desc = step['description']
                assert any(prefix in desc for prefix in ['GIVEN:', 'WHEN:', 'Verify:', 'THEN:']), \
                    f"Step missing proper prefix: {desc}"

            logger.info("Step structure validation successful")

    except Exception as e:
        logger.error(f"Error in step structure validation: {str(e)}")
        raise

def test_search_test_cases():
    """Test searching for test cases in Zephyr Scale"""
    try:
        # Initialize the agent
        agent = TestCaseMappingAgent()

        # Mock the search response
        mock_response = [
            {
                "key": "TEST-1",
                "name": "Login Test Case",
                "objective": "Verify user login functionality",
                "priorityName": "High",
                "labels": ["authentication", "login"],
                "script": {
                    "type": "STEP_BY_STEP",
                    "steps": [{"step": 1}, {"step": 2}]
                }
            }
        ]

        # Test different search scenarios
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            # Test search by query
            results = agent.search_test_cases(query="login")
            assert len(results) > 0, "No test cases found"

            test_case = results[0]
            assert "key" in test_case, "Test case missing key"
            assert "name" in test_case, "Test case missing name"
            assert len(test_case["script"]["steps"]) == 2, "Incorrect step count"

            # Verify search parameters
            calls = mock_get.call_args_list
            assert len(calls) > 0, "No API calls were made"
            params = calls[0].kwargs['params']
            assert "text" in params, "Search query parameter missing"
            assert params["projectKey"] == agent.zephyr_project_key, "Project key missing"

            # Log the search results
            logger.info("Search Results:")
            logger.info(json.dumps(results, indent=2))

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--log-cli-level=DEBUG"])