"""Pattern: Chain of Responsibility.
trimite o cerere printr-un lant de handlere, iar primul care poate sa o proceseze se ocupa de ea.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class RequestHandler(ABC):
    def __init__(self) -> None:
        self._next: RequestHandler | None = None

    def set_next(self, handler: "RequestHandler") -> "RequestHandler":
        self._next = handler
        return handler

    def handle(self, value: int) -> str:
        if self._can_handle(value):
            return self._process(value)
        if self._next:
            return self._next.handle(value)
        return f"Nu exista handler pentru valoarea: {value}"

    @abstractmethod
    def _can_handle(self, value: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _process(self, value: int) -> str:
        raise NotImplementedError


class LowValueHandler(RequestHandler):
    def _can_handle(self, value: int) -> bool:
        return value < 10

    def _process(self, value: int) -> str:
        return f"LowValueHandler a procesat {value}"


class MediumValueHandler(RequestHandler):
    def _can_handle(self, value: int) -> bool:
        return 10 <= value < 100

    def _process(self, value: int) -> str:
        return f"MediumValueHandler a procesat {value}"


class HighValueHandler(RequestHandler):
    def _can_handle(self, value: int) -> bool:
        return value >= 100

    def _process(self, value: int) -> str:
        return f"HighValueHandler a procesat {value}"


def demo() -> None:
    low = LowValueHandler()
    medium = MediumValueHandler()
    high = HighValueHandler()
    low.set_next(medium).set_next(high)

    for value in [5, 42, 130]:
        print(low.handle(value))


if __name__ == "__main__":
    demo()
