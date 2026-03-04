# game/factories/enemy_factory.py
# DESIGN PATTERN: Factory Method

from abc import ABC, abstractmethod
from game.entities import Character
from patterns.creational.builder import CharacterBuilder
import random

# (Factory Method): definim Creatorul abstract.
# Acesta declară metoda factory `create_enemy()`, fără implementare concretă.
class EnemyFactory(ABC):
    """
    
    Factory Method pattern: subclasele decid ce tip de inamic să creeze.
    """

    @abstractmethod
    def create_enemy(self) -> Character:
        pass

# definim un Creator concret care decide ce produs concret creează.
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

# alt Creator concret, aceeași interfață, produs diferit.
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

# extinderea este simplă — adăugăm un nou Creator concret.
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

#  Clientul poate lucra doar cu tipul abstract `EnemyFactory`.
# `RandomEnemyFactory` orchestrează selecția fără a schimba codul clientului.
class RandomEnemyFactory(EnemyFactory):
    """
    Factory pentru crearea unui inamic aleatoriu.
    """

    def create_enemy(self) -> Character:
        factories = [GoblinFactory(), OrcFactory(), TrollFactory()]
        return random.choice(factories).create_enemy()