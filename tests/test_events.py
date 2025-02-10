"""Test event system functionality"""
import pytest
from datetime import datetime
from events.event import Event, EventType
from events.event_manager import EventManager

def test_event_manager_singleton():
    """Test EventManager maintains singleton pattern"""
    manager1 = EventManager()
    manager2 = EventManager()
    assert manager1 is manager2

def test_subscribe_and_publish():
    """Test basic subscribe and publish functionality"""
    manager = EventManager()
    received_events = []
    
    def callback(event):
        received_events.append(event)
    
    # Subscribe to test event
    manager.subscribe(EventType.TASK_CREATED, callback)
    
    # Create and publish test event
    test_event = Event(
        event_type=EventType.TASK_CREATED,
        source="test",
        timestamp=datetime.now(),
        data={"task_id": "123"}
    )
    manager.publish(test_event)
    
    assert len(received_events) == 1
    assert received_events[0].event_type == EventType.TASK_CREATED
    assert received_events[0].data["task_id"] == "123"

def test_multiple_subscribers():
    """Test multiple subscribers receive events"""
    manager = EventManager()
    count1, count2 = 0, 0
    
    def callback1(event):
        nonlocal count1
        count1 += 1
    
    def callback2(event):
        nonlocal count2
        count2 += 1
    
    manager.subscribe(EventType.TASK_COMPLETED, callback1)
    manager.subscribe(EventType.TASK_COMPLETED, callback2)
    
    test_event = Event(
        event_type=EventType.TASK_COMPLETED,
        source="test",
        timestamp=datetime.now(),
        data={"result": "success"}
    )
    manager.publish(test_event)
    
    assert count1 == 1
    assert count2 == 1
