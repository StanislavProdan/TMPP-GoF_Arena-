# GoF Arena

Simulator RPG in Python pentru demonstrarea pattern-urilor GoF, acum cu interfata grafica (Tkinter) si mod consola.

## Pattern-uri implementate până acum
- **Singleton** - `utils/logger.py` - Ensure only one Logger instance exists globally
- **Observer** - `game/events.py` - EventBus pentru subscribe/publish la game events (damage, death, heal)
- **Builder** - `patterns/creational/builder.py` - CharacterBuilder pentru construire fluent a personajelor
- **Factory Method** - `game/factories/enemy_factory.py` - EnemyFactory pentru creare automată a tipurilor de inamici
- **Abstract Factory** - `patterns/creational/abstract_factory.py` - MedievalFactionFactory și SciFiFactionFactory pentru crearea de kit-uri complete (erou, inamic, armă)
- **Prototype** - `patterns/creational/prototype.py` - CharacterPrototype + PrototypeRegistry pentru clonarea rapidă a personajelor predefinite
- **Adapter** - `patterns/structural/adapter.py` - adaptează `LegacyEnemy` la interfața modernă `Character`
- **Composite** - `patterns/structural/composite.py` - tratează un personaj individual și un grup (`Squad`) prin aceeași interfață
- **Facade** - `patterns/structural/facade.py` - expune API simplificat pentru setup + rundă de duel

## Structură proiect
```
TMPP(GoF_Arena)/
├── main.py              # Punctul de intrare principal
├── game/
│   ├── __init__.py
│   ├── entities.py      # Character class
│   ├── events.py        # Observer pattern - EventBus
│   ├── gui.py           # Interfata grafica Tkinter
│   └── factories/
│       ├── __init__.py
│       └── enemy_factory.py  # Factory Method pattern
├── patterns/
│   ├── __init__.py
│   ├── creational/
│       ├── __init__.py
│       ├── builder.py          # Builder pattern - CharacterBuilder
│       ├── abstract_factory.py  # Abstract Factory pattern
│       └── prototype.py         # Prototype pattern
│   └── structural/
│       ├── __init__.py
│       ├── adapter.py           # Adapter pattern
│       ├── composite.py         # Composite pattern
│       └── facade.py            # Facade pattern
└── utils/
    ├── __init__.py
    └── logger.py        # Singleton pattern - Logger global
```

## Cum rulezi
```bash
# Din radacina proiectului
python main.py
```

### Moduri de rulare
- `python main.py` - porneste interfata grafica (GUI)
- `python main.py --console` - porneste meniul text din terminal

## Caracteristici recente (Feb 16, 2026)
- ✅ Implementat Abstract Factory pattern în `patterns/creational/abstract_factory.py`
- ✅ Adăugat opțiunea 5 în meniu pentru crearea kit-urilor de facțiune (Medieval/Sci-Fi)
- ✅ MedievalFactionFactory - creează erou (Sir Arthur), inamic (Goblin Raider), armă (Longsword +5)
- ✅ SciFiFactionFactory - creează erou (Nova-7 Android), inamic (Xenomorph Scout), armă (Plasma Rifle Mk.3)
- ✅ Fixate metodele CharacterBuilder în Abstract Factory (set_name → name, set_max_hp → max_hp, etc.)
- ✅ Update menu range: 0-4 → 0-5
- ✅ Implementat Prototype pattern în `patterns/creational/prototype.py`
- ✅ Adăugat opțiunea 6 în meniu pentru clonarea inamicilor din prototip (Goblin Elite, Orc Berserker, Ancient Troll)

## Gameplay
1. **Opțiunea 1**: Creează un erou cu HP personalizat
2. **Opțiunea 2**: Alege din tipuri predefiniţi de inamici (Goblin, Orc Warrior, Troll, Random)
3. **Opțiunea 3**: Luptă manuală cu damage custom
4. **Opțiunea 4**: Afişează log-urile complete (Singleton logger)
5. **Opțiunea 5**: Creează kit facțiune (Abstract Factory) - alege Medieval sau Sci-Fi pentru a genera erou, inamic și armă corespunzătoare temei
6. **Opțiunea 6**: Creează inamic din prototip (Prototype) - clonează un șablon predefinit și îi poți schimba numele
7. **Opțiunea 7**: Rulează demo-ul Builder (integritate + reset intern)
8. **Opțiunea 8**: Rulează demo-ul Adapter (legacy enemy integrat în sistem)
9. **Opțiunea 9**: Rulează demo-ul Composite (echipe ierarhice cu HP agregat)
10. **Opțiunea 10**: Rulează demo-ul Facade (setup duel și execute round prin API simplificat)

## Exemple output pentru pattern-uri structurale

### Adapter (opțiunea 8)
```text
=== Demo Adapter ===
Inamic legacy adaptat: Retro Drone
HP inițial: 80/80
După acțiuni prin interfața Character:
    Retro Drone: HP 65/80
```

### Composite (opțiunea 9)
```text
=== Demo Composite ===
Alpha Team: 205/205 -> [Knight (120/120), Archer (85/85)]
Beta Team: 150/150 -> [Orc Grunt (95/95), Goblin Sneak (55/55)]
Structură compusă:
Alliance Battalion: 355/355 -> [Alpha Team: 205/205 -> [Knight (120/120), Archer (85/85)], Beta Team: 150/150 -> [Orc Grunt (95/95), Goblin Sneak (55/55)]]
```

### Facade (opțiunea 10)
```text
=== Demo Facade ===
Duel inițializat: Facade Hero vs Goblin
Rezumat round (prin Facade):
    Facade Hero: 102/110
    Goblin: 38/50
```
