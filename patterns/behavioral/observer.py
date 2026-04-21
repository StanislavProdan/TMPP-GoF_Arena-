# DESIGN PATTERN: Observer
# Keeps battle notifications decoupled from producers.

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class Observer(ABC):
    """Observer interface that receives event updates."""

    @abstractmethod
    def update(self, event: str, payload: Any = None) -> None:
        raise NotImplementedError


class Subject:
    """Subject that allows observers to subscribe and receive notifications."""

    def __init__(self):
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: str, payload: Any = None) -> None:
        for observer in self._observers:
            observer.update(event, payload)


@dataclass
class BattleFeedObserver(Observer):
    """Stores battle events in order for UI or audit output."""

    messages: list[str] = field(default_factory=list)

    def update(self, event: str, payload: Any = None) -> None:
        self.messages.append(f"{event}: {payload}")


@dataclass
class BattleStatsObserver(Observer):
    """Counts event occurrences for lightweight telemetry."""

    counters: dict[str, int] = field(default_factory=dict)

    def update(self, event: str, payload: Any = None) -> None:
        self.counters[event] = self.counters.get(event, 0) + 1
