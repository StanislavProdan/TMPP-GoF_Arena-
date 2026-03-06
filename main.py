# main.py
# DESIGN PATTERNS USED:
# - Singleton: logger instance
# - Observer: event_bus for subscribing to game events
# - Factory Method: EnemyFactory subclasses for creating enemy instances
# - Prototype: clonare rapidă pe baza unor prototipuri predefinite

import sys

from utils.logger import logger
from game.entities import Character, event_bus
from game.factories.enemy_factory import GoblinFactory, OrcFactory, TrollFactory, RandomEnemyFactory
from game.gui import run_gui
from patterns.creational.abstract_factory import MedievalFactionFactory, SciFiFactionFactory
from patterns.creational.prototype import CharacterPrototype, PrototypeRegistry
from patterns.creational.builder import CharacterBuilder

# Event listeners
def on_damage(data):
    c = data["character"]
    print(f"  → {c.name} a fost lovit cu {data['amount']} dmg! Rămân {data['remaining_hp']} HP.")

def on_death(data):
    c = data["character"]
    print(f"  → {c.name} A MURIT!")

def on_heal(data):
    c = data["character"]
    print(f"  → {c.name} s-a vindecat cu {data['amount']}! HP acum: {data['new_hp']}")

def afiseaza_status(personaj):
    """Afișează status-ul curent al unui personaj."""
    print(f"  {personaj.name}: HP {personaj.hp}/{personaj.max_hp}")


def demo_builder_integrity():
    """Demonstrează că Builder setează description și își resetează starea."""
    print("\n=== Demo Builder (corectitudine) ===")
    builder = CharacterBuilder()

    cavaler = (builder
               .name("Demo Knight")
               .max_hp(140)
               .initial_hp(120)
               .description("Erou construit fluent")
               .build())

    # Dacă reset-ul funcționează, al doilea build pornește din valorile implicite.
    implicit_char = builder.build()

    print("Primul personaj (configurat):")
    print(f"  Nume: {cavaler.name}")
    print(f"  HP: {cavaler.hp}/{cavaler.max_hp}")
    print(f"  Description: {cavaler.description or '(gol)'}")

    print("Al doilea personaj (după reset builder):")
    print(f"  Nume: {implicit_char.name}")
    print(f"  HP: {implicit_char.hp}/{implicit_char.max_hp}")
    print(f"  Description: {implicit_char.description or '(gol)'}")


def meniu():
    """Afișează meniul principal și returnează opțiunea aleasă."""
    print("\n" + "=" * 50)
    print("              GoF Arena - Meniu Principal")
    print("=" * 50)
    print("  1. Creează un erou nou")
    print("  2. Creează un inamic nou")
    print("  3. Testează luptă simplă (manual)")
    print("  4. Arată toate log-urile")
    print("  5. Creează kit facțiune (Abstract Factory)")
    print("  6. Creează inamic din prototip (Prototype)")
    print("  7. Demo Builder (description + reset)")
    print("  0. Ieșire")
    print("=" * 50)
    return input("\nAlege opțiunea (0-7): ").strip()


