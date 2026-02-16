# patterns/creational/abstract_factory.py

from abc import ABC, abstractmethod
from game.entities import Character
from patterns.creational.builder import CharacterBuilder

class FactionFactory(ABC):
    """Abstract Factory pentru crearea familiilor de personaje dintr-o facțiune/temă."""

    @abstractmethod
    def create_hero(self) -> Character:
        pass

    @abstractmethod
    def create_enemy(self) -> Character:
        pass

    @abstractmethod
    def create_weapon(self) -> str:  # exemplu simplu de item/weapon
        pass
    

class MedievalFactionFactory(FactionFactory):
    """Facțiune medievală: eroi cavaleri, inamici goblin/orc."""

    def create_hero(self) -> Character:
        builder = CharacterBuilder()
        return (builder
                .name("Sir Arthur")
                .max_hp(120)
                .initial_hp(120)
                .description("Cavaler medieval curajos cu sabie lungă")
                .build())

    def create_enemy(self) -> Character:
        builder = CharacterBuilder()
        return (builder
                .name("Goblin Raider")
                .max_hp(60)
                .initial_hp(60)
                .description("Goblin sălbatic din pădure")
                .build())

    def create_weapon(self) -> str:
        return "Longsword +5"


class SciFiFactionFactory(FactionFactory):
    """Facțiune sci-fi: eroi roboți, inamici extratereștri."""

    def create_hero(self) -> Character:
        builder = CharacterBuilder()
        return (builder
                .name("Nova-7 Android")
                .max_hp(180)
                .initial_hp(180)
                .description("Robot de luptă cu plasmă și scut energetic")
                .build())

    def create_enemy(self) -> Character:
        builder = CharacterBuilder()
        return (builder
                .name("Xenomorph Scout")
                .max_hp(100)
                .initial_hp(100)
                .description("Extraterestru agresiv cu acid și gheare")
                .build())

    def create_weapon(self) -> str:
        return "Plasma Rifle Mk.3"
    