# patterns.structural package

from .adapter import LegacyEnemy, LegacyEnemyAdapter
from .composite import CharacterLeaf, Squad
from .facade import ArenaFacade

__all__ = [
    "LegacyEnemy",
    "LegacyEnemyAdapter",
    "CharacterLeaf",
    "Squad",
    "ArenaFacade",
]
