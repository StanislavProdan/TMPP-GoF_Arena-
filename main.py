# main.py
# DESIGN PATTERNS USED:
# - Singleton: logger instance
# - Observer: event_bus for subscribing to game events
# - Factory Method: EnemyFactory for creating enemy instances

from utils.logger import logger
from game.entities import Character, event_bus
from game.factories.enemy_factory import EnemyFactory
from patterns.creational.abstract_factory import MedievalFactionFactory, SciFiFactionFactory

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

# Înregistrăm ascultătorii o singură dată la pornire
event_bus.subscribe("damage_taken", on_damage)
event_bus.subscribe("death", on_death)
event_bus.subscribe("healed", on_heal)


def afiseaza_status(personaj):
    """Afișează status-ul curent al unui personaj."""
    print(f"  {personaj.name}: HP {personaj.hp}/{personaj.max_hp}")


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
    print("  0. Ieșire")
    print("=" * 50)
    return input("\nAlege opțiunea (0-5): ").strip()


def main():
    print("=== GoF Arena - Design Patterns Showcase ===")
    print("Implementare: Singleton + Observer + Character")
    print("Scop: demonstrarea celor 23 pattern-uri GoF într-un simulator text-based\n")

    erou = None
    inamic = None

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
                inamic = EnemyFactory.create_goblin()
            elif alegere == 'o':
                inamic = EnemyFactory.create_orc()
            elif alegere == 't':
                inamic = EnemyFactory.create_troll()
            elif alegere == 'r':
                inamic = EnemyFactory.create_random_enemy()
            else:
                print("Opțiune invalidă → creez Goblin implicit")
                inamic = EnemyFactory.create_goblin()
            
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

        elif optiune == "0":
            print("\nMulțumim că ai testat GoF Arena!")
            print("Ieșire...")
            break

        else:
            print("\nOpțiune invalidă. Alege un număr între 0 și 5.")

if __name__ == "__main__":
    main()
