"""Event system implementation for CrewAI test automation."""
from typing import Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

class EventType(str, Enum):
    """Standard event types in the system"""
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    REQUIREMENT_UPDATE = "requirement_update"
    TEST_EXECUTION = "test_execution"
    CONFIG_CHANGED = "config_changed"

class Event(BaseModel):
    """Event model with validation"""
    event_type: EventType
    source: str
    timestamp: datetime = datetime.now()
    data: Dict[str, Any]
