"""Task model and related functionality for CrewAI test automation."""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ExecutionMode(str, Enum):
    """Task execution modes"""
    SYNC = "sync"
    ASYNC = "async"

class Priority(int, Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class RetryPolicy(BaseModel):
    """Configuration for task retry behavior"""
    max_attempts: int = 3
    backoff_factor: float = 2.0
    max_delay: int = 300  # Maximum delay in seconds

class Task(BaseModel):
    """Task model with validation"""
    task_id: str
    description: str
    expected_output: Dict[str, Any]
    execution_mode: ExecutionMode = ExecutionMode.SYNC
    priority: Priority = Priority.MEDIUM
    dependencies: List[str] = Field(default_factory=list)
    timeout: Optional[int] = 60  # Timeout in seconds
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    
    class Config:
        """Pydantic model configuration"""
        use_enum_values = True

    def validate_dependencies(self, available_tasks: List[str]) -> bool:
        """Validate that all dependencies exist
        
        Args:
            available_tasks: List of existing task IDs

        Returns:
            bool indicating if all dependencies are valid
        """
        return all(dep in available_tasks for dep in self.dependencies)
