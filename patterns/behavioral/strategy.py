# DESIGN PATTERN: Strategy
# Encapsulates interchangeable battle algorithms for computing outgoing damage.

from __future__ import annotations

import random
from abc import ABC, abstractmethod

from game.entities import Character
from utils.logger import logger


class AttackStrategy(ABC):
    """Strategy interface for attack behavior."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def compute_damage(self, base_damage: int) -> int:
        raise NotImplementedError


class BalancedStrategy(AttackStrategy):
    @property
    def name(self) -> str:
        return "balanced"

    def compute_damage(self, base_damage: int) -> int:
        return max(0, base_damage)


class AggressiveStrategy(AttackStrategy):
    @property
    def name(self) -> str:
        return "aggressive"

    def compute_damage(self, base_damage: int) -> int:
        return max(0, int(round(base_damage * 1.4)))


class DefensiveStrategy(AttackStrategy):
    @property
    def name(self) -> str:
        return "defensive"

    def compute_damage(self, base_damage: int) -> int:
        return max(0, int(round(base_damage * 0.75)))


class ChaosStrategy(AttackStrategy):
    @property
    def name(self) -> str:
        return "chaos"

    def compute_damage(self, base_damage: int) -> int:
        spread = random.randint(-4, 6)
        return max(0, base_damage + spread)


class AttackContext:
    """Context that delegates attack damage calculation to the active strategy."""

    def __init__(self, strategy: AttackStrategy):
        self._strategy = strategy

    @property
    def strategy(self) -> AttackStrategy:
        return self._strategy

    def set_strategy(self, strategy: AttackStrategy) -> None:
        self._strategy = strategy

    def attack(self, attacker: Character, target: Character, base_damage: int) -> int:
        damage = self._strategy.compute_damage(base_damage)
        logger.log(
            f"{attacker.name} uses {self._strategy.name} strategy -> {damage} dmg",
            "INFO",
        )
        target.take_damage(damage)
        return damage
