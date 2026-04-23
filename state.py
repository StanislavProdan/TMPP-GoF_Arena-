"""Pattern: State.
schimba comportamentul unui obiect in functie de starea interna curenta.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TrafficLightState(ABC):
    @abstractmethod
    def next_state(self, context: "TrafficLight") -> None:
        raise NotImplementedError

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError


class RedState(TrafficLightState):
    def next_state(self, context: "TrafficLight") -> None:
        context.state = GreenState()

    def name(self) -> str:
        return "RED"


class GreenState(TrafficLightState):
    def next_state(self, context: "TrafficLight") -> None:
        context.state = YellowState()

    def name(self) -> str:
        return "GREEN"


class YellowState(TrafficLightState):
    def next_state(self, context: "TrafficLight") -> None:
        context.state = RedState()

    def name(self) -> str:
        return "YELLOW"


class TrafficLight:
    def __init__(self) -> None:
        self.state: TrafficLightState = RedState()

    def change(self) -> str:
        current = self.state.name()
        self.state.next_state(self)
        return f"{current} -> {self.state.name()}"


def demo() -> None:
    light = TrafficLight()
    for _ in range(5):
        print(light.change())


if __name__ == "__main__":
    demo()
