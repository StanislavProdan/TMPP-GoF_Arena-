# DESIGN PATTERN: Bridge
# In this program, Bridge separates weapon types from damage modes so they can be combined independently.

from __future__ import annotations

from abc import ABC, abstractmethod

from game.entities import Character
from utils.logger import logger


class DamageMode(ABC):
    """Implementor side of the bridge: how damage is transformed."""

    @abstractmethod
    def transform(self, base_damage: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def label(self) -> str:
        raise NotImplementedError


class PhysicalDamage(DamageMode):
    def transform(self, base_damage: int) -> int:
        return base_damage

    def label(self) -> str:
        return "physical"


class EnergyDamage(DamageMode):
    def transform(self, base_damage: int) -> int:
        return int(round(base_damage * 1.25))

    def label(self) -> str:
        return "energy"


class PiercingDamage(DamageMode):
    def transform(self, base_damage: int) -> int:
        return base_damage + 6

    def label(self) -> str:
        return "piercing"


class Weapon(ABC):
    """Abstraction side of the bridge: weapon type independent from damage mode."""

    def __init__(self, name: str, base_damage: int, damage_mode: DamageMode):
        self.name = name
        self.base_damage = base_damage
        self.damage_mode = damage_mode

    def strike(self, attacker: Character, target: Character) -> int:
        damage = max(0, self.damage_mode.transform(self.base_damage))
        logger.log(
            f"{attacker.name} uses {self.name} [{self.damage_mode.label()}] for {damage} dmg",
            "INFO",
        )
        target.take_damage(damage)
        return damage

    def describe(self) -> str:
        return f"{self.name} ({self.base_damage} base, {self.damage_mode.label()} mode)"


class Sword(Weapon):
    pass


class Blaster(Weapon):
    pass


class Spear(Weapon):
    pass
