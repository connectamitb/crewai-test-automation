"""Test suite for TestCaseMappingAgent."""
import pytest
from testai.agents.test_case_mapping import TestCaseMappingAgent, TestCaseOutput, TestCaseFormat

def test_test_case_mapping_agent_initialization():
    """Test TestCaseMappingAgent initialization"""
    agent = TestCaseMappingAgent()
    assert agent.config.agent_id == "test_case_mapping_001"
    assert agent.config.role == "Test Case Designer"
    assert isinstance(agent.generated_cases, list)

def test_test_case_generation():
    """Test basic test case generation"""
    agent = TestCaseMappingAgent()
    task = {
        "parsed_requirement": {
            "primary_action": "validate",
            "target_object": "user credentials",
            "expected_outcome": "grant access to the system",
            "confidence_score": 0.9,
            "original_text": "System should validate user credentials and grant access"
        }
    }
    
    result = agent.execute_task(task)
    
    assert result["status"] == "success"
    assert "test_case" in result
    assert "validation" in result
    assert result["validation"]["is_valid"]
    
    test_case = TestCaseOutput(**result["test_case"])
    assert "validate" in test_case.title.lower()
    assert "user credentials" in test_case.description.lower()

def test_test_case_format():
    """Test Gherkin format structure"""
    agent = TestCaseMappingAgent()
    task = {
        "parsed_requirement": {
            "primary_action": "process",
            "target_object": "payment transaction",
            "expected_outcome": "complete successfully",
            "additional_context": {"tags": ["critical"]}
        }
    }
    
    result = agent.execute_task(task)
    test_case = TestCaseOutput(**result["test_case"])
    
    assert len(test_case.format.given) > 0
    assert len(test_case.format.when) > 0
    assert len(test_case.format.then) > 0
    assert test_case.format.priority == "high"  # Should be high due to critical tag

def test_test_case_validation():
    """Test test case validation"""
    agent = TestCaseMappingAgent()
    
    # Test with complete data
    complete_task = {
        "parsed_requirement": {
            "primary_action": "verify",
            "target_object": "email format",
            "expected_outcome": "show validation message",
            "additional_context": {"tags": ["validation"]}
        }
    }
    
    complete_result = agent.execute_task(complete_task)
    assert complete_result["validation"]["is_valid"]
    assert all(complete_result["validation"]["checks"].values())

def test_event_handling():
    """Test event handling"""
    agent = TestCaseMappingAgent()
    
    # Test requirement parsed event
    parsed_event = {
        "type": "requirement_parsed",
        "parsed_requirement": {
            "primary_action": "check",
            "target_object": "login form",
            "expected_outcome": "display error message"
        }
    }
    agent.handle_event(parsed_event)
    
    # Verify the test case was generated
    assert len(agent.generated_cases) > 0
    
    # Test status update
    status = agent.update_status()
    assert "test_cases_generated" in status
    assert status["test_cases_generated"] == len(agent.generated_cases)
