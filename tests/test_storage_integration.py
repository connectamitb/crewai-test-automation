"""Test suite for StorageIntegrationAgent."""
import pytest
from testai.agents.storage_integration_agent import StorageIntegrationAgent

def test_storage_integration_agent_initialization():
    """Test StorageIntegrationAgent initialization"""
    agent = StorageIntegrationAgent()
    assert agent.config.agent_id == "storage_integration_001"
    assert agent.config.role == "Storage Integration Manager"
    assert isinstance(agent.stored_cases, list)

def test_basic_storage():
    """Test basic test case storage"""
    agent = StorageIntegrationAgent()
    test_case = {
        "title": "Test Login Feature",
        "description": "Verify user login functionality",
        "steps": ["Navigate to login page", "Enter credentials"],
        "expected_results": ["Page loads successfully", "User is logged in"],
        "metadata": {"priority": "High"}
    }

    result = agent.execute_task({"test_case": test_case})

    assert result["status"] == "success"
    assert result["stored_case"]["title"] == test_case["title"]
    assert len(agent.stored_cases) == 1

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
            "steps": ["Step 1"],
            "expected_results": ["Result 1"]
        }
    }
    agent.handle_event(test_case_event)

    assert len(agent.stored_cases) > 0
    assert "Event Test Case" == agent.stored_cases[-1]["title"]

    # Test status update
    status = agent.update_status()
    assert "cases_stored" in status
    assert status["cases_stored"] == len(agent.stored_cases)