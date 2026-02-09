# patterns/creational/builder.py
# DESIGN PATTERN: Builder
# Provides a fluent interface to construct complex Character objects step-by-step

from game.entities import Character

class CharacterBuilder:
    def __init__(self):
        self._name = "Unnamed"
        self._max_hp = 100
        self._initial_hp = None
        self._description = ""

    def name(self, name: str):
        self._name = name
        return self

    def max_hp(self, max_hp: int):
        self._max_hp = max_hp
        if self._initial_hp is None:
            self._initial_hp = max_hp
        return self

    def initial_hp(self, hp: int):
        self._initial_hp = hp
        return self

    def description(self, desc: str):
        self._description = desc
        return self

    def build(self) -> Character:
        hp = self._initial_hp if self._initial_hp is not None else self._max_hp
        char = Character(self._name, self._max_hp)
        char.hp = hp  # suprascriem hp-ul inițial dacă e diferit
        if self._description:
            print(f"Descriere: {self._description}")
        return char