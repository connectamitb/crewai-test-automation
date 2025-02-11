"""Test suite for ValidationAgent."""
import pytest
from testai.agents.validation_agent import ValidationAgent, ValidationCriteria, ValidationResult

def test_validation_agent_initialization():
    """Test ValidationAgent initialization"""
    agent = ValidationAgent()
    assert agent.config.agent_id == "validation_001"
    assert agent.config.role == "Test Case Validator"
    assert isinstance(agent.validation_history, list)
    assert isinstance(agent.criteria, ValidationCriteria)

def test_basic_validation():
    """Test basic validation functionality"""
    agent = ValidationAgent()
    
    # Test with valid test case
    valid_test_case = {
        "title": "Test Login Functionality",
        "description": "Verify that users can successfully log in with valid credentials",
        "format": {
            "given": ["User is on login page", "User has valid credentials"],
            "when": ["User enters username", "User enters password", "User clicks login"],
            "then": ["User should be logged in", "Dashboard should be displayed"]
        }
    }
    
    result = agent.execute_task({"test_case": valid_test_case})
    validation = result["validation_result"]
    
    assert result["status"] == "success"
    assert validation["is_valid"]
    assert validation["score"] == 1.0
    assert len(validation["suggestions"]) == 0

def test_invalid_test_case():
    """Test validation with invalid test case"""
    agent = ValidationAgent()
    
    # Test with incomplete test case
    incomplete_test_case = {
        "title": "Test Login",
        "description": "Short desc",
        "format": {
            "given": ["User is on login page"],
            "when": ["User logs in"],
            # Missing 'then' section
        }
    }
    
    result = agent.execute_task({"test_case": incomplete_test_case})
    validation = result["validation_result"]
    
    assert not validation["is_valid"]
    assert validation["score"] < 1.0
    assert len(validation["suggestions"]) > 0
    assert not validation["checks"]["description_length"]
    assert not validation["checks"]["has_all_sections"]

def test_validation_criteria():
    """Test validation criteria handling"""
    agent = ValidationAgent()
    
    # Test with minimum requirements
    minimal_test_case = {
        "title": "Minimal Test",
        "description": "This is a minimal but valid test case description",
        "format": {
            "given": ["Condition 1", "Condition 2"],
            "when": ["Action 1", "Action 2"],
            "then": ["Result 1", "Result 2"]
        }
    }
    
    result = agent.execute_task({"test_case": minimal_test_case})
    validation = result["validation_result"]
    
    assert validation["is_valid"]
    assert validation["checks"]["min_steps_met"]
    assert validation["checks"]["description_length"]

def test_event_handling():
    """Test event handling"""
    agent = ValidationAgent()
    
    # Test test case creation event
    test_case_event = {
        "type": "test_case_created",
        "test_case": {
            "title": "Event Test Case",
            "description": "Test case created through event handling",
            "format": {
                "given": ["Precondition 1", "Precondition 2"],
                "when": ["Action 1", "Action 2"],
                "then": ["Expected Result 1", "Expected Result 2"]
            }
        }
    }
    agent.handle_event(test_case_event)
    
    # Verify the validation was performed
    assert len(agent.validation_history) > 0
    
    # Test configuration update event
    config_event = {
        "type": "config_update",
        "config": {
            "required_fields": ["title", "description", "steps"],
            "min_steps": 3,
            "min_description_length": 30,
            "required_sections": ["given", "when", "then"]
        }
    }
    agent.handle_event(config_event)
    
    # Verify criteria was updated
    assert agent.criteria.min_steps == 3
    assert agent.criteria.min_description_length == 30

def test_validation_suggestions():
    """Test validation suggestions generation"""
    agent = ValidationAgent()
    
    # Test case missing required elements
    incomplete_test_case = {
        "title": "",  # Missing title
        "description": "Short",  # Too short
        "format": {
            "given": ["Step 1"],  # Not enough steps
            "when": ["Step 1"],
            # Missing 'then' section
        }
    }
    
    result = agent.execute_task({"test_case": incomplete_test_case})
    validation = result["validation_result"]
    
    assert len(validation["suggestions"]) > 0
    assert any("title" in suggestion.lower() for suggestion in validation["suggestions"])
    assert any("description" in suggestion.lower() for suggestion in validation["suggestions"])
    assert any("section" in suggestion.lower() for suggestion in validation["suggestions"])
