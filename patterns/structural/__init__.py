# patterns.structural package

from .adapter import LegacyEnemy, LegacyEnemyAdapter
from .bridge import Blaster, DamageMode, EnergyDamage, PhysicalDamage, PiercingDamage, Spear, Sword, Weapon
from .decorator import BlessingDecorator, CharacterComponent, CharacterDecorator, ShieldDecorator
from .composite import CharacterLeaf, Squad
from .facade import ArenaFacade
from .flyweight import EnemyArchetype, EnemyFlyweight, EnemyFlyweightFactory
from .proxy import MatchHistoryProxy, MatchHistoryReader

__all__ = [
    "LegacyEnemy",
    "LegacyEnemyAdapter",
    "Blaster",
    "DamageMode",
    "EnergyDamage",
    "PhysicalDamage",
    "PiercingDamage",
    "Spear",
    "Sword",
    "Weapon",
    "BlessingDecorator",
    "CharacterComponent",
    "CharacterDecorator",
    "ShieldDecorator",
    "CharacterLeaf",
    "Squad",
    "ArenaFacade",
    "EnemyArchetype",
    "EnemyFlyweight",
    "EnemyFlyweightFactory",
    "MatchHistoryProxy",
    "MatchHistoryReader",
]
