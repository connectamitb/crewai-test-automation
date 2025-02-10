"""Test configuration loader functionality"""
import pytest
from config.config_loader import ConfigLoader, SystemConfig

def test_config_loader():
    """Test basic configuration loading"""
    loader = ConfigLoader()
    config = loader.config

    # Verify it's a valid SystemConfig instance
    assert isinstance(config, SystemConfig)

    # Verify required sections exist
    assert config.agents
    assert config.orchestration
    assert config.tools
    assert config.external

    # Verify specific agent configuration
    data_collector = loader.get_agent_config("data_collector")
    assert data_collector.id == "data_collector_001"
    assert data_collector.role == "Data Collection Specialist"

    # Verify tool configuration
    web_scraper = loader.get_tool_config("web_scraper")
    assert web_scraper.enabled
    assert web_scraper.timeout == 30