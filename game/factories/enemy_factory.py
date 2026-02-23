# game/factories/enemy_factory.py
# DESIGN PATTERN: Factory Method

from abc import ABC, abstractmethod
from game.entities import Character
from patterns.creational.builder import CharacterBuilder
import random

class EnemyFactory(ABC):
    """
    Abstract Factory pentru crearea inamicilor.
    Factory Method pattern: subclasele decid ce tip de inamic să creeze.
    """

    @abstractmethod
    def create_enemy(self) -> Character:
        pass

class GoblinFactory(EnemyFactory):
    """
    Factory concret pentru crearea goblinilor.
    """

    def create_enemy(self) -> Character:
        builder = CharacterBuilder()
        return (builder
                .name("Goblin")
                .max_hp(50)
                .initial_hp(50)
                .description("Un goblin mic și viclean, dar slab")
                .build())

class OrcFactory(EnemyFactory):
    """
    Factory concret pentru crearea orc-ilor.
    """

    def create_enemy(self) -> Character:
        builder = CharacterBuilder()
        return (builder
                .name("Orc Warrior")
                .max_hp(90)
                .initial_hp(90)
                .description("Un orc puternic și agresiv")
                .build())

class TrollFactory(EnemyFactory):
    """
    Factory concret pentru crearea troliilor.
    """

    def create_enemy(self) -> Character:
        builder = CharacterBuilder()
        return (builder
                .name("Troll")
                .max_hp(150)
                .initial_hp(150)
                .description("Un troll mare și regenerativ")
                .build())

class RandomEnemyFactory(EnemyFactory):
    """
    Factory pentru crearea unui inamic aleatoriu.
    """

    def create_enemy(self) -> Character:
        factories = [GoblinFactory(), OrcFactory(), TrollFactory()]
        return random.choice(factories).create_enemy()