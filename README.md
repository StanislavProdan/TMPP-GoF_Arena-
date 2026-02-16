# GoF Arena

Simulator text-based de lupte RPG în Python pentru demonstrarea celor 22 pattern-uri de design Gang of Four (GoF).

## Pattern-uri implementate până acum
- **Singleton** - `utils/logger.py` - Ensure only one Logger instance exists globally
- **Observer** - `game/events.py` - EventBus pentru subscribe/publish la game events (damage, death, heal)
- **Builder** - `patterns/creational/builder.py` - CharacterBuilder pentru construire fluent a personajelor
- **Factory Method** - `game/factories/enemy_factory.py` - EnemyFactory pentru creare automată a tipurilor de inamici
- **Abstract Factory** - `patterns/creational/abstract_factory.py` - MedievalFactionFactory și SciFiFactionFactory pentru crearea de kit-uri complete (erou, inamic, armă)

## Structură proiect
```
TMPP(GoF_Arena)/
├── main.py              # Punctul de intrare principal
├── game/
│   ├── __init__.py
│   ├── entities.py      # Character class
│   ├── events.py        # Observer pattern - EventBus
│   └── factories/
│       ├── __init__.py
│       └── enemy_factory.py  # Factory Method pattern
├── patterns/
│   ├── __init__.py
│   └── creational/
│       ├── __init__.py
│       ├── builder.py          # Builder pattern - CharacterBuilder
│       └── abstract_factory.py  # Abstract Factory pattern
└── utils/
    ├── __init__.py
    └── logger.py        # Singleton pattern - Logger global
```

## Cum rulezi
```bash
# Din rădăcina proiectului
cd c:\Users\dprod\Desktop\TMPP(GoF_Arena)
python main.py
```

## Caracteristici recente (Feb 16, 2026)
- ✅ Implementat Abstract Factory pattern în `patterns/creational/abstract_factory.py`
- ✅ Adăugat opțiunea 5 în meniu pentru crearea kit-urilor de facțiune (Medieval/Sci-Fi)
- ✅ MedievalFactionFactory - creează erou (Sir Arthur), inamic (Goblin Raider), armă (Longsword +5)
- ✅ SciFiFactionFactory - creează erou (Nova-7 Android), inamic (Xenomorph Scout), armă (Plasma Rifle Mk.3)
- ✅ Fixate metodele CharacterBuilder în Abstract Factory (set_name → name, set_max_hp → max_hp, etc.)
- ✅ Update menu range: 0-4 → 0-5

## Gameplay
1. **Opțiunea 1**: Creează un erou cu HP personalizat
2. **Opțiunea 2**: Alege din tipuri predefiniţi de inamici (Goblin, Orc Warrior, Troll, Random)
3. **Opțiunea 3**: Luptă manuală cu damage custom
4. **Opțiunea 4**: Afişează log-urile complete (Singleton logger)
5. **Opțiunea 5**: Creează kit facțiune (Abstract Factory) - alege Medieval sau Sci-Fi pentru a genera erou, inamic și armă corespunzătoare temei
