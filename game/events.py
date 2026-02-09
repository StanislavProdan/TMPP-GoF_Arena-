# game/events.py
# DESIGN PATTERN: Observer
# Implements a publish-subscribe mechanism for decoupled event handling

from typing import Callable, Any, Dict

class EventBus:
    """Observer pattern - bus central pentru evenimente în joc."""
    
    def __init__(self):
        self._listeners: Dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
        # print(f"[DEBUG] Subscribed {callback.__name__} la {event_type}")

    def publish(self, event_type: str, data: Any = None):
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                callback(data)