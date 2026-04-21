# DESIGN PATTERN: Iterator
# Provides sequential access to combat entries without exposing collection internals.

from __future__ import annotations


class CombatLogIterator:
    def __init__(self, entries: list[str], reverse: bool = False):
        self._entries = entries
        self._reverse = reverse
        self._index = len(entries) - 1 if reverse else 0

    def __iter__(self):
        return self

    def __next__(self) -> str:
        if self._reverse:
            if self._index < 0:
                raise StopIteration
            value = self._entries[self._index]
            self._index -= 1
            return value

        if self._index >= len(self._entries):
            raise StopIteration
        value = self._entries[self._index]
        self._index += 1
        return value


class CombatLogCollection:
    def __init__(self):
        self._entries: list[str] = []

    def add(self, message: str) -> None:
        self._entries.append(message)

    def __iter__(self) -> CombatLogIterator:
        return CombatLogIterator(self._entries, reverse=False)

    def reversed_iter(self) -> CombatLogIterator:
        return CombatLogIterator(self._entries, reverse=True)

    def __len__(self) -> int:
        return len(self._entries)
