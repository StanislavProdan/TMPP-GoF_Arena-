# DESIGN PATTERN: Decorator
# In this program, Decorator adds battle effects on top of an existing character, such as shield and healing bonus.

from __future__ import annotations

from abc import ABC, abstractmethod

from game.entities import Character
from utils.logger import logger


class CharacterComponent(ABC):
    """Common interface for the base character and all decorators."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @name.setter
    @abstractmethod
    def name(self, value: str) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def hp(self) -> int:
        raise NotImplementedError

    @hp.setter
    @abstractmethod
    def hp(self, value: int) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def max_hp(self) -> int:
        raise NotImplementedError

    @max_hp.setter
    @abstractmethod
    def max_hp(self, value: int) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @description.setter
    @abstractmethod
    def description(self, value: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def take_damage(self, amount: int):
        raise NotImplementedError

    @abstractmethod
    def heal(self, amount: int):
        raise NotImplementedError


class CharacterDecorator(CharacterComponent):
    """Base decorator that forwards all state to the wrapped character."""

    def __init__(self, character: Character):
        self._character = character

    @property
    def name(self) -> str:
        return self._character.name

    @name.setter
    def name(self, value: str) -> None:
        self._character.name = value

    @property
    def hp(self) -> int:
        return self._character.hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._character.hp = value

    @property
    def max_hp(self) -> int:
        return self._character.max_hp

    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self._character.max_hp = value

    @property
    def description(self) -> str:
        return self._character.description

    @description.setter
    def description(self, value: str) -> None:
        self._character.description = value

    def take_damage(self, amount: int):
        return self._character.take_damage(amount)

    def heal(self, amount: int):
        return self._character.heal(amount)


class ShieldDecorator(CharacterDecorator):
    """Reduces incoming damage by a fixed amount."""

    def __init__(self, character: Character, shield_value: int = 5):
        super().__init__(character)
        self.shield_value = max(0, shield_value)

    def take_damage(self, amount: int):
        mitigated = max(0, amount - self.shield_value)
        logger.log(
            f"{self.name} blocks {self.shield_value} dmg with shield -> {mitigated} applied",
            "INFO",
        )
        return self._character.take_damage(mitigated)


class BlessingDecorator(CharacterDecorator):
    """Boosts healing received by a fixed bonus."""

    def __init__(self, character: Character, healing_bonus: int = 4):
        super().__init__(character)
        self.healing_bonus = max(0, healing_bonus)

    def heal(self, amount: int):
        boosted = amount + self.healing_bonus
        logger.log(
            f"{self.name} receives a blessing -> heal {amount} becomes {boosted}",
            "INFO",
        )
        return self._character.heal(boosted)
