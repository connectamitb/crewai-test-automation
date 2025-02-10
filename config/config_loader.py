"""Configuration loader for the CrewAI test automation system."""
from typing import Dict, Any
import os
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

class ToolConfig(BaseModel):
    """Tool configuration model"""
    enabled: bool = True
    timeout: int = Field(default=30, ge=0)
    supported_formats: list[str] = Field(default_factory=list)

class AgentConfig(BaseModel):
    """Agent configuration model"""
    id: str
    role: str
    goal: str
    backstory: str
    allow_delegation: bool = True
    verbose: bool = False

class OrchestrationConfig(BaseModel):
    """Orchestration configuration model"""
    strategy: str = "hierarchical"
    retry_policy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_attempts": 3,
            "backoff_factor": 2
        }
    )

class ExternalConfig(BaseModel):
    """External integrations configuration"""
    llm: Dict[str, str] = Field(
        default_factory=lambda: {
            "primary": "openai",
            "fallback": "cohere",
            "model": "gpt-4"
        }
    )
    vector_db: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "weaviate",
            "batch_size": 100
        }
    )

class SystemConfig(BaseModel):
    """Complete system configuration"""
    agents: Dict[str, AgentConfig]
    orchestration: OrchestrationConfig
    tools: Dict[str, ToolConfig]
    external: ExternalConfig

class ConfigLoader:
    """Configuration loader with hot-reload capability"""
    _instance = None
    _config: SystemConfig = None
    _config_path: str = None

    def __new__(cls, config_path: str = None):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = None):
        if self._config_path != config_path:
            self._config_path = config_path or os.path.join("config", "config.yaml")
            self.reload_config()

    def reload_config(self) -> None:
        """Reload configuration from YAML file"""
        try:
            config_file = Path(self._config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {self._config_path}")

            with open(config_file, 'r') as f:
                yaml_config = yaml.safe_load(f)
                self._config = SystemConfig(**yaml_config)
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {str(e)}")

    @property
    def config(self) -> SystemConfig:
        """Get current configuration"""
        return self._config

    def get_agent_config(self, agent_id: str) -> AgentConfig:
        """Get configuration for specific agent"""
        if agent_id not in self._config.agents:
            raise ValueError(f"Agent configuration not found for: {agent_id}")
        return self._config.agents[agent_id]

    def get_tool_config(self, tool_name: str) -> ToolConfig:
        """Get configuration for specific tool"""
        if tool_name not in self._config.tools:
            raise ValueError(f"Tool configuration not found for: {tool_name}")
        return self._config.tools[tool_name]
