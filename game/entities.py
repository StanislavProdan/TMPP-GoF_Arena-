# game/entities.py

from utils.logger import logger
from game.events import EventBus

event_bus = EventBus()  # instanță globală de EventBus

class Character:
    def __init__(self, name: str, max_hp: int = 100):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.description = ""

    def take_damage(self, amount: int):
        if amount <= 0:
            return
        
        self.hp = max(0, self.hp - amount)
        
        logger.log(f"{self.name} primește {amount} dmg → HP: {self.hp}/{self.max_hp}", "DAMAGE")
        
        event_bus.publish("damage_taken", {
            "character": self,
            "amount": amount,
            "remaining_hp": self.hp
        })
        
        if self.hp <= 0:
            event_bus.publish("death", {"character": self})
            logger.log(f"{self.name} a murit!", "CRITICAL")

    def heal(self, amount: int):
        if amount <= 0:
            return
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        logger.log(f"{self.name} se vindecă cu {amount} → HP: {self.hp}/{self.max_hp}", "HEAL")
        event_bus.publish("healed", {
            "character": self,
            "amount": amount,
            "old_hp": old_hp,
            "new_hp": self.hp
        })