# main.py
# DESIGN PATTERNS USED:
# - Singleton: logger instance
# - Observer: event_bus for subscribing to game events
# - Factory Method: EnemyFactory subclasses for creating enemy instances
# - Prototype: clonare rapidă pe baza unor prototipuri predefinite
# - Adapter / Composite / Facade / Flyweight / Decorator / Bridge / Proxy: pattern-uri structurale pentru integrare și orchestration

import sys
from pathlib import Path

from utils.logger import logger
from game.entities import Character, event_bus
from game.factories.enemy_factory import GoblinFactory, OrcFactory, TrollFactory, RandomEnemyFactory
from game.gui import run_gui
from patterns.creational.abstract_factory import MedievalFactionFactory, SciFiFactionFactory
from patterns.creational.prototype import CharacterPrototype, PrototypeRegistry
from patterns.creational.builder import CharacterBuilder
from patterns.structural import (
    ArenaFacade,
    Blaster,
    BlessingDecorator,
    CharacterLeaf,
    EnergyDamage,
    EnemyFlyweightFactory,
    LegacyEnemy,
    LegacyEnemyAdapter,
    MatchHistoryProxy,
    PhysicalDamage,
    PiercingDamage,
    ShieldDecorator,
    Squad,
    Spear,
    Sword,
)

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


def construieste_arma(nume_arma: str, base_damage: int, damage_mode: str):
    mode = damage_mode.strip().lower()
    if mode == "energy":
        implementor = EnergyDamage()
    elif mode == "piercing":
        implementor = PiercingDamage()
    else:
        implementor = PhysicalDamage()

    weapon_name = nume_arma.strip().lower()
    weapon_map = {
        "sword": Sword,
        "blaster": Blaster,
        "spear": Spear,
    }
    weapon_cls = weapon_map.get(weapon_name, Sword)
    return weapon_cls(f"{weapon_cls.__name__} of the Arena", base_damage, implementor)


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


def demo_adapter_pattern():
    """Demonstrează adaptarea unui inamic legacy la API-ul Character."""
    print("\n=== Demo Adapter ===")
    legacy_enemy = LegacyEnemy("Retro Drone", 80)
    adapted_enemy = LegacyEnemyAdapter(legacy_enemy)

    print(f"Inamic legacy adaptat: {adapted_enemy.name}")
    print(f"HP inițial: {adapted_enemy.hp}/{adapted_enemy.max_hp}")

    adapted_enemy.take_damage(22)
    adapted_enemy.heal(7)

    print("După acțiuni prin interfața Character:")
    afiseaza_status(adapted_enemy)


def demo_composite_pattern():
    """Demonstrează calcul agregat pe grupuri de personaje."""
    print("\n=== Demo Composite ===")

    alpha = Squad("Alpha Team")
    alpha.add(CharacterLeaf(Character("Knight", 120)))
    alpha.add(CharacterLeaf(Character("Archer", 85)))

    beta = Squad("Beta Team")
    beta.add(CharacterLeaf(Character("Orc Grunt", 95)))
    beta.add(CharacterLeaf(Character("Goblin Sneak", 55)))

    battalion = Squad("Alliance Battalion")
    battalion.add(alpha)
    battalion.add(beta)

    print(alpha.describe())
    print(beta.describe())
    print("Structură compusă:")
    print(battalion.describe())


def demo_facade_pattern():
    """Demonstrează API simplificat pentru setup + round de luptă."""
    print("\n=== Demo Facade ===")
    facade = ArenaFacade()

    hero_name = input("Nume erou (Enter = 'Facade Hero'): ").strip() or "Facade Hero"
    try:
        hero_hp = int(input("HP erou (Enter = 110): ") or 110)
    except ValueError:
        hero_hp = 110

    enemy_type = input("Tip inamic (goblin/orc/troll/random): ").strip().lower() or "random"
    hero, enemy = facade.setup_duel(hero_name=hero_name, hero_hp=hero_hp, enemy_type=enemy_type)

    print(f"Duel inițializat: {hero.name} vs {enemy.name}")
    try:
        hero_dmg = int(input("Damage erou (Enter = 12): ") or 12)
    except ValueError:
        hero_dmg = 12
    try:
        enemy_dmg = int(input("Damage inamic (Enter = 8): ") or 8)
    except ValueError:
        enemy_dmg = 8

    summary = facade.execute_round(hero_dmg, enemy_dmg)
    print("Rezumat round (prin Facade):")
    print(f"  {summary['hero']}")
    print(f"  {summary['enemy']}")


def demo_flyweight_pattern():
    """Demonstrează reutilizarea stării partajate pentru mulți inamici."""
    print("\n=== Demo Flyweight ===")
    factory = EnemyFlyweightFactory()

    goblin_one = factory.create_enemy("goblin", "Goblin Scout A")
    goblin_two = factory.create_enemy("goblin", "Goblin Scout B")
    orc_one = factory.create_enemy("orc", "Orc Patrol")

    print(f"Cache flyweights: {factory.cache_size()} ({', '.join(factory.cached_keys())})")
    print(f"{goblin_one.name}: {goblin_one.hp}/{goblin_one.max_hp} | archetype id={id(factory.get('goblin', 'Goblin', 50, 'shared'))}")
    print(f"{goblin_two.name}: {goblin_two.hp}/{goblin_two.max_hp} | archetype id={id(factory.get('goblin', 'Goblin', 50, 'shared'))}")
    print(f"{orc_one.name}: {orc_one.hp}/{orc_one.max_hp}")


