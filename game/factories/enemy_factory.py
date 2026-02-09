# game/factories/enemy_factory.py
# DESIGN PATTERN: Factory Method 

from game.entities import Character
from patterns.creational.builder import CharacterBuilder
import random

class EnemyFactory:
    """
    Factory Method pentru crearea inamicilor predefiniți,
    folosind CharacterBuilder pentru consistență.
    """

    @staticmethod
    def create_goblin():
        builder = CharacterBuilder()
        return (builder
                .name("Goblin")
                .max_hp(50)
                .initial_hp(50)
                .description("Un goblin mic și viclean, dar slab")
                .build())

    @staticmethod
    def create_orc():
        builder = CharacterBuilder()
        return (builder
                .name("Orc Warrior")
                .max_hp(90)
                .initial_hp(90)
                .description("Un orc puternic și agresiv")
                .build())

    @staticmethod
    def create_troll():
        builder = CharacterBuilder()
        return (builder
                .name("Troll")
                .max_hp(150)
                .initial_hp(150)
                .description("Un troll mare și regenerativ")
                .build())

    @staticmethod
    def create_random_enemy():
        creators = [
            EnemyFactory.create_goblin,
            EnemyFactory.create_orc,
            EnemyFactory.create_troll
        ]
        return random.choice(creators)()