# GoF Arena

Simulator text-based de lupte RPG în Python pentru demonstrarea celor 22 pattern-uri de design Gang of Four (GoF).

## Pattern-uri implementate până acum
- **Singleton** - `utils/logger.py` - Ensure only one Logger instance exists globally
- **Observer** - `game/events.py` - EventBus pentru subscribe/publish la game events (damage, death, heal)
- **Builder** - `patterns/creational/builder.py` - CharacterBuilder pentru construire fluent a personajelor
- **Factory Method** - `game/factories/enemy_factory.py` - EnemyFactory pentru creare automată a tipurilor de inamici

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
│       └── builder.py   # Builder pattern - CharacterBuilder
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

## Caracteristici recente (Feb 9, 2026)
- ✅ Adăugat pattern comments la inceput fişier
- ✅ Creat `__init__.py` pentru toate pachetele
- ✅ Implementat EnemyFactory pentru crearea de inamici predefiniţi (Goblin, Orc, Troll)
- ✅ Main.py actualizat să folosească Factory Method pentru opțiunea 2
- ✅ Adăugat atribut `description` la Character class

## Gameplay
1. **Opțiunea 1**: Creează un erou cu HP personalizat
2. **Opțiunea 2**: Alege din tipuri predefiniţi de inamici (Goblin, Orc Warrior, Troll, Random)
3. **Opțiunea 3**: Luptă manuală cu damage custom
4. **Opțiunea 4**: Afişează log-urile complete (Singleton logger)
