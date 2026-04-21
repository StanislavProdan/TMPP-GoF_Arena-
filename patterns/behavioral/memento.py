# DESIGN PATTERN: Memento
# Captures and restores character state snapshots without exposing internals.

from __future__ import annotations

from dataclasses import dataclass

from game.entities import Character


@dataclass(frozen=True)
class CharacterMemento:
    name: str
    max_hp: int
    hp: int
    description: str


class CharacterStateOriginator:
    """Creates snapshots and restores Character state from mementos."""

    @staticmethod
    def save(character: Character) -> CharacterMemento:
        return CharacterMemento(
            name=character.name,
            max_hp=character.max_hp,
            hp=character.hp,
            description=character.description,
        )

    @staticmethod
    def restore(character: Character, memento: CharacterMemento) -> None:
        character.name = memento.name
        character.max_hp = memento.max_hp
        character.hp = max(0, min(memento.hp, memento.max_hp))
        character.description = memento.description


class MementoCaretaker:
    """Stores a history of snapshots for undo-like recovery flows."""

    def __init__(self):
        self._history: list[CharacterMemento] = []

    def push(self, memento: CharacterMemento) -> None:
        self._history.append(memento)

    def pop(self) -> CharacterMemento | None:
        if not self._history:
            return None
        return self._history.pop()

    def size(self) -> int:
        return len(self._history)
