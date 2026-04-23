# GoF Arena

Simulator RPG in Python pentru demonstrarea pattern-urilor GoF, acum cu interfata grafica (Tkinter) si mod consola.

## Pattern-uri implementate (active în Fight Interface)

### Behavioral (4)
- **Observer** - `patterns/behavioral/observer.py` + `game/events.py`
    - Notifică UI-ul și statistica de luptă la damage/heal/death și la evenimente de wave.
- **Strategy** - `patterns/behavioral/strategy.py`
    - Schimbă comportamentul AI-ului inamic în funcție de archetype (`slime`, `archer`, `brute`).
- **Command** - `patterns/behavioral/command.py`
    - Execută acțiunile de damage/heal prin comenzi (`DamageCommand`, `HealCommand`) în timpul luptei.
- **Memento** - `patterns/behavioral/memento.py`
    - Salvează checkpoint-uri pentru erou și permite restaurarea în fight (`Rewind Hero`).

### Creational (4)
- **Factory Method** - `game/factories/enemy_factory.py`
    - Generează inamici pentru valuri speciale (ex. valuri de tip boss).
- **Abstract Factory** - `patterns/creational/abstract_factory.py`
    - Aplică tema wave-ului (Medieval/Sci-Fi) și produce familie coerentă de entități.
- **Builder** - `patterns/creational/builder.py`
    - Construiește inamicii de wave cu HP/scalare configurată dinamic.
- **Prototype** - `patterns/creational/prototype.py`
    - Clonează rapid baza de inamic pe archetype înainte de personalizare pe wave.

### Structural (4)
- **Bridge** - `patterns/structural/bridge.py`
    - Separă tipul armei de tipul damage-ului și permite combinații runtime în battle.
- **Decorator** - `patterns/structural/decorator.py`
    - Aplică buff-uri active pe erou (`ShieldDecorator`, `BlessingDecorator`) în timpul luptei.
- **Flyweight** - `patterns/structural/flyweight.py`
    - Refolosește arhetipuri de inamici pentru spawn eficient pe wave-uri.
- **Adapter** - `patterns/structural/adapter.py`
    - Integrează inamici legacy (`LegacyEnemy`) în flow-ul modern de fight prin adaptor.

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
│   ├── behavioral/
│       ├── __init__.py
│       ├── strategy.py          # Strategy pattern
│       ├── observer.py          # Observer pattern (subject/observers)
│       ├── command.py           # Command pattern
│       ├── memento.py           # Memento pattern
│       └── iterator.py          # Iterator pattern
│   └── structural/
│       ├── __init__.py
│       ├── adapter.py           # Adapter pattern
│       ├── composite.py         # Composite pattern
│       ├── facade.py            # Facade pattern
│       ├── flyweight.py         # Flyweight pattern
│       ├── decorator.py         # Decorator pattern
│       ├── bridge.py            # Bridge pattern
│       └── proxy.py             # Proxy pattern
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
11. **Opțiunea 11**: Rulează demo-ul Flyweight (arhetipuri de inamici partajate)
12. **Opțiunea 12**: Rulează demo-ul Decorator (shield + blessing pe personaj)
13. **Opțiunea 13**: Rulează demo-ul Bridge (arme și moduri de damage separate)
14. **Opțiunea 14**: Rulează demo-ul Proxy (acces lazy la match history)
15. **Opțiunea 15**: Aplică Shield pe erou (Decorator)
16. **Opțiunea 16**: Aplică Blessing pe erou (Decorator)
17. **Opțiunea 17**: Rulează demo-ul Strategy (schimbarea stilului de atac la runtime)
18. **Opțiunea 18**: Rulează demo-ul Observer (subject + observers reutilizabili)
19. **Opțiunea 19**: Rulează demo-ul Command (execute + undo)
20. **Opțiunea 20**: Rulează demo-ul Memento (save + restore stare)
21. **Opțiunea 21**: Rulează demo-ul Iterator (traversare forward/reverse)

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

### Flyweight (opțiunea 11)
Flyweight este folosit aici pentru a reutiliza datele comune ale inamicilor de același tip. În program, asta reduce duplicarea și arată cum mai multe instanțe pot împărți aceeași stare internă.
```text
=== Demo Flyweight ===
Cache flyweights: 2 (goblin, orc)
Goblin Scout A: 50/50 | archetype id=...
Goblin Scout B: 50/50 | archetype id=...
Orc Patrol: 90/90
```

### Decorator (opțiunea 12)
Decorator adaugă efecte peste un personaj existent fără să-i modifice clasa de bază. În program îl folosim pentru a aplica un scut care reduce damage-ul și o binecuvântare care mărește vindecarea.
```text
=== Demo Decorator ===
Status inițial:
    Decorated Hero: HP 100/100
Atac de 30 dmg prin ShieldDecorator:
    Decorated Hero: HP 78/100
Heal de 10 prin BlessingDecorator:
    Decorated Hero: HP 94/100
```

### Bridge (opțiunea 13)
Bridge separă arma de modul în care este calculat damage-ul. În program, poți combina liber o armă cu un tip de damage, ca să schimbi comportamentul fără să multiplici clasele.
```text
=== Demo Bridge ===
Lionheart Sword (18 base, physical mode)
Arc Pulse Blaster (16 base, energy mode)
Storm Spear (14 base, piercing mode)
Status după atacuri:
    Bridge Knight: HP 120/120
    Bridge Dummy: HP 84/140
```

### Proxy (opțiunea 14)
Proxy acționează ca un intermediar pentru istoricul de meciuri. În program, el încarcă lista de fișiere doar când ai nevoie și o poate reutiliza din cache la apelurile următoare.
```text
=== Demo Proxy ===
Proxy încărcat? False
Proxy încărcat după prima listare? True
- match_20260306_140800.txt
GoF Arena - Match Report
...
```
