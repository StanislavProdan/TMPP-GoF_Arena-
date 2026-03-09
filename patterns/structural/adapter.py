# DESIGN PATTERN: Adapter

from game.entities import Character, event_bus
from utils.logger import logger


class LegacyEnemy:
    """Old API enemy that does not match the Character interface."""

    def __init__(self, codename: str, vitality: int):
        self.codename = codename
        self.vitality = vitality
        self.max_vitality = vitality

    def receive_hit(self, force: int):
        if force <= 0:
            return
        self.vitality = max(0, self.vitality - force)

    def recover(self, amount: int):
        if amount <= 0:
            return
        self.vitality = min(self.max_vitality, self.vitality + amount)


class LegacyEnemyAdapter(Character):
    """Adapts LegacyEnemy to the Character interface used by the game."""

    def __init__(self, legacy_enemy: LegacyEnemy):
        super().__init__(legacy_enemy.codename, legacy_enemy.max_vitality)
        self._legacy_enemy = legacy_enemy
        self.hp = legacy_enemy.vitality

    def take_damage(self, amount: int):
        if amount <= 0:
            return

        self._legacy_enemy.receive_hit(amount)
        self.hp = self._legacy_enemy.vitality
        logger.log(f"{self.name} (adapted) primește {amount} dmg -> HP: {self.hp}/{self.max_hp}", "DAMAGE")

        event_bus.publish("damage_taken", {
            "character": self,
            "amount": amount,
            "remaining_hp": self.hp,
        })

        if self.hp <= 0:
            event_bus.publish("death", {"character": self})
            logger.log(f"{self.name} (adapted) a murit!", "CRITICAL")

    def heal(self, amount: int):
        if amount <= 0:
            return

        old_hp = self.hp
        self._legacy_enemy.recover(amount)
        self.hp = self._legacy_enemy.vitality
        logger.log(f"{self.name} (adapted) se vindecă cu {amount} -> HP: {self.hp}/{self.max_hp}", "HEAL")

        event_bus.publish("healed", {
            "character": self,
            "amount": amount,
            "old_hp": old_hp,
            "new_hp": self.hp,
        })
