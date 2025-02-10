"""Event manager singleton implementation."""
from typing import Dict, Set, Callable, Any
import logging
from .event import Event

class EventManager:
    """Singleton event manager for handling event distribution"""
    _instance = None
    _subscribers: Dict[str, Set[Callable]] = {}
    _logger = logging.getLogger(__name__)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance._subscribers = {}
        return cls._instance

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to specific event type
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)
        self._logger.debug(f"Subscribed to {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from specific event type
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to remove from subscribers
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
            self._logger.debug(f"Unsubscribed from {event_type}")

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers
        
        Args:
            event: Event to publish
        """
        event_type = event.event_type
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    self._logger.error(f"Error in event callback: {str(e)}")
        self._logger.debug(f"Published event: {event_type}")

    def get_subscribers(self, event_type: str) -> Set[Callable]:
        """Get all subscribers for an event type
        
        Args:
            event_type: Type of event to get subscribers for
            
        Returns:
            Set of callback functions subscribed to the event
        """
        return self._subscribers.get(event_type, set())
