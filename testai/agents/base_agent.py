"""Base agent implementation for the CrewAI test automation system."""
from contextlib import contextmanager
from typing import Generator, Any, Dict, Optional
import logging
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Configuration model for agents"""
    agent_id: str
    role: str
    goal: str
    backstory: str
    allow_delegation: bool = True
    verbose: bool = False

class BaseAgent:
    """Base class for all agents with common functionality"""

    def __init__(self, config: AgentConfig):
        """Initialize the base agent with configuration"""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a given task

        Args:
            task: Task details and parameters

        Returns:
            Dict containing task execution results
        """
        with self.memory_context():
            try:
                self.logger.info(f"Executing task: {task.get('description', 'No description')}")
                result = self._process_task(task)
                self.logger.info("Task completed successfully")
                return result
            except Exception as e:
                self.logger.error(f"Error executing task: {str(e)}")
                raise

    def delegate_task(self, task: Dict[str, Any], target_agent: Optional[str] = None) -> bool:
        """Delegate a task to another agent

        Args:
            task: Task to delegate
            target_agent: Optional specific agent to delegate to

        Returns:
            bool indicating delegation success
        """
        if not self.config.allow_delegation:
            self.logger.warning("Task delegation not allowed for this agent")
            return False

        try:
            self.logger.info(f"Delegating task to {target_agent or 'any available agent'}")
            # Delegation logic to be implemented by specific agents
            return True
        except Exception as e:
            self.logger.error(f"Error delegating task: {str(e)}")
            return False

    def update_status(self) -> Dict[str, Any]:
        """Update and return the current status of the agent

        Returns:
            Dict containing agent status information
        """
        return {
            "agent_id": self.config.agent_id,
            "role": self.config.role,
            "status": "active",
            "current_task": None  # To be updated by implementing agents
        }

    def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle incoming events

        Args:
            event: Event data to process
        """
        self.logger.info(f"Handling event: {event.get('type', 'Unknown event type')}")
        # Event handling logic to be implemented by specific agents

    @contextmanager
    def memory_context(self) -> Generator:
        """Context manager for memory efficient operations"""
        try:
            yield
        finally:
            self._cleanup()

    def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to process tasks

        Args:
            task: Task to process

        Returns:
            Dict containing processing results
        """
        raise NotImplementedError("_process_task must be implemented by child classes")

    def _cleanup(self):
        """Clean up resources after task execution"""
        # Implement cleanup logic in child classes if needed
        pass