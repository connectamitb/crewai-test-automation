"""Base agent implementation for CrewAI test automation system."""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Configuration for role-based agents"""
    agent_id: str
    role: str
    goal: str
    backstory: str
    allow_delegation: bool = True
    verbose: bool = False

class BaseAgent(ABC):
    """Abstract base class for all CrewAI agents"""

    def __init__(self, config: AgentConfig):
        """Initialize the agent with role-based configuration"""
        self.config = config
        self.logger = logging.getLogger(f"agent.{self.config.role}")
        self.logger.setLevel(logging.DEBUG)

    @abstractmethod
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a given task
        
        Args:
            task: Task details including description, expected output,
                 execution mode, priority, and dependencies

        Returns:
            Dict containing execution results and status
        """
        pass

    @abstractmethod
    def delegate_task(self, task: Dict[str, Any], target_agent: Optional[str] = None) -> bool:
        """Delegate a task to another agent
        
        Args:
            task: Task to delegate
            target_agent: Optional specific agent to delegate to

        Returns:
            bool indicating delegation success
        """
        pass

    @abstractmethod
    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent
        
        Returns:
            Dict containing agent status information
        """
        pass

    @abstractmethod
    def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle incoming events
        
        Args:
            event: Event data to process
        """
        pass

    def _log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log agent actions with telemetry
        
        Args:
            action: Name of the action being performed
            details: Additional context about the action
        """
        self.logger.info(
            f"Agent {self.config.agent_id} ({self.config.role}) - {action}",
            extra={
                "agent_id": self.config.agent_id,
                "role": self.config.role,
                "action": action,
                "details": details
            }
        )
