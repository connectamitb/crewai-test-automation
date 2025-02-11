"""Test suite for CrewAI agent implementations."""
import pytest
from typing import Dict, Any

from testai.agents.data_collector_agent import DataCollectorAgent
from testai.agents.analyzer_agent import AnalyzerAgent
from testai.agents.strategist_agent import StrategistAgent

def test_data_collector_agent():
    """Test DataCollectorAgent functionality"""
    agent = DataCollectorAgent()

    # Test agent initialization
    assert agent.config.agent_id == "data_collector_001"
    assert agent.config.role == "Data Collection Specialist"

    # Test task execution
    task = {
        "source": "test_requirements",
        "timestamp": "2024-02-10T12:00:00"
    }
    result = agent.execute_task(task)

    assert result["status"] == "success"
    assert "data" in result
    assert "metadata" in result
    assert result["metadata"]["source"] == "test_requirements"

def test_analyzer_agent():
    """Test AnalyzerAgent functionality"""
    agent = AnalyzerAgent()

    # Test agent initialization
    assert agent.config.agent_id == "analyzer_001"
    assert agent.config.role == "Test Analysis Expert"

    # Test task execution
    task = {
        "data": {
            "requirements": "Test login functionality",
            "priority": "high"
        },
        "timestamp": "2024-02-10T12:00:00"
    }
    result = agent.execute_task(task)

    assert result["status"] == "success"
    assert "result" in result
    assert "insights" in result["result"]
    assert "recommendations" in result["result"]

def test_strategist_agent():
    """Test StrategistAgent functionality"""
    agent = StrategistAgent()

    # Test agent initialization
    assert agent.config.agent_id == "strategist_001"
    assert agent.config.role == "Test Strategy Designer"

    # Test task execution
    task = {
        "analysis": {
            "complexity": "medium",
            "coverage": 0.85,
            "risk_areas": ["authentication", "data validation"]
        },
        "timestamp": "2024-02-10T12:00:00"
    }
    result = agent.execute_task(task)

    assert result["status"] == "success"
    assert "strategy" in result
    assert "approach" in result["strategy"]
    assert "coverage_plan" in result["strategy"]
    assert "risk_mitigation" in result["strategy"]

def test_agent_event_handling():
    """Test event handling across all agents"""
    agents = [
        DataCollectorAgent(),
        AnalyzerAgent(),
        StrategistAgent()
    ]

    for agent in agents:
        # Test configuration update event
        config_event = {
            "type": "config_update",
            "config": get_agent_config(agent)
        }
        agent.handle_event(config_event)

        # Verify status update includes event handling
        status = agent.update_status()
        assert isinstance(status, dict)
        assert "agent_id" in status

def test_agent_delegation():
    """Test task delegation functionality"""
    agents = [
        DataCollectorAgent(),
        AnalyzerAgent(),
        StrategistAgent()
    ]

    task = {"type": "test_task"}
    target = "test_agent"

    for agent in agents:
        # Test successful delegation
        assert agent.delegate_task(task, target) == True

        # Test delegation with disabled flag
        agent.config.allow_delegation = False
        assert agent.delegate_task(task, target) == False

def get_agent_config(agent: Any) -> Dict[str, Any]:
    """Helper function to get appropriate configuration for each agent type"""
    if isinstance(agent, DataCollectorAgent):
        return {
            "source_type": "requirements",
            "max_items": 200,
            "timeout": 30
        }
    elif isinstance(agent, AnalyzerAgent):
        return {
            "analysis_depth": "detailed",
            "max_insights": 15,
            "priority_threshold": 0.8
        }
    else:  # StrategistAgent
        return {
            "coverage_target": 0.95,
            "risk_tolerance": "low",
            "optimization_level": "aggressive"
        }