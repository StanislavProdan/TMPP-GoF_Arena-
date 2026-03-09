# DESIGN PATTERN: Facade

from __future__ import annotations

from game.entities import Character
from game.factories.enemy_factory import GoblinFactory, OrcFactory, RandomEnemyFactory, TrollFactory
from patterns.creational.builder import CharacterBuilder
from utils.logger import logger


class ArenaFacade:
    """Simple API that hides setup and one-round duel flow."""

    def __init__(self):
        self.hero: Character | None = None
        self.enemy: Character | None = None

    def setup_duel(self, hero_name: str, hero_hp: int, enemy_type: str = "random"):
        self.hero = CharacterBuilder().name(hero_name).max_hp(hero_hp).initial_hp(hero_hp).build()

        enemy_type = enemy_type.lower()
        factories = {
            "goblin": GoblinFactory,
            "orc": OrcFactory,
            "troll": TrollFactory,
            "random": RandomEnemyFactory,
        }
        factory_cls = factories.get(enemy_type, RandomEnemyFactory)
        self.enemy = factory_cls().create_enemy()

        logger.log(
            f"Facade setup: {self.hero.name} vs {self.enemy.name} ({self.enemy.hp}/{self.enemy.max_hp})",
            "INFO",
        )
        return self.hero, self.enemy

    def execute_round(self, hero_damage: int, enemy_damage: int) -> dict:
        if not self.hero or not self.enemy:
            raise RuntimeError("Duel not initialized. Call setup_duel first.")

        if hero_damage > 0 and self.enemy.hp > 0:
            self.enemy.take_damage(hero_damage)

        if enemy_damage > 0 and self.enemy.hp > 0 and self.hero.hp > 0:
            self.hero.take_damage(enemy_damage)

        summary = {
            "hero": f"{self.hero.name}: {self.hero.hp}/{self.hero.max_hp}",
            "enemy": f"{self.enemy.name}: {self.enemy.hp}/{self.enemy.max_hp}",
            "hero_alive": self.hero.hp > 0,
            "enemy_alive": self.enemy.hp > 0,
        }
        logger.log(f"Facade round summary: {summary}", "INFO")
        return summary
