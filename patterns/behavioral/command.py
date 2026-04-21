# DESIGN PATTERN: Command
# Encapsulates character actions as objects and supports undo for reversible changes.

from __future__ import annotations

from abc import ABC, abstractmethod

from game.entities import Character
from utils.logger import logger


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def undo(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def label(self) -> str:
        raise NotImplementedError


class DamageCommand(Command):
    def __init__(self, target: Character, amount: int):
        self.target = target
        self.amount = max(0, amount)
        self._previous_hp: int | None = None

    @property
    def label(self) -> str:
        return f"Damage {self.target.name} by {self.amount}"

    def execute(self) -> None:
        self._previous_hp = self.target.hp
        self.target.take_damage(self.amount)

    def undo(self) -> None:
        if self._previous_hp is None:
            return
        self.target.hp = self._previous_hp
        logger.log(f"Undo command: {self.label}", "INFO")


class HealCommand(Command):
    def __init__(self, target: Character, amount: int):
        self.target = target
        self.amount = max(0, amount)
        self._previous_hp: int | None = None

    @property
    def label(self) -> str:
        return f"Heal {self.target.name} by {self.amount}"

    def execute(self) -> None:
        self._previous_hp = self.target.hp
        self.target.heal(self.amount)

    def undo(self) -> None:
        if self._previous_hp is None:
            return
        self.target.hp = self._previous_hp
        logger.log(f"Undo command: {self.label}", "INFO")


class CommandInvoker:
    """Invoker that executes commands and keeps undo history."""

    def __init__(self):
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append(command)
        logger.log(f"Command executed: {command.label}", "INFO")

    def undo_last(self) -> bool:
        if not self._history:
            return False
        command = self._history.pop()
        command.undo()
        return True

    def history_labels(self) -> list[str]:
        return [command.label for command in self._history]