def run_console():
    # In console mode, print game events to stdout.
    event_bus.subscribe("damage_taken", on_damage)
    event_bus.subscribe("death", on_death)
    event_bus.subscribe("healed", on_heal)

    print("=== GoF Arena - Design Patterns Showcase ===")
    print("Scop: demonstrarea celor 22 pattern-uri GoF într-un simulator text-based\n")

    erou = None
    inamic = None

    # Registry de prototipuri pregătite o singură dată.
    prototype_registry = PrototypeRegistry()
    prototype_registry.register(
        "goblin_elite",
        CharacterPrototype(Character("Goblin Elite", 75))
    )
    prototype_registry.register(
        "orc_berserker",
        CharacterPrototype(Character("Orc Berserker", 130))
    )
    prototype_registry.register(
        "troll_ancient",
        CharacterPrototype(Character("Ancient Troll", 220))
    )

    while True:
        optiune = meniu()

        if optiune == "1":
            nume = input("Nume erou (Enter = 'Hero'): ").strip() or "Hero"
            try:
                hp_max = int(input("HP maxim (Enter = 100): ") or 100)
            except ValueError:
                hp_max = 100
                print("Valoare invalidă → folosim 100.")
            erou = Character(nume, hp_max)
            print(f"\nErou creat: {erou.name}")
            afiseaza_status(erou)

        elif optiune == "2":
            print("\nTipuri de inamici disponibili:")
            print("  g - Goblin")
            print("  o - Orc Warrior")
            print("  t - Troll")
            print("  r - Random")
            
            alegere = input("Alege tip (g/o/t/r): ").strip().lower()
            
            if alegere == 'g':
                inamic = GoblinFactory().create_enemy()
            elif alegere == 'o':
                inamic = OrcFactory().create_enemy()
            elif alegere == 't':
                inamic = TrollFactory().create_enemy()
            elif alegere == 'r':
                inamic = RandomEnemyFactory().create_enemy()
            else:
                print("Opțiune invalidă → creez Goblin implicit")
                inamic = GoblinFactory().create_enemy()
            
            print(f"\nInamic creat cu succes: {inamic.name}")
            afiseaza_status(inamic)

        elif optiune == "3":
            if not erou or not inamic:
                print("\nTrebuie să creezi întâi un erou și un inamic!")
            else:
                print(f"\n=== Luptă: {erou.name} vs {inamic.name} ===")
                afiseaza_status(erou)
                afiseaza_status(inamic)

                # Atac erou → inamic
                try:
                    dmg = int(input("\nCât damage dă eroul? (0 = sări): ") or 0)
                except ValueError:
                    dmg = 0
                if dmg > 0:
                    inamic.take_damage(dmg)

                # Atac inamic → erou (doar dacă inamicul mai trăiește)
                if inamic.hp > 0:
                    try:
                        dmg = int(input("Cât damage dă inamicul? (0 = sări): ") or 0)
                    except ValueError:
                        dmg = 0
                    if dmg > 0:
                        erou.take_damage(dmg)

                print("\nStatus după tur:")
                afiseaza_status(erou)
                afiseaza_status(inamic)

        elif optiune == "4":
            print("\nLog-uri acumulate:")
            print("-" * 50)
            print(logger.get_all_logs())
            print("-" * 50)

        elif optiune == "5":
            print("\nFacțiuni disponibile:")
            print("  m - Medieval")
            print("  s - Sci-Fi")
            
            alegere = input("Alege facțiune (m/s): ").strip().lower()
            
            if alegere == 'm':
                factory = MedievalFactionFactory()
            elif alegere == 's':
                factory = SciFiFactionFactory()
            else:
                print("Invalid → folosim Medieval implicit")
                factory = MedievalFactionFactory()
            
            hero = factory.create_hero()
            enemy = factory.create_enemy()
            weapon = factory.create_weapon()
            
            print("\nKit facțiune creat:")
            print(f"Erou: {hero.name} ({hero.description})")
            afiseaza_status(hero)
            print(f"Inamic: {enemy.name} ({enemy.description})")
            afiseaza_status(enemy)
            print(f"Armă tipică: {weapon}")

        elif optiune == "6":
            print("\nPrototipuri disponibile:")
            print("  ge - Goblin Elite")
            print("  ob - Orc Berserker")
            print("  ta - Ancient Troll")

            alegere = input("Alege prototip (ge/ob/ta): ").strip().lower()
            key_map = {
                "ge": "goblin_elite",
                "ob": "orc_berserker",
                "ta": "troll_ancient",
            }
            key = key_map.get(alegere, "goblin_elite")

            try:
                inamic = prototype_registry.clone(key)
            except KeyError:
                print("Prototip invalid → folosim Goblin Elite implicit")
                inamic = prototype_registry.clone("goblin_elite")

            nou_nume = input("Nume pentru clonă (Enter = păstrează numele): ").strip()
            if nou_nume:
                inamic.name = nou_nume

            print(f"\nInamic clonat din prototip: {inamic.name}")
            afiseaza_status(inamic)

        elif optiune == "7":
            demo_builder_integrity()

        elif optiune == "0":
            print("\nMulțumim că ai testat GoF Arena!")
            print("Ieșire...")
            break

        else:
            print("\nOpțiune invalidă. Alege un număr între 0 și 7.")

if __name__ == "__main__":
    if "--console" in sys.argv:
        run_console()
    else:
        run_gui()
