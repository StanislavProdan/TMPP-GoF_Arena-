# patterns/creational/prototype.py
# DESIGN PATTERN: Prototype

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from game.entities import Character


class Prototype(ABC):
    """Interfață generică pentru obiecte clonabile."""

    @abstractmethod
    def clone(self):
        pass


class CharacterPrototype(Prototype):
    """Prototype concret pentru obiecte Character."""

    def __init__(self, character: Character):
        self._character = character

    def clone(self) -> Character:
        return deepcopy(self._character)


class PrototypeRegistry:
    """Registry simplu pentru stocarea și clonarea prototipurilor după cheie."""

    def __init__(self):
        self._prototypes: dict[str, Prototype] = {}

    def register(self, key: str, prototype: Prototype):
        self._prototypes[key] = prototype

    def clone(self, key: str):
        if key not in self._prototypes:
            raise KeyError(f"Prototip inexistent: {key}")
        return self._prototypes[key].clone()
