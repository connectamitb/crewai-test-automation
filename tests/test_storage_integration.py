"""Test suite for StorageIntegrationAgent."""
import pytest
from testai.agents.storage_integration_agent import StorageIntegrationAgent
from integrations.weaviate_integration import TestCase

def test_storage_integration_agent_initialization():
    """Test StorageIntegrationAgent initialization"""
    agent = StorageIntegrationAgent()
    assert agent.config.agent_id == "storage_integration_001"
    assert agent.config.role == "Storage Integration Manager"
    assert isinstance(agent.stored_cases, list)
    assert agent.weaviate is not None

def test_basic_storage():
    """Test basic test case storage"""
    agent = StorageIntegrationAgent()
    test_case = {
        "title": "Test Login Feature",
        "description": "Verify user login functionality",
        "precondition": "User exists in the system",
        "automation_needed": "Yes",
        "steps": [
            {
                "action": "Navigate to login page",
                "test_data": "URL: /login",
                "expected_result": "Login page loads successfully"
            },
            {
                "action": "Enter credentials",
                "test_data": "username=test@example.com, password=testpass",
                "expected_result": "User is logged in"
            }
        ]
    }

    result = agent.execute_task({"test_case": test_case})

    assert result["status"] == "success"
    assert "weaviate_id" in result
    assert len(agent.stored_cases) == 1
    assert agent.stored_cases[0]["name"] == "Test Login Feature"

def test_invalid_test_case():
    """Test handling of invalid test cases"""
    agent = StorageIntegrationAgent()

    # Test with missing test case
    with pytest.raises(ValueError, match="Test case is required"):
        agent.execute_task({})

    # Test with empty test case
    with pytest.raises(ValueError, match="Invalid test case format"):
        agent.execute_task({"test_case": {}})

    # Test with missing required fields
    with pytest.raises(ValueError, match="Invalid test case format"):
        agent.execute_task({"test_case": {"steps": ["Step 1"]}})

def test_event_handling():
    """Test event handling"""
    agent = StorageIntegrationAgent()

    # Test validated test case event
    test_case_event = {
        "type": "test_case_validated",
        "test_case": {
            "title": "Event Test Case",
            "description": "Test case from event",
            "precondition": "System is running",
            "automation_needed": "Yes",
            "steps": [
                {
                    "action": "Step 1",
                    "test_data": "Test data 1",
                    "expected_result": "Result 1"
                }
            ]
        }
    }
    agent.handle_event(test_case_event)

    assert len(agent.stored_cases) > 0
    assert "Event Test Case" == agent.stored_cases[-1]["name"]

    # Test status update
    status = agent.update_status()
    assert "cases_stored" in status
    assert status["cases_stored"] == len(agent.stored_cases)