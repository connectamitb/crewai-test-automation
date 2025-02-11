"""Test suite for NLPParsingAgent."""
import pytest
from testai.agents.nlp_parsing import NLPParsingAgent, ParsedRequirement

def test_nlp_parsing_agent_initialization():
    """Test NLPParsingAgent initialization"""
    agent = NLPParsingAgent()
    assert agent.config.agent_id == "nlp_parsing_001"
    assert agent.config.role == "NLP Parser"
    assert isinstance(agent.parsed_requirements, list)

def test_requirement_parsing():
    """Test basic requirement parsing"""
    agent = NLPParsingAgent()
    task = {
        "cleaned_requirement": "Verify user authentication process shows success message after login"
    }
    
    result = agent.execute_task(task)
    
    assert result["status"] == "success"
    assert "parsed_requirement" in result
    assert "validation" in result
    assert result["validation"]["is_valid"]

def test_parsed_structure_validation():
    """Test parsed requirement validation"""
    agent = NLPParsingAgent()
    
    # Test with well-formed requirement
    valid_task = {
        "cleaned_requirement": "Validate payment processing completes with confirmation"
    }
    valid_result = agent.execute_task(valid_task)
    assert valid_result["validation"]["is_valid"]
    
    # Test with minimal requirement
    minimal_task = {
        "cleaned_requirement": "Test login"
    }
    minimal_result = agent.execute_task(minimal_task)
    parsed = ParsedRequirement(**minimal_result["parsed_requirement"])
    assert parsed.primary_action == "Test"
    assert parsed.target_object == "login"

def test_confidence_scoring():
    """Test confidence score calculation"""
    agent = NLPParsingAgent()
    task = {
        "cleaned_requirement": "Verify user registration process completes successfully"
    }
    
    result = agent.execute_task(task)
    parsed = ParsedRequirement(**result["parsed_requirement"])
    
    assert 0 <= parsed.confidence_score <= 1
    assert result["validation"]["checks"]["confidence_acceptable"]

def test_event_handling():
    """Test event handling"""
    agent = NLPParsingAgent()
    
    # Test requirement update event
    requirement_event = {
        "type": "requirement_update",
        "requirement": "Check email validation displays error for invalid format"
    }
    agent.handle_event(requirement_event)
    
    # Verify the requirement was processed
    assert len(agent.parsed_requirements) > 0
    
    # Test status update
    status = agent.update_status()
    assert "requirements_parsed" in status
    assert status["requirements_parsed"] == len(agent.parsed_requirements)