def demo_decorator_pattern():
    """Demonstrează decorarea unui personaj cu efecte suprapuse."""
    print("\n=== Demo Decorator ===")
    hero = Character("Decorated Hero", 100)
    shielded = ShieldDecorator(hero, shield_value=8)
    blessed = BlessingDecorator(shielded, healing_bonus=6)

    print("Status inițial:")
    afiseaza_status(blessed)

    print("Atac de 30 dmg prin ShieldDecorator:")
    blessed.take_damage(30)
    afiseaza_status(blessed)

    print("Heal de 10 prin BlessingDecorator:")
    blessed.heal(10)
    afiseaza_status(blessed)


def demo_bridge_pattern():
    """Demonstrează separarea dintre tipul armei și modul de damage."""
    print("\n=== Demo Bridge ===")
    hero = Character("Bridge Knight", 120)
    enemy = Character("Bridge Dummy", 140)

    sword = Sword("Lionheart Sword", 18, PhysicalDamage())
    blaster = Blaster("Arc Pulse Blaster", 16, EnergyDamage())
    spear = Spear("Storm Spear", 14, PiercingDamage())

    print(sword.describe())
    sword.strike(hero, enemy)
    print(blaster.describe())
    blaster.strike(hero, enemy)
    print(spear.describe())
    spear.strike(hero, enemy)

    print("Status după atacuri:")
    afiseaza_status(hero)
    afiseaza_status(enemy)


def demo_proxy_pattern():
    """Demonstrează acces lazy și cache peste istoricul de meciuri."""
    print("\n=== Demo Proxy ===")
    proxy = MatchHistoryProxy(Path("match_history"))

    print(f"Proxy încărcat? {proxy.cache_loaded}")
    matches = proxy.latest_matches(3)
    print(f"Proxy încărcat după prima listare? {proxy.cache_loaded}")

    if not matches:
        print("Nu există fișiere de istoric disponibile.")
        return

    for match in matches:
        print(f"- {match.name}")
        preview = proxy.preview(match)
        print(preview)
        print("---")


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
    print("  8. Demo Adapter (legacy enemy)")
    print("  9. Demo Composite (squad)")
    print(" 10. Demo Facade (duel orchestration)")
    print(" 11. Demo Flyweight (shared enemy archetypes)")
    print(" 12. Demo Decorator (shield + blessing)")
    print(" 13. Demo Bridge (weapon/damage modes)")
    print(" 14. Demo Proxy (match history access)")
    print(" 15. Aplică Shield pe erou")
    print(" 16. Aplică Blessing pe erou")
    print("  0. Ieșire")
    print("=" * 50)
    return input("\nAlege opțiunea (0-16): ").strip()


def run_console():
    # In console mode, print game events to stdout.
    event_bus.subscribe("damage_taken", on_damage)
    event_bus.subscribe("death", on_death)
    event_bus.subscribe("healed", on_heal)

    print("=== GoF Arena - Design Patterns Showcase ===")
    print("Scop: demonstrarea pattern-urilor GoF într-un simulator text-based\n")

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
                    arma = input("Arma eroului (Sword/Blaster/Spear, Enter = Sword): ").strip() or "Sword"
                    mod_damage = input("Mod damage (Physical/Energy/Piercing, Enter = Physical): ").strip() or "Physical"
                    weapon = construieste_arma(arma, dmg, mod_damage)
                    dealt = weapon.strike(erou, inamic)
                    print(f"  → Eroul atacă folosind {weapon.name} și produce {dealt} dmg.")

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

        elif optiune == "15":
            if not erou:
                print("\nTrebuie să creezi întâi un erou!")
            else:
                try:
                    shield_value = int(input("Valoare Shield (Enter = 5): ") or 5)
                except ValueError:
                    shield_value = 5
                erou = ShieldDecorator(erou, shield_value=shield_value)
                print(f"\nShield aplicat pe {erou.name} cu reducere {shield_value}.")
                afiseaza_status(erou)

        elif optiune == "16":
            if not erou:
                print("\nTrebuie să creezi întâi un erou!")
            else:
                try:
                    blessing_value = int(input("Bonus Blessing (Enter = 4): ") or 4)
                except ValueError:
                    blessing_value = 4
                erou = BlessingDecorator(erou, healing_bonus=blessing_value)
                print(f"\nBlessing aplicat pe {erou.name} cu bonus {blessing_value} la heal.")
                afiseaza_status(erou)

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

        elif optiune == "8":
            demo_adapter_pattern()

        elif optiune == "9":
            demo_composite_pattern()

        elif optiune == "10":
            demo_facade_pattern()

        elif optiune == "11":
            demo_flyweight_pattern()

        elif optiune == "12":
            demo_decorator_pattern()

        elif optiune == "13":
            demo_bridge_pattern()

        elif optiune == "14":
            demo_proxy_pattern()

        elif optiune == "0":
            print("\nMulțumim că ai testat GoF Arena!")
            print("Ieșire...")
            break

        else:
            print("\nOpțiune invalidă. Alege un număr între 0 și 16.")

if __name__ == "__main__":
    if "--console" in sys.argv:
        run_console()
    else:
        run_gui()
