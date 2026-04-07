# DESIGN PATTERN: Flyweight
# In this program, Flyweight reuses shared enemy archetypes so multiple enemies can share the same intrinsic data.

from __future__ import annotations

from dataclasses import dataclass

from game.entities import Character


@dataclass(frozen=True)
class EnemyArchetype:
    """Intrinsic state shared by many enemies of the same type."""

    key: str
    name: str
    max_hp: int
    description: str


class EnemyFlyweight:
    """Flyweight that stores shared enemy data and spawns concrete characters."""

    def __init__(self, archetype: EnemyArchetype):
        self.archetype = archetype

    def spawn(self, name: str | None = None) -> Character:
        character = Character(name or self.archetype.name, self.archetype.max_hp)
        character.description = self.archetype.description
        return character


class EnemyFlyweightFactory:
    """Caches flyweights so multiple enemies reuse the same intrinsic state."""

    def __init__(self):
        self._flyweights: dict[str, EnemyFlyweight] = {}

    def get(self, key: str, name: str, max_hp: int, description: str) -> EnemyFlyweight:
        if key not in self._flyweights:
            self._flyweights[key] = EnemyFlyweight(
                EnemyArchetype(key=key, name=name, max_hp=max_hp, description=description)
            )
        return self._flyweights[key]

    def create_enemy(self, key: str, name: str | None = None) -> Character:
        archetypes = {
            "goblin": ("Goblin", 50, "Un goblin mic și viclean, creat din stare partajată"),
            "orc": ("Orc Warrior", 90, "Un orc puternic, reutilizat prin flyweight"),
            "troll": ("Troll", 150, "Un troll mare și regenerativ, partajat între instanțe"),
        }
        default_name, default_hp, default_description = archetypes.get(key, archetypes["goblin"])
        flyweight = self.get(key, default_name, default_hp, default_description)
        return flyweight.spawn(name)

    def cache_size(self) -> int:
        return len(self._flyweights)

    def cached_keys(self) -> list[str]:
        return list(self._flyweights.keys())
