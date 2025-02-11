"""Test suite for RequirementInputAgent."""
import pytest
from testai.agents.requirement_input import RequirementInputAgent, RequirementData

def test_requirement_input_agent_initialization():
    """Test RequirementInputAgent initialization"""
    agent = RequirementInputAgent()
    assert agent.config.agent_id == "requirement_input_001"
    assert agent.config.role == "Requirement Input Processor"
    assert isinstance(agent.processed_requirements, list)

def test_requirement_processing():
    """Test basic requirement processing"""
    agent = RequirementInputAgent()
    task = {
        "raw_text": "The system must verify user authentication before accessing protected resources.",
        "wireframe_paths": ["path/to/wireframe1.png"],
        "metadata": {"priority": "high"}
    }
    
    result = agent.execute_task(task)
    
    assert result["status"] == "success"
    assert "processed_requirement" in result
    assert result["processed_requirement"]["text"]
    assert result["processed_requirement"]["validation_status"]["is_valid"]

def test_requirement_validation():
    """Test requirement validation logic"""
    agent = RequirementInputAgent()
    
    # Test valid requirement
    valid_task = {
        "raw_text": "The system must validate user input for security.",
        "metadata": {"type": "security"}
    }
    valid_result = agent.execute_task(valid_task)
    assert valid_result["processed_requirement"]["validation_status"]["is_valid"]
    
    # Test invalid requirement (too short)
    invalid_task = {
        "raw_text": "Test",
        "metadata": {"type": "test"}
    }
    invalid_result = agent.execute_task(invalid_task)
    assert not invalid_result["processed_requirement"]["validation_status"]["is_valid"]

def test_wireframe_processing():
    """Test wireframe processing"""
    agent = RequirementInputAgent()
    task = {
        "raw_text": "Implement login page according to wireframe.",
        "wireframe_paths": ["wireframes/login.png", "wireframes/dashboard.png"]
    }
    
    result = agent.execute_task(task)
    wireframes = result["processed_requirement"]["wireframes"]
    
    assert len(wireframes) == 2
    assert all(w["status"] in ["processed", "error"] for w in wireframes)

def test_event_handling():
    """Test event handling"""
    agent = RequirementInputAgent()
    
    # Test requirement update event
    requirement_event = {
        "type": "requirement_update",
        "requirement": "New requirement to process"
    }
    agent.handle_event(requirement_event)
    
    # Verify the requirement was processed
    assert len(agent.processed_requirements) > 0
    
    # Test status update
    status = agent.update_status()
    assert "requirements_processed" in status
    assert status["requirements_processed"] == len(agent.processed_requirements)
