# DESIGN PATTERN: Composite

from __future__ import annotations

from abc import ABC, abstractmethod

from game.entities import Character


class FighterNode(ABC):
    """Common interface for both single fighters and groups."""

    @abstractmethod
    def total_hp(self) -> int:
        pass

    @abstractmethod
    def total_max_hp(self) -> int:
        pass

    @abstractmethod
    def describe(self) -> str:
        pass


class CharacterLeaf(FighterNode):
    """Leaf node: wraps one Character."""

    def __init__(self, character: Character):
        self.character = character

    def total_hp(self) -> int:
        return self.character.hp

    def total_max_hp(self) -> int:
        return self.character.max_hp

    def describe(self) -> str:
        return f"{self.character.name} ({self.character.hp}/{self.character.max_hp})"


class Squad(FighterNode):
    """Composite node: stores leaves or other squads recursively."""

    def __init__(self, name: str):
        self.name = name
        self._members: list[FighterNode] = []

    def add(self, node: FighterNode):
        self._members.append(node)

    def remove(self, node: FighterNode):
        self._members.remove(node)

    def total_hp(self) -> int:
        return sum(member.total_hp() for member in self._members)

    def total_max_hp(self) -> int:
        return sum(member.total_max_hp() for member in self._members)

    def describe(self) -> str:
        members = ", ".join(member.describe() for member in self._members) if self._members else "(empty)"
        return f"{self.name}: {self.total_hp()}/{self.total_max_hp()} -> [{members}]"
