# GoF Arena

GoF Arena este un simulator RPG în Python creat pentru a demonstra practic pattern-urile de proiectare GoF. Aplicația are două moduri de rulare: interfață grafică Tkinter și consolă, iar fiecare mecanism important este izolat într-un modul dedicat.

## Ce oferă proiectul

- luptă între un erou și inamici generați prin mai multe pattern-uri de creare;
- demo-uri dedicate pentru pattern-urile GoF implementate;
- observare a evenimentelor de luptă printr-un event bus;
- istoric de meciuri salvat în fișiere text;
- interfață grafică cu teme vizuale diferite și zonă de battle feed.

## Pattern-uri implementate

### Behavioral
- **Observer** - propagă evenimentele de luptă către UI și statistici.
- **Strategy** - schimbă stilul de atac al inamicilor la runtime.
- **Command** - încapsulează acțiuni precum damage și heal.
- **Memento** - salvează și restaurează starea eroului.

### Creational
- **Factory Method** - creează inamici prin fabrici specializate.
- **Abstract Factory** - generează familii coerente de obiecte tematice.
- **Builder** - construiește personajul pas cu pas.
- **Prototype** - clonează rapid prototipuri de inamici.

### Structural
- **Adapter** - integrează un inamic legacy în sistemul modern.
- **Flyweight** - reutilizează date comune pentru inamici similari.
- **Decorator** - adaugă buff-uri peste un personaj existent.
- **Bridge** - separă arma de modul de calcul al damage-ului.

## Structură proiect

```
TMPP-GoF_Arena-
├── main.py
├── game/
│   ├── entities.py
│   ├── events.py
│   ├── gui.py
│   └── factories/
├── patterns/
│   ├── behavioral/
│   ├── creational/
│   └── structural/
├── utils/
│   └── logger.py
├── match_history/
└── diagrame/
```

## Rulare

Din rădăcina proiectului:

```bash
python main.py
```

Moduri de rulare:

- `python main.py` - pornește interfața grafică;
- `python main.py --console` - pornește meniul din terminal.

## Meniu consolă

Aplicația are opțiuni pentru:

- creare erou și inamic;
- luptă manuală;
- kit-uri de facțiune prin Abstract Factory;
- clonare de inamici prin Prototype;
- demo-uri pentru Builder, Adapter, Flyweight, Decorator, Bridge, Proxy, Strategy, Observer, Command, Memento și Iterator.

## Exemple de utilizare

### GUI
- ecran principal cu tema selectabilă;
- zone separate pentru status, battle feed și istoric.

### Consolă
- creare rapidă de personaje;
- simulări manuale;
- afișare loguri complete.

## Concluzie

Proiectul arată cum pot fi aplicate pattern-urile GoF într-o aplicație coerentă, ușor de extins și ușor de prezentat. Arhitectura este modulară, iar funcționalitățile principale sunt suficiente pentru demonstrații practice și pentru susținerea proiectului de semestru.

## Link proiect

- GitHub: https://github.com/StanislavProdan/TMPP-GoF_Arena-.git
