"""Tkinter interface for GoF Arena.
"""

import random
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Optional

from utils.logger import logger
from game.entities import Character, event_bus
from game.factories.enemy_factory import (
    GoblinFactory,
    OrcFactory,
    RandomEnemyFactory,
    TrollFactory,
)
from patterns.behavioral import (
    AggressiveStrategy,
    AttackContext,
    BalancedStrategy,
    BattleFeedObserver,
    BattleStatsObserver,
    ChaosStrategy,
    CommandInvoker,
    CombatLogCollection,
    DamageCommand,
    DefensiveStrategy,
    HealCommand,
    CharacterStateOriginator,
    MementoCaretaker,
    Subject,
)
from patterns.creational.abstract_factory import MedievalFactionFactory, SciFiFactionFactory
from patterns.creational.builder import CharacterBuilder
from patterns.creational.prototype import CharacterPrototype, PrototypeRegistry
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


class GoFArenaGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GoF Arena - GUI")
        self.root.geometry("1240x760")
        self.root.minsize(1040, 620)

        self.theme_palettes = {
            "Arena Neon": {
                "bg": "#0d111a",
                "panel": "#171f2f",
                "panel_alt": "#1d2740",
                "text": "#f2f1e8",
                "muted": "#a7b2c8",
                "accent": "#5fd1c9",
                "accent_alt": "#f0b35a",
                "danger": "#e16969",
                "success": "#6fcf87",
                "feed_bg": "#0f1523",
                "select": "#2b3956",
            },
            "Sunset Brass": {
                "bg": "#1d1614",
                "panel": "#2e221d",
                "panel_alt": "#453028",
                "text": "#f8ecde",
                "muted": "#ccb49f",
                "accent": "#e5a15c",
                "accent_alt": "#f1ce74",
                "danger": "#d16b5e",
                "success": "#98c97a",
                "feed_bg": "#241a17",
                "select": "#614235",
            },
            "Frost Steel": {
                "bg": "#141a22",
                "panel": "#1f2a38",
                "panel_alt": "#2a3a4f",
                "text": "#eef3fa",
                "muted": "#a9b8cb",
                "accent": "#7fb9ff",
                "accent_alt": "#b9d2ff",
                "danger": "#d97676",
                "success": "#82d0b8",
                "feed_bg": "#18202c",
                "select": "#3a4d67",
            },
        }
        self.current_theme = tk.StringVar(value="Arena Neon")
        self.colors = dict(self.theme_palettes[self.current_theme.get()])

        self.hero: Optional[Character] = None
        self.enemy: Optional[Character] = None
        self._winner_shown_for: Optional[str] = None
        self.hero_damage_dealt = 0
        self.hero_damage_taken = 0
        self.hero_total_heal = 0
        self.hero_anchor = (140, 120)
        self.enemy_anchor = (420, 120)
        self._active_scroll_target = None
        self._hero_buff_state = {"shield": 0, "blessing": 0}
        self.battle_window: Optional[tk.Toplevel] = None
        self.battle_feed: Optional[tk.Text] = None
        self.battle_status_var: Optional[tk.StringVar] = None
        self.battle_round_var: Optional[tk.StringVar] = None
        self.battle_hero_hp_var: Optional[tk.StringVar] = None
        self.battle_enemy_hp_var: Optional[tk.StringVar] = None
        self.battle_stats_var: Optional[tk.StringVar] = None
        self.battle_attack_var = tk.IntVar(value=12)
        self.battle_heal_var = tk.IntVar(value=10)
        self.battle_enemy_attack_var = tk.IntVar(value=8)
        self.demo_buttons: list[ttk.Button] = []
        self.terraria_canvas: Optional[tk.Canvas] = None
        self.terraria_state: dict[str, object] = {}
        self.terraria_keys: set[str] = set()
        self.terraria_loop_after_id: Optional[str] = None
        self.battle_weapon_var: Optional[tk.StringVar] = None
        self.command_invoker = CommandInvoker()
        self.hero_state_caretaker = MementoCaretaker()
        self.enemy_attack_context = AttackContext(BalancedStrategy())
        self.battle_subject = Subject()
        self.battle_feed_observer = BattleFeedObserver()
        self.battle_stats_observer = BattleStatsObserver()
        self.battle_subject.attach(self.battle_feed_observer)
        self.battle_subject.attach(self.battle_stats_observer)

        self.prototype_registry = PrototypeRegistry()
        self.prototype_registry.register("goblin_elite", CharacterPrototype(Character("Goblin Elite", 75)))
        self.prototype_registry.register("orc_berserker", CharacterPrototype(Character("Orc Berserker", 130)))
        self.prototype_registry.register("troll_ancient", CharacterPrototype(Character("Ancient Troll", 220)))
        self.flyweight_factory = EnemyFlyweightFactory()
        self.history_proxy = MatchHistoryProxy("match_history")

        self._configure_style()
        self._build_layout()
        self._bind_scroll_handlers()
        self._subscribe_events()
        self._append_log("GUI ready. Create a hero and an enemy to start.")
        self._add_history("Arena initialized")
        self._update_stats()
        self._update_status()

    def _set_theme(self, theme_name: str):
        palette = self.theme_palettes.get(theme_name)
        if not palette:
            return

        self.colors = dict(palette)
        self._configure_style()

        if hasattr(self, "left_canvas"):
            self.left_canvas.configure(bg=self.colors["bg"])
        if hasattr(self, "right_canvas"):
            self.right_canvas.configure(bg=self.colors["bg"])
        if hasattr(self, "hero_hp_canvas"):
            self.hero_hp_canvas.configure(bg=self.colors["bg"])
        if hasattr(self, "enemy_hp_canvas"):
            self.enemy_hp_canvas.configure(bg=self.colors["bg"])
        if hasattr(self, "arena_canvas"):
            self.arena_canvas.configure(bg=self.colors["feed_bg"])
            self._draw_arena_background()
        if hasattr(self, "history_list"):
            self.history_list.configure(
                bg=self.colors["feed_bg"],
                fg=self.colors["text"],
                selectbackground=self.colors["select"],
            )
        if hasattr(self, "feed"):
            self.feed.configure(
                bg=self.colors["feed_bg"],
                fg=self.colors["text"],
                insertbackground=self.colors["text"],
            )

        self._update_status()

    def apply_theme(self):
        selected = self.current_theme.get()
        self._set_theme(selected)
        self._append_log(f"Theme applied: {selected}")
        self._add_history(f"Theme: {selected}")

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        self.root.configure(bg=self.colors["bg"])
        style.configure("Header.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Bahnschrift SemiBold", 26))
        style.configure("SubHeader.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Calibri", 11, "italic"))
        style.configure("Card.TLabelframe", background=self.colors["panel"], foreground=self.colors["text"], borderwidth=1)
        style.configure("Card.TLabelframe.Label", background=self.colors["panel"], foreground=self.colors["accent_alt"], font=("Bahnschrift SemiBold", 10))
        style.configure("Card.TFrame", background=self.colors["panel"])
        style.configure("ArenaName.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Bahnschrift SemiBold", 13))
        style.configure("ArenaMeta.TLabel", background=self.colors["panel"], foreground=self.colors["muted"], font=("Calibri", 10))
        style.configure("FieldLabel.TLabel", background=self.colors["panel"], foreground=self.colors["muted"], font=("Calibri", 10))

        style.configure(
            "TButton",
            background=self.colors["panel_alt"],
            foreground=self.colors["text"],
            borderwidth=0,
            padding=(8, 6),
            font=("Calibri", 10, "bold"),
        )
        style.map(
            "TButton",
            background=[("active", "#23314f"), ("pressed", "#314262")],
            foreground=[("disabled", "#6f7c96")],
        )

        style.configure("Emphasis.TButton", background=self.colors["accent"], foreground="#081018", font=("Bahnschrift SemiBold", 10), padding=(8, 7))
        style.map("Emphasis.TButton", background=[("active", "#7ce4dd"), ("pressed", "#49b5ad")])

        style.configure("Danger.TButton", background=self.colors["danger"], foreground="#fff7f7", font=("Bahnschrift SemiBold", 10), padding=(8, 7))
        style.map("Danger.TButton", background=[("active", "#f08585"), ("pressed", "#ca5858")])

        style.configure("TCombobox", fieldbackground=self.colors["feed_bg"], background=self.colors["panel_alt"], foreground=self.colors["text"])

    def _build_layout(self):
        title = ttk.Label(
            self.root,
            text="GoF Arena",
            style="Header.TLabel",
            anchor="center",
        )
        title.pack(fill="x", padx=12, pady=(14, 2))

        subtitle = ttk.Label(
            self.root,
            text="Tactical Pattern Playground",
            style="SubHeader.TLabel",
            anchor="center",
        )
        subtitle.pack(fill="x", padx=12, pady=(0, 10))

        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        left_shell = ttk.Frame(body, style="Card.TFrame")
        left_shell.pack(side="left", fill="y")

        self.left_canvas = tk.Canvas(
            left_shell,
            width=320,
            bg=self.colors["bg"],
            highlightthickness=0,
            relief="flat",
        )
        left_scroll = ttk.Scrollbar(left_shell, orient="vertical", command=self.left_canvas.yview)
        self.left_canvas.configure(yscrollcommand=left_scroll.set)
        self.left_canvas.pack(side="left", fill="both", expand=True)
        left_scroll.pack(side="left", fill="y")

        left = ttk.Frame(self.left_canvas, style="Card.TFrame")
        self._left_window = self.left_canvas.create_window((0, 0), window=left, anchor="nw")
        left.bind("<Configure>", self._on_left_frame_configure)
        self.left_canvas.bind("<Configure>", self._on_left_canvas_configure)
        self.left_canvas.bind("<Enter>", lambda _e: self._set_active_scroll_target(self.left_canvas))
        self.left_canvas.bind("<Leave>", self._clear_active_scroll_target)

        center = ttk.Frame(body, style="Card.TFrame")
        center.pack(side="left", fill="both", expand=True, padx=(14, 0))

        right_shell = ttk.Frame(body, style="Card.TFrame")
        right_shell.pack(side="left", fill="both", expand=True, padx=(14, 0))

        self.right_canvas = tk.Canvas(
            right_shell,
            bg=self.colors["bg"],
            highlightthickness=0,
            relief="flat",
        )
        right_scroll = ttk.Scrollbar(right_shell, orient="vertical", command=self.right_canvas.yview)
        self.right_canvas.configure(yscrollcommand=right_scroll.set)
        self.right_canvas.pack(side="left", fill="both", expand=True)
        right_scroll.pack(side="left", fill="y")

        right = ttk.Frame(self.right_canvas, style="Card.TFrame")
        self._right_window = self.right_canvas.create_window((0, 0), window=right, anchor="nw")
        right.bind("<Configure>", self._on_right_frame_configure)
        self.right_canvas.bind("<Configure>", self._on_right_canvas_configure)
        self.right_canvas.bind("<Enter>", lambda _e: self._set_active_scroll_target(self.right_canvas))
        self.right_canvas.bind("<Leave>", self._clear_active_scroll_target)

        status_box = ttk.LabelFrame(left, text="Current Characters", style="Card.TLabelframe")
        status_box.pack(fill="x", pady=(0, 10))

        self.hero_var = tk.StringVar(value="Hero: (none)")
        self.enemy_var = tk.StringVar(value="Enemy: (none)")
        ttk.Label(status_box, textvariable=self.hero_var, width=30, style="ArenaMeta.TLabel").pack(anchor="w", padx=8, pady=(8, 3))
        ttk.Label(status_box, textvariable=self.enemy_var, width=30, style="ArenaMeta.TLabel").pack(anchor="w", padx=8, pady=(0, 8))

        stats_box = ttk.LabelFrame(left, text="Live Stats", style="Card.TLabelframe")
        stats_box.pack(fill="x", pady=(0, 10))
        self.stats_dealt_var = tk.StringVar(value="Hero dealt: 0")
        self.stats_taken_var = tk.StringVar(value="Hero taken: 0")
        self.stats_heal_var = tk.StringVar(value="Hero heals: 0")
        ttk.Label(stats_box, textvariable=self.stats_dealt_var, style="ArenaMeta.TLabel").pack(anchor="w", padx=8, pady=(8, 2))
        ttk.Label(stats_box, textvariable=self.stats_taken_var, style="ArenaMeta.TLabel").pack(anchor="w", padx=8, pady=2)
        ttk.Label(stats_box, textvariable=self.stats_heal_var, style="ArenaMeta.TLabel").pack(anchor="w", padx=8, pady=(2, 8))

        controls = ttk.LabelFrame(left, text="Actions", style="Card.TLabelframe")
        controls.pack(fill="x")

        ttk.Button(controls, text="1) Create Hero", command=self.create_hero).pack(fill="x", padx=8, pady=(8, 4))

        self.enemy_type = tk.StringVar(value="Random")
        ttk.Label(controls, text="Enemy type:", style="FieldLabel.TLabel").pack(anchor="w", padx=8, pady=(4, 0))
        ttk.Combobox(
            controls,
            textvariable=self.enemy_type,
            values=["Goblin", "Orc", "Troll", "Random"],
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))
        ttk.Button(controls, text="2) Create Enemy", command=self.create_enemy).pack(fill="x", padx=8, pady=(0, 6))

        ttk.Button(controls, text="3) Fight Round", command=self.fight_round, style="Emphasis.TButton").pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="Quick Duel (random)", command=self.quick_duel).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="4) Show Logs", command=self.show_logs).pack(fill="x", padx=8, pady=4)

        ttk.Separator(controls, orient="horizontal").pack(fill="x", padx=8, pady=8)
        ttk.Label(controls, text="Theme:", style="FieldLabel.TLabel").pack(anchor="w", padx=8, pady=(0, 0))
        ttk.Combobox(
            controls,
            textvariable=self.current_theme,
            values=list(self.theme_palettes.keys()),
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))
        ttk.Button(controls, text="Apply Theme", command=self.apply_theme, style="Emphasis.TButton").pack(fill="x", padx=8, pady=(0, 4))

        ttk.Separator(controls, orient="horizontal").pack(fill="x", padx=8, pady=8)
        ttk.Label(controls, text="Hero Weapon:", style="FieldLabel.TLabel").pack(anchor="w", padx=8, pady=(0, 0))
        self.hero_weapon_kind = tk.StringVar(value="Sword")
        ttk.Combobox(
            controls,
            textvariable=self.hero_weapon_kind,
            values=["Sword", "Blaster", "Spear"],
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))

        ttk.Label(controls, text="Damage mode:", style="FieldLabel.TLabel").pack(anchor="w", padx=8, pady=(0, 0))
        self.hero_damage_mode = tk.StringVar(value="Physical")
        ttk.Combobox(
            controls,
            textvariable=self.hero_damage_mode,
            values=["Physical", "Energy", "Piercing"],
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))

        ttk.Button(controls, text="Apply Shield to Hero", command=self.apply_hero_shield).pack(fill="x", padx=8, pady=(0, 4))
        ttk.Button(controls, text="Apply Blessing to Hero", command=self.apply_hero_blessing).pack(fill="x", padx=8, pady=(0, 6))

        self.faction_var = tk.StringVar(value="Medieval")
        ttk.Label(controls, text="Faction:", style="FieldLabel.TLabel").pack(anchor="w", padx=8, pady=(4, 0))
        ttk.Combobox(
            controls,
            textvariable=self.faction_var,
            values=["Medieval", "Sci-Fi"],
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))
        ttk.Button(controls, text="5) Create Faction Kit", command=self.create_faction_kit).pack(fill="x", padx=8, pady=(0, 6))

        self.prototype_var = tk.StringVar(value="goblin_elite")
        ttk.Label(controls, text="Prototype:", style="FieldLabel.TLabel").pack(anchor="w", padx=8, pady=(4, 0))
        ttk.Combobox(
            controls,
            textvariable=self.prototype_var,
            values=["goblin_elite", "orc_berserker", "troll_ancient"],
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))
        ttk.Button(controls, text="6) Clone Prototype", command=self.clone_prototype_enemy).pack(fill="x", padx=8, pady=(0, 6))

        demo_actions = [
            ("7) Builder Demo", self.demo_builder_integrity),
            ("8) Adapter Demo", self.demo_adapter_pattern),
            ("9) Composite Demo", self.demo_composite_pattern),
            ("10) Facade Demo", self.demo_facade_pattern),
            ("11) Flyweight Demo", self.demo_flyweight_pattern),
            ("12) Decorator Demo", self.demo_decorator_pattern),
            ("13) Bridge Demo", self.demo_bridge_pattern),
            ("14) Proxy Demo", self.demo_proxy_pattern),
            ("15) Strategy Demo", self.demo_strategy_pattern),
            ("16) Observer Demo", self.demo_observer_pattern),
            ("17) Command Demo", self.demo_command_pattern),
            ("18) Memento Demo", self.demo_memento_pattern),
            ("19) Iterator Demo", self.demo_iterator_pattern),
        ]
        for label, callback in demo_actions:
            btn = ttk.Button(controls, text=label, command=callback)
            btn.pack(fill="x", padx=8, pady=4)
            self.demo_buttons.append(btn)
        ttk.Button(controls, text="Reset Match", command=self.reset_match, style="Danger.TButton").pack(fill="x", padx=8, pady=4)

        ttk.Separator(controls, orient="horizontal").pack(fill="x", padx=8, pady=8)
        ttk.Button(controls, text="Exit", command=self.root.destroy, style="Danger.TButton").pack(fill="x", padx=8, pady=(0, 8))

        arena_box = ttk.LabelFrame(center, text="Arena", style="Card.TLabelframe")
        arena_box.pack(fill="both", expand=True)

        hero_card = ttk.Frame(arena_box, style="Card.TFrame")
        hero_card.pack(fill="x", padx=10, pady=(10, 6))

        ttk.Label(hero_card, text="HERO", style="ArenaMeta.TLabel").pack(anchor="w")
        self.hero_name_var = tk.StringVar(value="(none)")
        ttk.Label(hero_card, textvariable=self.hero_name_var, style="ArenaName.TLabel").pack(anchor="w", pady=(0, 4))
        self.hero_hp_text_var = tk.StringVar(value="HP: 0/0")
        ttk.Label(hero_card, textvariable=self.hero_hp_text_var, style="ArenaMeta.TLabel").pack(anchor="w", pady=(0, 4))
        self.hero_hp_canvas = tk.Canvas(hero_card, width=320, height=20, bg="#111522", highlightthickness=0)
        self.hero_hp_canvas.pack(anchor="w", pady=(0, 6))

        ttk.Separator(arena_box, orient="horizontal").pack(fill="x", padx=10, pady=8)
        self.round_var = tk.StringVar(value="Round: 0")
        ttk.Label(arena_box, textvariable=self.round_var, style="ArenaName.TLabel").pack(pady=(0, 8))
        ttk.Label(arena_box, text="VS", style="ArenaName.TLabel").pack(pady=(0, 8))
        self.last_action_var = tk.StringVar(value="Last action: waiting...")
        ttk.Label(arena_box, textvariable=self.last_action_var, style="ArenaMeta.TLabel").pack(pady=(0, 10))

        battle_controls = ttk.Frame(arena_box, style="Card.TFrame")
        battle_controls.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(battle_controls, text="Hero Attack", command=self.hero_attack, style="Emphasis.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(battle_controls, text="Hero Heal", command=self.hero_heal).pack(side="left")

        self.arena_canvas = tk.Canvas(
            arena_box,
            width=560,
            height=190,
            bg=self.colors["feed_bg"],
            highlightthickness=0,
            relief="flat",
        )
        self.arena_canvas.pack(fill="x", padx=10, pady=(0, 8))
        self._draw_arena_background()

        ttk.Separator(arena_box, orient="horizontal").pack(fill="x", padx=10, pady=8)

        enemy_card = ttk.Frame(arena_box, style="Card.TFrame")
        enemy_card.pack(fill="x", padx=10, pady=(6, 10))

        ttk.Label(enemy_card, text="ENEMY", style="ArenaMeta.TLabel").pack(anchor="w")
        self.enemy_name_var = tk.StringVar(value="(none)")
        ttk.Label(enemy_card, textvariable=self.enemy_name_var, style="ArenaName.TLabel").pack(anchor="w", pady=(0, 4))
        self.enemy_hp_text_var = tk.StringVar(value="HP: 0/0")
        ttk.Label(enemy_card, textvariable=self.enemy_hp_text_var, style="ArenaMeta.TLabel").pack(anchor="w", pady=(0, 4))
        self.enemy_hp_canvas = tk.Canvas(enemy_card, width=320, height=20, bg="#111522", highlightthickness=0)
        self.enemy_hp_canvas.pack(anchor="w", pady=(0, 6))

        history_box = ttk.LabelFrame(right, text="Combat History", style="Card.TLabelframe")
        history_box.pack(fill="x", pady=(0, 10))

        history_shell = ttk.Frame(history_box, style="Card.TFrame")
        history_shell.pack(fill="x", padx=8, pady=8)

        self.history_list = tk.Listbox(
            history_shell,
            height=7,
            bg=self.colors["feed_bg"],
            fg=self.colors["text"],
            relief="flat",
            highlightthickness=0,
            selectbackground=self.colors["select"],
            activestyle="none",
            font=("Consolas", 10),
        )
        history_scroll = ttk.Scrollbar(history_shell, orient="vertical", command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=history_scroll.set)
        self.history_list.pack(side="left", fill="both", expand=True)
        history_scroll.pack(side="left", fill="y")

        log_box = ttk.LabelFrame(right, text="Combat Feed", style="Card.TLabelframe")
        log_box.pack(fill="x")

        feed_shell = ttk.Frame(log_box, style="Card.TFrame")
        feed_shell.pack(fill="both", expand=True)

        self.feed = tk.Text(
            feed_shell,
            wrap="word",
            height=24,
            padx=10,
            pady=10,
            bg=self.colors["feed_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            font=("Consolas", 10),
        )
        feed_scroll = ttk.Scrollbar(feed_shell, orient="vertical", command=self.feed.yview)
        self.feed.configure(yscrollcommand=feed_scroll.set)
        self.feed.pack(side="left", fill="both", expand=True)
        feed_scroll.pack(side="left", fill="y")
        self.feed.bind("<Enter>", lambda _e: self._set_active_scroll_target(self.feed))
        self.feed.bind("<Leave>", self._clear_active_scroll_target)
        self.history_list.bind("<Enter>", lambda _e: self._set_active_scroll_target(self.history_list))
        self.history_list.bind("<Leave>", self._clear_active_scroll_target)
        self.feed.configure(state="disabled")
        self.round_count = 0

    def _bind_scroll_handlers(self):
        self.root.bind_all("<MouseWheel>", self._dispatch_mousewheel)
        self.root.bind("<FocusIn>", self._on_root_focus)

    def _on_root_focus(self, _event):
        self._refresh_focus_mode()

    def _set_active_scroll_target(self, widget):
        self._active_scroll_target = widget

    def _clear_active_scroll_target(self, _event):
        self._active_scroll_target = None

    def _dispatch_mousewheel(self, event):
        target = self._active_scroll_target
        if not target:
            return
        target.yview_scroll(int(-event.delta / 120), "units")

    def _on_left_frame_configure(self, _event):
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def _on_left_canvas_configure(self, event):
        self.left_canvas.itemconfigure(self._left_window, width=event.width)

    def _on_right_frame_configure(self, _event):
        self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))

    def _on_right_canvas_configure(self, event):
        self.right_canvas.itemconfigure(self._right_window, width=event.width)

    def _draw_arena_background(self):
        self.arena_canvas.delete("bg")
        self.arena_canvas.create_rectangle(0, 0, 560, 58, fill="#141c3d", outline="", tags="bg")
        self.arena_canvas.create_rectangle(0, 58, 560, 98, fill="#2a2d56", outline="", tags="bg")
        self.arena_canvas.create_rectangle(0, 98, 560, 122, fill="#3b3a4f", outline="", tags="bg")

        # Grandstands crowd silhouette.
        for x in range(8, 560, 13):
            tone = "#5a6175" if (x // 13) % 2 == 0 else "#6e7587"
            self.arena_canvas.create_oval(x, 66, x + 8, 74, fill=tone, outline="", tags="bg")

        # Banners and arena wall for a stadium look.
        self.arena_canvas.create_rectangle(18, 8, 122, 34, fill="#7b2f2f", outline="#c8d1e6", width=1, tags="bg")
        self.arena_canvas.create_rectangle(438, 8, 542, 34, fill="#2d5e7d", outline="#c8d1e6", width=1, tags="bg")
        self.arena_canvas.create_text(70, 21, text="EAST STAND", fill="#f3e8d8", font=("Bahnschrift", 8), tags="bg")
        self.arena_canvas.create_text(490, 21, text="WEST STAND", fill="#f3e8d8", font=("Bahnschrift", 8), tags="bg")

        # Ground layers.
        self.arena_canvas.create_rectangle(0, 122, 560, 190, fill="#2f4a3a", outline="", tags="bg")
        self.arena_canvas.create_line(0, 122, 560, 122, fill="#c9b179", width=2, tags="bg")

        # Perspective dirt/grass texture lines.
        for x in range(0, 560, 16):
            self.arena_canvas.create_line(x, 122, x - 14, 190, fill="#3f654f", width=1, tags="bg")
        for x in range(6, 560, 44):
            self.arena_canvas.create_line(x, 122, x - 24, 190, fill="#6d7f52", width=1, tags="bg")

        # Torches near walls.
        for tx in (150, 408):
            self.arena_canvas.create_rectangle(tx, 92, tx + 4, 121, fill="#5d5d66", outline="", tags="bg")
            self.arena_canvas.create_oval(tx - 4, 84, tx + 8, 95, fill="#f7b86e", outline="", tags="bg")
            self.arena_canvas.create_oval(tx - 1, 86, tx + 5, 92, fill="#ffe8ad", outline="", tags="bg")

    def _character_palette(self, name: str, is_enemy: bool):
        if not is_enemy:
            return {"body": "#5ca0ff", "head": "#f4d7b5", "accent": "#8fd0ff"}

        lower = name.lower()
        if "goblin" in lower:
            return {"body": "#66b85f", "head": "#9ed17a", "accent": "#d7ef9d"}
        if "orc" in lower:
            return {"body": "#7f9850", "head": "#9cbf64", "accent": "#dbe7ab"}
        if "troll" in lower:
            return {"body": "#5d8b6f", "head": "#8ab592", "accent": "#cde8d1"}
        return {"body": "#c06a6a", "head": "#e2a4a4", "accent": "#f3d3d3"}

    def _draw_character_sprite(self, tag: str, x: int, y: int, name: str, is_enemy: bool):
        palette = self._character_palette(name, is_enemy)
        direction = -1 if is_enemy else 1

        self.arena_canvas.create_oval(x - 18, y + 36, x + 18, y + 48, fill="#1a2420", outline="", tags=("sprites", tag))
        self.arena_canvas.create_oval(x - 12, y - 48, x + 12, y - 24, fill=palette["head"], outline="", tags=("sprites", tag))
        self.arena_canvas.create_rectangle(x - 14, y - 24, x + 14, y + 16, fill=palette["body"], outline="", tags=("sprites", tag))
        self.arena_canvas.create_line(x, y + 16, x - 9, y + 42, fill=palette["accent"], width=3, tags=("sprites", tag))
        self.arena_canvas.create_line(x, y + 16, x + 9, y + 42, fill=palette["accent"], width=3, tags=("sprites", tag))
        self.arena_canvas.create_line(x - 11 * direction, y - 6, x - 25 * direction, y + 8, fill=palette["accent"], width=3, tags=("sprites", tag))
        self.arena_canvas.create_line(x + 11 * direction, y - 6, x + 30 * direction, y - 16, fill="#dfe7ff", width=3, tags=("sprites", tag))
        self.arena_canvas.create_text(x, y + 58, text=name, fill="#f2f1e8", font=("Bahnschrift SemiBold", 9), tags=("sprites", tag))

    def _render_arena_sprites(self):
        self.arena_canvas.delete("sprites")

        hx, hy = self.hero_anchor
        ex, ey = self.enemy_anchor

        if self.hero:
            self._draw_character_sprite("hero_sprite", hx, hy, self.hero.name, is_enemy=False)
        else:
            self.arena_canvas.create_text(hx, hy + 12, text="No Hero", fill="#a7b2c8", font=("Calibri", 10, "italic"), tags="sprites")

        if self.enemy:
            self._draw_character_sprite("enemy_sprite", ex, ey, self.enemy.name, is_enemy=True)
        else:
            self.arena_canvas.create_text(ex, ey + 12, text="No Enemy", fill="#a7b2c8", font=("Calibri", 10, "italic"), tags="sprites")

    def _animate_strike(self, attacker: str):
        if not self.hero or not self.enemy:
            return

        if attacker == "hero":
            tag = "hero_sprite"
            direction = 1
            target_x, target_y = self.enemy_anchor
            slash_color = "#79f0e7"
        else:
            tag = "enemy_sprite"
            direction = -1
            target_x, target_y = self.hero_anchor
            slash_color = "#ff9f8d"

        for _ in range(5):
            self.arena_canvas.move(tag, direction * 6, 0)
            self.root.update_idletasks()
            self.root.update()
            self.root.after(16)

        slash = self.arena_canvas.create_line(
            target_x - 14,
            target_y - 12,
            target_x + 14,
            target_y + 12,
            fill=slash_color,
            width=4,
            tags="anim",
        )
        self.root.update_idletasks()
        self.root.update()
        self.root.after(65)
        self.arena_canvas.delete(slash)

        for _ in range(5):
            self.arena_canvas.move(tag, -direction * 6, 0)
            self.root.update_idletasks()
            self.root.update()
            self.root.after(16)

    def _animate_heal(self, target: str):
        x, y = self.hero_anchor if target == "hero" else self.enemy_anchor
        ring = self.arena_canvas.create_oval(x - 18, y - 30, x + 18, y + 6, outline=self.colors["success"], width=2, tags="anim")
        plus = self.arena_canvas.create_text(x, y - 12, text="+", fill="#b7ffd0", font=("Bahnschrift SemiBold", 14), tags="anim")
        self.root.update_idletasks()
        self.root.update()
        self.root.after(100)
        self.arena_canvas.delete(ring)
        self.arena_canvas.delete(plus)

    def _subscribe_events(self):
        event_bus.subscribe("damage_taken", self._on_damage)
        event_bus.subscribe("death", self._on_death)
        event_bus.subscribe("healed", self._on_heal)

    def _append_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        self.feed.configure(state="normal")
        self.feed.insert("end", line)
        self.feed.see("end")
        self.feed.configure(state="disabled")
        self._append_battle_feed(line)

    def _append_battle_feed(self, line: str):
        if not self.battle_feed or not self._battle_window_exists():
            return
        self.battle_feed.configure(state="normal")
        self.battle_feed.insert("end", line)
        self.battle_feed.see("end")
        self.battle_feed.configure(state="disabled")

    def _add_history(self, message: str):
        self.history_list.insert("end", message)
        # Keep only last important actions to keep the panel concise.
        while self.history_list.size() > 8:
            self.history_list.delete(0)
        self.history_list.see("end")

    def _history_items(self):
        return list(self.history_list.get(0, "end"))

    def _update_stats(self):
        self.stats_dealt_var.set(f"Hero dealt: {self.hero_damage_dealt}")
        self.stats_taken_var.set(f"Hero taken: {self.hero_damage_taken}")
        self.stats_heal_var.set(f"Hero heals: {self.hero_total_heal}")
        self._sync_battle_window_status()

    def _reset_stats(self):
        self.hero_damage_dealt = 0
        self.hero_damage_taken = 0
        self.hero_total_heal = 0
        self._update_stats()

    def _save_history_snapshot(self, winner: str, defeated: str):
        output_dir = Path("match_history")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"match_{timestamp}.txt"

        lines = [
            "GoF Arena - Match Report",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Winner: {winner}",
            f"Defeated: {defeated}",
            f"Rounds: {self.round_count}",
            "",
            "Hero Stats",
            f"Damage dealt: {self.hero_damage_dealt}",
            f"Damage taken: {self.hero_damage_taken}",
            f"Total heal: {self.hero_total_heal}",
            "",
            "Recent Combat History",
        ]
        history = self._history_items()
        if history:
            lines.extend([f"- {item}" for item in history])
        else:
            lines.append("- (no history)")

        path.write_text("\n".join(lines), encoding="utf-8")
        self._append_log(f"History saved: {path}")

    def _update_status(self):
        if self.hero:
            self.hero_var.set(f"Hero: {self.hero.name} | HP {self.hero.hp}/{self.hero.max_hp}")
            self.hero_name_var.set(self.hero.name)
            self.hero_hp_text_var.set(f"HP: {self.hero.hp}/{self.hero.max_hp}")
            self._draw_hp_bar(self.hero_hp_canvas, self.hero.hp, self.hero.max_hp)
        else:
            self.hero_var.set("Hero: (none)")
            self.hero_name_var.set("(none)")
            self.hero_hp_text_var.set("HP: 0/0")
            self._draw_hp_bar(self.hero_hp_canvas, 0, 1)

        if self.enemy:
            self.enemy_var.set(f"Enemy: {self.enemy.name} | HP {self.enemy.hp}/{self.enemy.max_hp}")
            self.enemy_name_var.set(self.enemy.name)
            self.enemy_hp_text_var.set(f"HP: {self.enemy.hp}/{self.enemy.max_hp}")
            self._draw_hp_bar(self.enemy_hp_canvas, self.enemy.hp, self.enemy.max_hp)
        else:
            self.enemy_var.set("Enemy: (none)")
            self.enemy_name_var.set("(none)")
            self.enemy_hp_text_var.set("HP: 0/0")
            self._draw_hp_bar(self.enemy_hp_canvas, 0, 1)

        self._render_arena_sprites()
        self._sync_battle_window_status()
        self._refresh_focus_mode()

    def _is_duel_active(self) -> bool:
        return bool(self.hero and self.enemy and self.hero.hp > 0 and self.enemy.hp > 0)

    def _set_demo_buttons_state(self, state: str):
        for button in self.demo_buttons:
            button.configure(state=state)

    def _refresh_focus_mode(self):
        if self._is_duel_active():
            self._set_demo_buttons_state("disabled")
            if self._battle_window_exists():
                self.battle_window.lift()
                self.battle_window.focus_set()
        else:
            self._set_demo_buttons_state("normal")

    def _battle_window_exists(self) -> bool:
        return self.battle_window is not None and self.battle_window.winfo_exists()

    def _ensure_battle_interface(self):
        if not (self.hero and self.enemy):
            return
        if self._battle_window_exists():
            self._terraria_init_world(reset_positions=True)
            self.battle_window.lift()
            self._sync_battle_window_status()
            self._refresh_focus_mode()
            return
        self._open_battle_interface()

    def _open_battle_interface(self):
        self.battle_window = tk.Toplevel(self.root)
        self.battle_window.title("Battle Interface")
        self.battle_window.geometry("760x560")
        self.battle_window.minsize(680, 500)
        self.battle_window.configure(bg=self.colors["bg"])
        self.battle_window.transient(self.root)

        def _on_close():
            if self._is_duel_active():
                messagebox.showinfo("Battle Active", "Finish or reset the duel before closing Battle Interface.")
                self.battle_window.lift()
                self.battle_window.focus_set()
                return
            self._terraria_stop_loop()
            self.terraria_keys.clear()
            self.battle_window.destroy()
            self.battle_window = None
            self.battle_feed = None
            self.terraria_canvas = None
            self._refresh_focus_mode()

        self.battle_window.protocol("WM_DELETE_WINDOW", _on_close)

        self.battle_status_var = tk.StringVar(value="Battle ready")
        self.battle_round_var = tk.StringVar(value="Round: 0")
        self.battle_hero_hp_var = tk.StringVar(value="Hero HP: -")
        self.battle_enemy_hp_var = tk.StringVar(value="Enemy HP: -")
        self.battle_stats_var = tk.StringVar(value="Dealt 0 | Taken 0 | Heal 0")
        self.battle_weapon_var = tk.StringVar(value=f"Weapon: {self.hero_weapon_kind.get()} (1/2/3)")

        top = ttk.Frame(self.battle_window, style="Card.TFrame")
        top.pack(fill="x", padx=12, pady=(12, 8))
        ttk.Label(top, text="Arena Battle Mode", style="Header.TLabel").pack(anchor="w")
        ttk.Label(top, textvariable=self.battle_status_var, style="ArenaMeta.TLabel").pack(anchor="w", pady=(2, 0))
        ttk.Label(top, textvariable=self.battle_round_var, style="ArenaName.TLabel").pack(anchor="w", pady=(2, 0))
        ttk.Label(top, textvariable=self.battle_weapon_var, style="ArenaMeta.TLabel").pack(anchor="w", pady=(0, 2))

        status = ttk.LabelFrame(self.battle_window, text="Fighters", style="Card.TLabelframe")
        status.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Label(status, textvariable=self.battle_hero_hp_var, style="ArenaMeta.TLabel").pack(anchor="w", padx=8, pady=(8, 2))
        ttk.Label(status, textvariable=self.battle_enemy_hp_var, style="ArenaMeta.TLabel").pack(anchor="w", padx=8, pady=2)
        ttk.Label(status, textvariable=self.battle_stats_var, style="ArenaMeta.TLabel").pack(anchor="w", padx=8, pady=(2, 8))

        terraria_box = ttk.LabelFrame(self.battle_window, text="GoF Mode (A/D move, W/Space jump, F attack, H heal, 1=Laser 2=Spear 3=Sword)", style="Card.TLabelframe")
        terraria_box.pack(fill="x", padx=12, pady=(0, 8))
        self.terraria_canvas = tk.Canvas(
            terraria_box,
            width=620,
            height=240,
            bg="#6fa0df",
            highlightthickness=0,
            relief="flat",
        )
        self.terraria_canvas.pack(fill="x", padx=8, pady=8)

        controls = ttk.LabelFrame(self.battle_window, text="Battle Actions", style="Card.TLabelframe")
        controls.pack(fill="x", padx=12, pady=(0, 8))

        sliders = ttk.Frame(controls, style="Card.TFrame")
        sliders.pack(fill="x", padx=8, pady=8)

        ttk.Label(sliders, text="Hero attack dmg", style="FieldLabel.TLabel").grid(row=0, column=0, sticky="w", pady=2)
        tk.Spinbox(sliders, from_=1, to=60, textvariable=self.battle_attack_var, width=6).grid(row=0, column=1, sticky="w", padx=(8, 20))

        ttk.Label(sliders, text="Hero heal", style="FieldLabel.TLabel").grid(row=0, column=2, sticky="w", pady=2)
        tk.Spinbox(sliders, from_=1, to=60, textvariable=self.battle_heal_var, width=6).grid(row=0, column=3, sticky="w", padx=(8, 20))

        ttk.Label(sliders, text="Enemy dmg", style="FieldLabel.TLabel").grid(row=0, column=4, sticky="w", pady=2)
        tk.Spinbox(sliders, from_=0, to=60, textvariable=self.battle_enemy_attack_var, width=6).grid(row=0, column=5, sticky="w", padx=(8, 0))

        buttons = ttk.Frame(controls, style="Card.TFrame")
        buttons.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(buttons, text="Hero Attack", command=self._battle_attack_action, style="Emphasis.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Hero Heal", command=self._battle_heal_action).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Rewind Hero", command=self._battle_rewind_hero).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Manual Round", command=self._battle_manual_round_action).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Quick Duel", command=self.quick_duel).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="End Fight", command=self._end_fight_and_close, style="Danger.TButton").pack(side="right", padx=(0, 6))
        ttk.Button(buttons, text="Close", command=_on_close, style="Danger.TButton").pack(side="right")

        feed_box = ttk.LabelFrame(self.battle_window, text="Live Battle Feed", style="Card.TLabelframe")
        feed_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        feed_shell = ttk.Frame(feed_box, style="Card.TFrame")
        feed_shell.pack(fill="both", expand=True, padx=8, pady=8)

        self.battle_feed = tk.Text(
            feed_shell,
            wrap="word",
            height=14,
            padx=10,
            pady=10,
            bg=self.colors["feed_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="flat",
            font=("Consolas", 10),
        )
        scroll = ttk.Scrollbar(feed_shell, orient="vertical", command=self.battle_feed.yview)
        self.battle_feed.configure(yscrollcommand=scroll.set)
        self.battle_feed.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self.battle_feed.configure(state="disabled")

        self._append_log("Battle interface opened.")
        self._terraria_init_world(reset_positions=True)
        self.battle_window.bind("<KeyPress>", self._on_battle_key_press)
        self.battle_window.bind("<KeyRelease>", self._on_battle_key_release)
        self.battle_window.focus_set()
        self._terraria_start_loop()
        self._sync_battle_window_status()
        self._refresh_focus_mode()

    def _terraria_init_world(self, reset_positions: bool = False):
        if not self.terraria_state or reset_positions:
            enemy_archetype = self._terraria_detect_enemy_archetype()
            self.terraria_state = {
                "world_width": 1600.0,
                "ground_y": 188.0,
                "camera_x": 0.0,
                "hero_x": 160.0,
                "hero_y": 188.0,
                "hero_vy": 0.0,
                "hero_w": 22.0,
                "hero_h": 36.0,
                "hero_on_ground": True,
                "enemy_x": 620.0,
                "enemy_y": 188.0,
                "enemy_vy": 0.0,
                "enemy_w": 24.0,
                "enemy_h": 38.0,
                "enemy_on_ground": True,
                "enemy_last_hit": 0.0,
                "enemy_last_shot": 0.0,
                "enemy_last_dash": 0.0,
                "hero_facing": 1,
                "enemy_facing": -1,
                "projectiles": [],
                "effects": [],
                "pickups": [],
                "pickup_last_spawn": time.time(),
                "hero_ammo": {"Blaster": 24, "Spear": 12},
                "hero_ammo_max": {"Blaster": 48, "Spear": 24},
                "enemy_archetype": enemy_archetype,
                "wave_number": 1,
                "wave_kills": 0,
                "wave_spawn_pending": False,
                "wave_spawn_at": 0.0,
                "platforms": [
                    (220.0, 420.0, 150.0),
                    (540.0, 760.0, 126.0),
                    (860.0, 1120.0, 158.0),
                    (1220.0, 1450.0, 136.0),
                ],
            }
        self._terraria_draw_world()

    def _terraria_detect_enemy_archetype(self) -> str:
        if not self.enemy:
            return random.choice(["slime", "archer", "brute"])

        name = self.enemy.name.lower()
        if "slime" in name or "goblin" in name:
            return "slime"
        if "archer" in name:
            return "archer"
        if "brute" in name or "troll" in name or "orc" in name:
            return "brute"
        return random.choice(["slime", "archer", "brute"])

    def _terraria_roll_wave_archetype(self, wave_number: int) -> str:
        if wave_number <= 2:
            return random.choice(["slime", "archer"])
        if wave_number <= 4:
            return random.choice(["slime", "archer", "brute"])
        # Later waves skew towards brute/archer for higher pressure.
        return random.choice(["archer", "brute", "brute", "slime"])

    def _terraria_build_enemy_for_wave(self, wave_number: int, archetype: str) -> Character:
        # Abstract Factory provides theme context for the current wave.
        faction_factory = SciFiFactionFactory() if wave_number % 2 == 0 else MedievalFactionFactory()
        faction_enemy = faction_factory.create_enemy()
        faction_weapon = faction_factory.create_weapon()

        # Factory Method fallback for periodic boss-like waves.
        if wave_number % 5 == 0:
            if archetype == "brute":
                base_enemy = TrollFactory().create_enemy()
            elif archetype == "archer":
                base_enemy = OrcFactory().create_enemy()
            else:
                base_enemy = GoblinFactory().create_enemy()
        else:
            # Flyweight shared archetype basis.
            fly_key = "troll" if archetype == "brute" else ("orc" if archetype == "archer" else "goblin")
            base_enemy = self.flyweight_factory.create_enemy(fly_key, name=faction_enemy.name)

        # Adapter appears on some late waves to integrate legacy enemy API into active battle flow.
        if wave_number % 7 == 0 and archetype == "brute":
            legacy = LegacyEnemy(f"Legacy Brute W{wave_number}", max(120, base_enemy.max_hp + 20))
            base_enemy = LegacyEnemyAdapter(legacy)

        # Prototype clone from prepared base to avoid rebuilding from scratch repeatedly.
        proto_key = f"wave_{archetype}"
        self.prototype_registry.register(proto_key, CharacterPrototype(base_enemy))
        cloned = self.prototype_registry.clone(proto_key)

        # Builder applies final scaled runtime stats.
        base_hp = 90 + (wave_number * 12)
        hp_factor = 0.95 if archetype == "slime" else (1.05 if archetype == "archer" else 1.3)
        hp = max(70, int(base_hp * hp_factor))
        name = f"{cloned.name} W{wave_number}"
        desc = (cloned.description or "") + f" | faction weapon: {faction_weapon}"
        return (
            CharacterBuilder()
            .name(name)
            .max_hp(hp)
            .initial_hp(hp)
            .description(desc)
            .build()
        )

    def _terraria_difficulty_tier(self) -> int:
        wave_number = int(self.terraria_state.get("wave_number", 1)) if self.terraria_state else 1
        return max(0, (wave_number - 1) // 3)

    def _terraria_cd_factor(self) -> float:
        # Every 3 waves, enemy cooldowns shorten.
        tier = self._terraria_difficulty_tier()
        return max(0.52, 1.0 - (0.09 * tier))

    def _terraria_speed_factor(self) -> float:
        # Every 3 waves, enemy movement gets faster.
        tier = self._terraria_difficulty_tier()
        return 1.0 + (0.08 * tier)

    def _terraria_schedule_next_wave(self):
        if not self.terraria_state:
            return
        wave_number = int(self.terraria_state.get("wave_number", 1)) + 1
        self.terraria_state["wave_number"] = wave_number
        self.terraria_state["wave_spawn_pending"] = True
        self.terraria_state["wave_spawn_at"] = time.time() + 1.2
        self._append_log(f"Wave {wave_number} incoming...")
        self._add_history(f"Wave {wave_number} incoming")
        self.battle_subject.notify("wave_incoming", {"wave": wave_number})

    def _terraria_try_spawn_next_wave(self):
        if not self.terraria_state or not bool(self.terraria_state.get("wave_spawn_pending", False)):
            return
        if self.hero is None or self.hero.hp <= 0:
            return
        if time.time() < float(self.terraria_state.get("wave_spawn_at", 0.0)):
            return

        wave_number = int(self.terraria_state.get("wave_number", 1))
        archetype = self._terraria_roll_wave_archetype(wave_number)
        self.enemy = self._terraria_build_enemy_for_wave(wave_number, archetype)
        self.terraria_state["enemy_archetype"] = archetype
        self.terraria_state["enemy_x"] = min(float(self.terraria_state.get("world_width", 1600.0)) - 120.0, float(self.terraria_state.get("hero_x", 200.0)) + 320.0)
        self.terraria_state["enemy_y"] = self._terraria_floor_for_x(float(self.terraria_state["enemy_x"]))
        self.terraria_state["enemy_vy"] = 0.0
        self.terraria_state["enemy_on_ground"] = True
        self.terraria_state["enemy_last_hit"] = 0.0
        self.terraria_state["enemy_last_shot"] = 0.0
        self.terraria_state["enemy_last_dash"] = 0.0
        self.terraria_state["wave_spawn_pending"] = False

        if archetype == "slime":
            self.enemy_attack_context.set_strategy(ChaosStrategy())
        elif archetype == "archer":
            self.enemy_attack_context.set_strategy(BalancedStrategy())
        else:
            self.enemy_attack_context.set_strategy(AggressiveStrategy())

        tier = self._terraria_difficulty_tier()

        self._append_log(f"Wave {wave_number} spawned: {self.enemy.name} [{archetype.upper()}] | Tier {tier}")
        self._add_history(f"Wave {wave_number}: {self.enemy.name} (T{tier})")
        self.battle_subject.notify(
            "wave_spawned",
            {
                "wave": wave_number,
                "archetype": archetype,
                "strategy": self.enemy_attack_context.strategy.name,
            },
        )
        self._battle_save_checkpoint()

    def _terraria_start_loop(self):
        if self.terraria_loop_after_id is not None:
            return
        self._terraria_loop()

    def _terraria_stop_loop(self):
        if self.terraria_loop_after_id is not None:
            try:
                self.root.after_cancel(self.terraria_loop_after_id)
            except tk.TclError:
                pass
            self.terraria_loop_after_id = None

    def _on_battle_key_press(self, event):
        key = event.keysym.lower()
        if key in {"a", "d", "left", "right", "w", "up", "space", "f", "h", "1", "2", "3"}:
            self.terraria_keys.add(key)

        if key in {"1", "2", "3"}:
            weapons = {"1": "Blaster", "2": "Spear", "3": "Sword"}
            selected = weapons[key]
            self.hero_weapon_kind.set(selected)
            if self.battle_weapon_var:
                self.battle_weapon_var.set(f"Weapon: {selected} (1/2/3)")
            self._append_log(f"GoF weapon switched: {selected}")
        elif key == "f":
            self._terraria_attack_action()
        elif key == "h":
            self._terraria_heal_action()

    def _on_battle_key_release(self, event):
        key = event.keysym.lower()
        if key in self.terraria_keys:
            self.terraria_keys.remove(key)

    def _terraria_attack_action(self):
        if not self._battle_ready():
            return

        self._battle_save_checkpoint()

        base = max(1, int(self.battle_attack_var.get()))
        dmg = max(1, base + random.randint(-3, 3))
        weapon = self._current_weapon(dmg)
        weapon_name = weapon.__class__.__name__
        dist = abs(float(self.terraria_state["hero_x"]) - float(self.terraria_state["enemy_x"]))
        dealt = 0

        if not self._terraria_consume_ammo(weapon_name):
            self._append_log(f"No ammo for {weapon_name}. Find ammo pickup.")
            self._terraria_spawn_effect(
                {
                    "type": "text",
                    "x": float(self.terraria_state["hero_x"]),
                    "y": float(self.terraria_state["hero_y"]) - 58,
                    "ttl": 20,
                    "text": "NO AMMO",
                    "color": "#ffcf9f",
                }
            )
            return

        if weapon_name == "Sword":
            if dist > 78:
                self._append_log("GoF slash missed (move closer).")
                self._terraria_spawn_effect(
                    {
                        "type": "text",
                        "x": float(self.terraria_state["hero_x"]),
                        "y": float(self.terraria_state["hero_y"]) - 56,
                        "ttl": 16,
                        "text": "MISS",
                        "color": "#ffe39a",
                    }
                )
                return
            self._terraria_spawn_sword_slash_effect()
            sword_damage = max(0, weapon.damage_mode.transform(weapon.base_damage))
            dealt = self._execute_damage_command(self.enemy, sword_damage, "hero_sword")
        elif weapon_name == "Blaster":
            dealt = self._terraria_fire_laser(dmg)
        else:
            self._terraria_spawn_projectile(owner="hero", damage=dmg)
            self._append_log(f"GoF projectile launched with {weapon.name}.")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        if dealt > 0:
            action_name = "slash" if weapon_name == "Sword" else "laser"
            self.last_action_var.set(f"Last action: GoF {action_name} with {weapon.name} for {dealt}")
            self._add_history(f"GoF {action_name}: {dealt} via {weapon.name}")
        else:
            action_name = "shot" if weapon_name != "Sword" else "slash"
            self.last_action_var.set(f"Last action: GoF {action_name} with {weapon.name}")
            self._add_history(f"GoF {action_name} via {weapon.name}")
        self._update_status()

    def _terraria_heal_action(self):
        if not self._battle_ready():
            return

        self._battle_save_checkpoint()

        heal = max(1, int(self.battle_heal_var.get()))
        self._execute_heal_command(self.hero, heal, "hero_heal")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self.last_action_var.set(f"Last action: GoF heal for {heal}")
        self._add_history(f"GoF heal: +{heal}")
        self._update_status()

    def _terraria_enemy_ai(self):
        if not self._is_duel_active():
            return

        hero_x = float(self.terraria_state["hero_x"])
        enemy_x = float(self.terraria_state["enemy_x"])
        world_width = float(self.terraria_state["world_width"])
        archetype = str(self.terraria_state.get("enemy_archetype", "slime"))
        speed_factor = self._terraria_speed_factor()
        cd_factor = self._terraria_cd_factor()
        tier = self._terraria_difficulty_tier()
        now = time.time()
        dist = abs(float(self.terraria_state["hero_x"]) - float(self.terraria_state["enemy_x"]))

        if hero_x > enemy_x:
            self.terraria_state["enemy_facing"] = 1
        else:
            self.terraria_state["enemy_facing"] = -1

        if archetype == "slime":
            # Slime: short hops towards player + quick close hits.
            if dist > 34:
                hop_speed = 1.7 * speed_factor
                hop = hop_speed if hero_x > enemy_x else -hop_speed
                self.terraria_state["enemy_x"] = max(28.0, min(world_width - 28.0, enemy_x + hop))
            if bool(self.terraria_state.get("enemy_on_ground", True)) and now - float(self.terraria_state.get("enemy_last_dash", 0.0)) > (1.2 * cd_factor):
                self.terraria_state["enemy_vy"] = -8.2 - (0.4 * tier)
                self.terraria_state["enemy_last_dash"] = now
            if dist < 42 and now - float(self.terraria_state["enemy_last_hit"]) >= (0.75 * cd_factor):
                enemy_dmg = max(1, int(self.battle_enemy_attack_var.get()) - 1 + random.randint(0, 2) + tier)
                enemy_dmg = self.enemy_attack_context.strategy.compute_damage(enemy_dmg)
                self._execute_damage_command(self.hero, enemy_dmg, f"enemy_{archetype}_melee")
                self.terraria_state["enemy_last_hit"] = now
                self._append_log(f"GoF slime hit: {self.enemy.name} deals {enemy_dmg}")

        elif archetype == "archer":
            # Archer: keep distance and fire often.
            preferred = max(170, 240 - (10 * tier))
            speed = 2.6 * speed_factor
            if dist < preferred - 20:
                direction = -1 if hero_x > enemy_x else 1
                self.terraria_state["enemy_x"] = max(28.0, min(world_width - 28.0, enemy_x + (direction * speed)))
            elif dist > preferred + 40:
                direction = 1 if hero_x > enemy_x else -1
                self.terraria_state["enemy_x"] = max(28.0, min(world_width - 28.0, enemy_x + (direction * speed)))

            if now - float(self.terraria_state["enemy_last_shot"]) >= (1.05 * cd_factor):
                enemy_dmg = max(1, int(self.battle_enemy_attack_var.get()) + random.randint(-1, 1) + max(0, tier - 1))
                enemy_dmg = self.enemy_attack_context.strategy.compute_damage(enemy_dmg)
                self._terraria_spawn_projectile(owner="enemy", damage=enemy_dmg)
                self.terraria_state["enemy_last_shot"] = now

        else:
            # Brute: slower but heavy melee + occasional rush.
            speed = 1.35 * speed_factor
            if dist > 44:
                if hero_x > enemy_x:
                    self.terraria_state["enemy_x"] = min(world_width - 28.0, enemy_x + speed)
                else:
                    self.terraria_state["enemy_x"] = max(28.0, enemy_x - speed)

            if dist < 46 and now - float(self.terraria_state["enemy_last_hit"]) >= (1.35 * cd_factor):
                enemy_dmg = max(2, int(self.battle_enemy_attack_var.get()) + random.randint(2, 5) + (tier * 2))
                enemy_dmg = self.enemy_attack_context.strategy.compute_damage(enemy_dmg)
                self._execute_damage_command(self.hero, enemy_dmg, f"enemy_{archetype}_smash")
                self.terraria_state["enemy_last_hit"] = now
                self._append_log(f"GoF brute smash: {self.enemy.name} deals {enemy_dmg}")

            if dist > 120 and now - float(self.terraria_state.get("enemy_last_dash", 0.0)) >= (2.6 * cd_factor):
                rush_distance = 22 + (2 * tier)
                rush = rush_distance if hero_x > enemy_x else -rush_distance
                self.terraria_state["enemy_x"] = max(28.0, min(world_width - 28.0, float(self.terraria_state["enemy_x"]) + rush))
                self.terraria_state["enemy_last_dash"] = now

    def _terraria_spawn_pickups(self):
        pickups = self.terraria_state.get("pickups", [])
        if not isinstance(pickups, list):
            return

        tier = self._terraria_difficulty_tier()
        now = time.time()
        last_spawn = float(self.terraria_state.get("pickup_last_spawn", now))
        if len(pickups) >= 5:
            return
        spawn_interval = min(10.0, 6.0 + (0.55 * tier))
        if now - last_spawn < spawn_interval:
            return

        x = random.uniform(80.0, float(self.terraria_state.get("world_width", 1600.0)) - 80.0)
        y = self._terraria_floor_for_x(x)
        health_chance = max(0.18, 0.55 - (0.07 * tier))
        kind = "health" if random.random() < health_chance else "ammo"
        amount = random.randint(8, 16) if kind == "health" else random.randint(4, 8)

        pickups.append({"x": x, "y": y, "kind": kind, "amount": amount, "ttl": 520})
        self.terraria_state["pickup_last_spawn"] = now

    def _terraria_update_pickups(self):
        pickups = self.terraria_state.get("pickups", [])
        if not isinstance(pickups, list):
            return

        hero_x = float(self.terraria_state.get("hero_x", 0.0))
        hero_y = float(self.terraria_state.get("hero_y", 0.0))
        ammo = self.terraria_state.get("hero_ammo", {})
        ammo_max = self.terraria_state.get("hero_ammo_max", {})

        survivors = []
        for item in pickups:
            if not isinstance(item, dict):
                continue

            item["ttl"] = int(item.get("ttl", 0)) - 1
            if int(item["ttl"]) <= 0:
                continue

            x = float(item.get("x", 0.0))
            y = float(item.get("y", 0.0))
            if abs(hero_x - x) < 20 and abs(hero_y - y) < 26:
                kind = str(item.get("kind", "health"))
                amount = int(item.get("amount", 0))
                if kind == "health":
                    if self.hero and self.hero.hp > 0:
                        self.hero.heal(amount)
                        self._append_log(f"Pickup: +{amount} HP")
                else:
                    if isinstance(ammo, dict) and isinstance(ammo_max, dict):
                        ammo["Blaster"] = min(int(ammo_max.get("Blaster", 48)), int(ammo.get("Blaster", 0)) + amount)
                        ammo["Spear"] = min(int(ammo_max.get("Spear", 24)), int(ammo.get("Spear", 0)) + max(1, amount // 2))
                    self._append_log(f"Pickup: +{amount} ammo")
                self._terraria_spawn_effect(
                    {
                        "type": "text",
                        "x": x,
                        "y": y - 20,
                        "ttl": 24,
                        "text": "+PICKUP",
                        "color": "#d5ffd4",
                    }
                )
                continue

            survivors.append(item)

        self.terraria_state["pickups"] = survivors

    def _terraria_consume_ammo(self, weapon_name: str) -> bool:
        if weapon_name == "Sword":
            return True

        ammo = self.terraria_state.get("hero_ammo", {})
        if not isinstance(ammo, dict):
            return True

        current = int(ammo.get(weapon_name, 0))
        if current <= 0:
            return False
        ammo[weapon_name] = current - 1
        return True

    def _battle_save_checkpoint(self):
        if not self.hero:
            return
        self.hero_state_caretaker.push(CharacterStateOriginator.save(self._unwrap_combatant(self.hero)))
        # Keep only the latest snapshots so restore remains bounded.
        if self.hero_state_caretaker.size() > 25:
            self.hero_state_caretaker.pop()

    def _battle_rewind_hero(self):
        if not self.hero:
            return
        snapshot = self.hero_state_caretaker.pop()
        if not snapshot:
            self._append_log("No checkpoint available for rewind.")
            return
        CharacterStateOriginator.restore(self._unwrap_combatant(self.hero), snapshot)
        self.battle_subject.notify("hero_rewind", {"hp": self.hero.hp})
        self._append_log("Hero restored from checkpoint.")
        self._add_history("Rewind hero")
        self._update_status()

    def _execute_damage_command(self, target: Character, amount: int, source: str) -> int:
        dmg = max(0, int(amount))
        if dmg <= 0:
            return 0
        self.command_invoker.execute(DamageCommand(target, dmg))
        self.battle_subject.notify("damage_command", {"target": target.name, "amount": dmg, "source": source})
        return dmg

    def _execute_heal_command(self, target: Character, amount: int, source: str) -> int:
        heal = max(0, int(amount))
        if heal <= 0:
            return 0
        self.command_invoker.execute(HealCommand(target, heal))
        self.battle_subject.notify("heal_command", {"target": target.name, "amount": heal, "source": source})
        return heal

    def _terraria_apply_gravity(self):
        gravity = 0.75
        for prefix in ("hero", "enemy"):
            vy_key = f"{prefix}_vy"
            y_key = f"{prefix}_y"
            on_ground_key = f"{prefix}_on_ground"
            x_key = f"{prefix}_x"
            prev_y = float(self.terraria_state[y_key])
            floor_y = self._terraria_floor_for_x(float(self.terraria_state[x_key]))

            self.terraria_state[vy_key] = float(self.terraria_state[vy_key]) + gravity
            self.terraria_state[y_key] = float(self.terraria_state[y_key]) + float(self.terraria_state[vy_key])

            if float(self.terraria_state[y_key]) >= floor_y:
                self.terraria_state[y_key] = floor_y
                self.terraria_state[vy_key] = 0.0
                self.terraria_state[on_ground_key] = True
            else:
                self.terraria_state[on_ground_key] = False

            # Landing check on platforms only when descending.
            if float(self.terraria_state[vy_key]) >= 0:
                body_h = float(self.terraria_state[f"{prefix}_h"])
                top_prev = prev_y - body_h
                top_now = float(self.terraria_state[y_key]) - body_h
                x = float(self.terraria_state[x_key])
                for p1, p2, py in self.terraria_state.get("platforms", []):
                    if p1 <= x <= p2 and top_prev <= py <= top_now:
                        self.terraria_state[y_key] = py + body_h
                        self.terraria_state[vy_key] = 0.0
                        self.terraria_state[on_ground_key] = True
                        break

    def _terraria_hero_movement(self):
        if not self._is_duel_active():
            return

        speed = 3.6
        world_width = float(self.terraria_state["world_width"])
        if "a" in self.terraria_keys or "left" in self.terraria_keys:
            self.terraria_state["hero_x"] = max(26.0, float(self.terraria_state["hero_x"]) - speed)
            self.terraria_state["hero_facing"] = -1
        if "d" in self.terraria_keys or "right" in self.terraria_keys:
            self.terraria_state["hero_x"] = min(world_width - 26.0, float(self.terraria_state["hero_x"]) + speed)
            self.terraria_state["hero_facing"] = 1

        wants_jump = "w" in self.terraria_keys or "up" in self.terraria_keys or "space" in self.terraria_keys
        if wants_jump and bool(self.terraria_state["hero_on_ground"]):
            self.terraria_state["hero_vy"] = -10.6
            self.terraria_state["hero_on_ground"] = False

    def _terraria_floor_for_x(self, x: float) -> float:
        return float(self.terraria_state.get("ground_y", 188.0))

    def _terraria_spawn_projectile(self, owner: str, damage: int):
        projectiles = self.terraria_state.get("projectiles", [])
        if not isinstance(projectiles, list):
            return

        if owner == "hero":
            x = float(self.terraria_state["hero_x"])
            y = float(self.terraria_state["hero_y"]) - 24
            direction = int(self.terraria_state["hero_facing"])
            speed = 8.2
            color = "#f6ddb0"
            target = "enemy"
        else:
            x = float(self.terraria_state["enemy_x"])
            y = float(self.terraria_state["enemy_y"]) - 26
            direction = int(self.terraria_state["enemy_facing"])
            speed = 7.0
            color = "#ffb1a3"
            target = "hero"

        projectiles.append(
            {
                "x": x,
                "y": y,
                "vx": direction * speed,
                "vy": 0.0,
                "ttl": 120,
                "owner": owner,
                "target": target,
                "damage": max(1, int(damage)),
                "color": color,
            }
        )

    def _terraria_update_projectiles(self):
        projectiles = self.terraria_state.get("projectiles", [])
        if not isinstance(projectiles, list):
            return

        world_width = float(self.terraria_state["world_width"])
        hero_left = float(self.terraria_state["hero_x"]) - 12
        hero_right = float(self.terraria_state["hero_x"]) + 12
        hero_top = float(self.terraria_state["hero_y"]) - 46
        hero_bottom = float(self.terraria_state["hero_y"])

        enemy_left = float(self.terraria_state["enemy_x"]) - 12
        enemy_right = float(self.terraria_state["enemy_x"]) + 12
        enemy_top = float(self.terraria_state["enemy_y"]) - 48
        enemy_bottom = float(self.terraria_state["enemy_y"])

        survivors = []
        for shot in projectiles:
            if not isinstance(shot, dict):
                continue
            shot["x"] = float(shot.get("x", 0.0)) + float(shot.get("vx", 0.0))
            shot["y"] = float(shot.get("y", 0.0)) + float(shot.get("vy", 0.0))
            shot["ttl"] = int(shot.get("ttl", 0)) - 1

            x = float(shot["x"])
            y = float(shot["y"])
            if shot["ttl"] <= 0 or x < 0 or x > world_width or y < 0 or y > 240:
                continue

            damage = max(1, int(shot.get("damage", 1)))
            owner = str(shot.get("owner", "hero"))
            hit = False

            if owner == "hero":
                if enemy_left <= x <= enemy_right and enemy_top <= y <= enemy_bottom and self.enemy and self.enemy.hp > 0:
                    self._execute_damage_command(self.enemy, damage, "hero_projectile")
                    self._append_log(f"Projectile hit: {self.enemy.name} takes {damage}")
                    self._add_history(f"Projectile: {damage} to {self.enemy.name}")
                    hit = True
            else:
                if hero_left <= x <= hero_right and hero_top <= y <= hero_bottom and self.hero and self.hero.hp > 0:
                    self._execute_damage_command(self.hero, damage, "enemy_projectile")
                    self._append_log(f"Projectile hit: {self.hero.name} takes {damage}")
                    self._add_history(f"Projectile: {damage} to {self.hero.name}")
                    hit = True

            if not hit:
                survivors.append(shot)

        self.terraria_state["projectiles"] = survivors

    def _terraria_spawn_effect(self, effect: dict):
        effects = self.terraria_state.get("effects", [])
        if isinstance(effects, list):
            effects.append(effect)

    def _terraria_update_effects(self):
        effects = self.terraria_state.get("effects", [])
        if not isinstance(effects, list):
            return

        survivors = []
        for fx in effects:
            if not isinstance(fx, dict):
                continue
            ttl = int(fx.get("ttl", 0)) - 1
            fx["ttl"] = ttl
            if fx.get("type") == "text":
                fx["y"] = float(fx.get("y", 0.0)) - 0.9
            if ttl > 0:
                survivors.append(fx)
        self.terraria_state["effects"] = survivors

    def _terraria_spawn_sword_slash_effect(self):
        hero_x = float(self.terraria_state["hero_x"])
        hero_y = float(self.terraria_state["hero_y"])
        facing = int(self.terraria_state["hero_facing"])
        self._terraria_spawn_effect(
            {
                "type": "slash",
                "x": hero_x + (18 * facing),
                "y": hero_y - 20,
                "ttl": 10,
                "facing": facing,
                "color": "#fff2b8",
            }
        )

    def _terraria_fire_laser(self, damage: int) -> int:
        if not self.hero or not self.enemy:
            return 0

        hero_x = float(self.terraria_state["hero_x"])
        hero_y = float(self.terraria_state["hero_y"]) - 24
        enemy_x = float(self.terraria_state["enemy_x"])
        enemy_y = float(self.terraria_state["enemy_y"]) - 28
        facing = int(self.terraria_state["hero_facing"])

        max_range = 560.0
        if facing > 0:
            target_x = hero_x + max_range
            in_front = enemy_x >= hero_x
        else:
            target_x = hero_x - max_range
            in_front = enemy_x <= hero_x

        hit = in_front and abs(enemy_x - hero_x) <= max_range and abs(enemy_y - hero_y) <= 36
        if hit:
            target_x = enemy_x

        self._terraria_spawn_effect(
            {
                "type": "laser",
                "x1": hero_x,
                "y1": hero_y,
                "x2": target_x,
                "y2": enemy_y if hit else hero_y,
                "ttl": 8,
                "color": "#7ef7ff",
            }
        )

        if not hit:
            self._append_log("GoF laser missed.")
            return 0

        self._execute_damage_command(self.enemy, damage, "hero_laser")
        return damage

    def _terraria_update_camera(self):
        if not self.terraria_canvas:
            return
        width = int(self.terraria_canvas.winfo_width()) or 620
        world_width = float(self.terraria_state["world_width"])
        desired = float(self.terraria_state["hero_x"]) - (width / 2)
        max_cam = max(0.0, world_width - width)
        self.terraria_state["camera_x"] = max(0.0, min(max_cam, desired))

    def _terraria_draw_world(self):
        if not self.terraria_canvas:
            return

        c = self.terraria_canvas
        c.delete("all")

        width = int(c.winfo_width()) or 620
        world_width = float(self.terraria_state.get("world_width", 1600.0))
        camera_x = float(self.terraria_state.get("camera_x", 0.0))
        ground = int(float(self.terraria_state.get("ground_y", 188.0)))
        parallax = camera_x * 0.25

        def sx(world_x: float) -> float:
            return world_x - camera_x

        c.create_rectangle(0, 0, width, 120, fill="#77ace8", outline="")
        c.create_rectangle(0, 120, width, ground, fill="#9fd0ff", outline="")
        c.create_rectangle(0, ground, width, 240, fill="#7b5737", outline="")

        for cx in range(-200, int(world_width), 280):
            cx_screen = sx(cx - parallax)
            c.create_oval(cx_screen, 20, cx_screen + 130, 80, fill="#d9ecff", outline="")

        for x in range(0, width, 20):
            c.create_rectangle(x, ground - 12, x + 20, ground, fill="#5bb05b", outline="#4a9d4a")
            c.create_line(x, ground, x, 240, fill="#5e412b")

        platforms = self.terraria_state.get("platforms", [])
        if isinstance(platforms, list):
            for p1, p2, py in platforms:
                x1 = sx(float(p1))
                x2 = sx(float(p2))
                if x2 < -40 or x1 > width + 40:
                    continue
                c.create_rectangle(x1, py - 8, x2, py, fill="#9a7448", outline="#5f452c")
                for tx in range(int(x1), int(x2), 18):
                    c.create_line(tx, py - 8, tx + 6, py, fill="#6e4f31")

        hero_x = sx(float(self.terraria_state["hero_x"]))
        hero_y = float(self.terraria_state["hero_y"])
        enemy_x = sx(float(self.terraria_state["enemy_x"]))
        enemy_y = float(self.terraria_state["enemy_y"])

        c.create_rectangle(hero_x - 11, hero_y - 36, hero_x + 11, hero_y, fill="#52a6ff", outline="#17385c", width=2)
        c.create_rectangle(hero_x - 8, hero_y - 46, hero_x + 8, hero_y - 36, fill="#f2d3ae", outline="#6f5237")
        c.create_text(hero_x, hero_y - 56, text=self.hero.name if self.hero else "Hero", fill="#10253d", font=("Consolas", 8, "bold"))

        c.create_rectangle(enemy_x - 12, enemy_y - 38, enemy_x + 12, enemy_y, fill="#d56a6a", outline="#5a1f1f", width=2)
        c.create_rectangle(enemy_x - 8, enemy_y - 48, enemy_x + 8, enemy_y - 38, fill="#f1d2b6", outline="#69442b")
        c.create_text(enemy_x, enemy_y - 58, text=self.enemy.name if self.enemy else "Enemy", fill="#3a1414", font=("Consolas", 8, "bold"))

        projectiles = self.terraria_state.get("projectiles", [])
        if isinstance(projectiles, list):
            for shot in projectiles:
                if not isinstance(shot, dict):
                    continue
                px = sx(float(shot.get("x", 0.0)))
                py = float(shot.get("y", 0.0))
                if -12 <= px <= width + 12:
                    c.create_oval(px - 4, py - 4, px + 4, py + 4, fill=str(shot.get("color", "#ffffff")), outline="")

        pickups = self.terraria_state.get("pickups", [])
        if isinstance(pickups, list):
            for item in pickups:
                if not isinstance(item, dict):
                    continue
                px = sx(float(item.get("x", 0.0)))
                py = float(item.get("y", 0.0)) - 8
                if -16 <= px <= width + 16:
                    if str(item.get("kind", "health")) == "health":
                        c.create_oval(px - 7, py - 7, px + 7, py + 7, fill="#ff6d7f", outline="#7d1f2b", width=1)
                        c.create_text(px, py + 1, text="+", fill="#fff2f2", font=("Consolas", 8, "bold"))
                    else:
                        c.create_rectangle(px - 7, py - 7, px + 7, py + 7, fill="#ffd98a", outline="#7b5a21", width=1)
                        c.create_text(px, py + 1, text="A", fill="#432e05", font=("Consolas", 8, "bold"))

        effects = self.terraria_state.get("effects", [])
        if isinstance(effects, list):
            for fx in effects:
                if not isinstance(fx, dict):
                    continue
                fx_type = fx.get("type")
                if fx_type == "laser":
                    x1 = sx(float(fx.get("x1", 0.0)))
                    y1 = float(fx.get("y1", 0.0))
                    x2 = sx(float(fx.get("x2", 0.0)))
                    y2 = float(fx.get("y2", 0.0))
                    color = str(fx.get("color", "#7ef7ff"))
                    c.create_line(x1, y1, x2, y2, fill=color, width=4)
                    c.create_line(x1, y1 + 2, x2, y2 + 2, fill="#d8ffff", width=1)
                elif fx_type == "slash":
                    sx0 = sx(float(fx.get("x", 0.0)))
                    sy0 = float(fx.get("y", 0.0))
                    facing = int(fx.get("facing", 1))
                    color = str(fx.get("color", "#fff2b8"))
                    c.create_arc(
                        sx0 - 24,
                        sy0 - 22,
                        sx0 + 24,
                        sy0 + 22,
                        start=300 if facing > 0 else 120,
                        extent=95,
                        style="arc",
                        outline=color,
                        width=3,
                    )
                elif fx_type == "text":
                    tx = sx(float(fx.get("x", 0.0)))
                    ty = float(fx.get("y", 0.0))
                    c.create_text(
                        tx,
                        ty,
                        text=str(fx.get("text", "")),
                        fill=str(fx.get("color", "#ffffff")),
                        font=("Consolas", 9, "bold"),
                    )

        if self.hero and self.enemy:
            wave_number = int(self.terraria_state.get("wave_number", 1)) if self.terraria_state else 1
            c.create_text(
                310,
                18,
                text=f"Wave {wave_number} | HP {self.hero.name}: {self.hero.hp}/{self.hero.max_hp} | HP {self.enemy.name}: {self.enemy.hp}/{self.enemy.max_hp}",
                fill="#0f2138",
                font=("Consolas", 10, "bold"),
            )

        c.create_text(310, 232, text="A/D move | W/Space jump | F attack | H heal | 1=Laser 2=Spear 3=Sword", fill="#f5f3db", font=("Consolas", 9))

        # Simple minimap in the top-right corner.
        mini_w = 150
        mini_h = 44
        mini_x = width - mini_w - 10
        mini_y = 8
        world_w = float(self.terraria_state.get("world_width", 1600.0))
        scale = mini_w / max(1.0, world_w)

        c.create_rectangle(mini_x, mini_y, mini_x + mini_w, mini_y + mini_h, fill="#122032", outline="#c8d1e6", width=1)
        c.create_line(mini_x, mini_y + mini_h - 8, mini_x + mini_w, mini_y + mini_h - 8, fill="#6ea36f", width=2)

        platforms = self.terraria_state.get("platforms", [])
        if isinstance(platforms, list):
            for p1, p2, _py in platforms:
                p1x = mini_x + int(float(p1) * scale)
                p2x = mini_x + int(float(p2) * scale)
                c.create_line(p1x, mini_y + mini_h - 14, p2x, mini_y + mini_h - 14, fill="#9c7e54", width=2)

        hero_mx = mini_x + int(float(self.terraria_state.get("hero_x", 0.0)) * scale)
        enemy_mx = mini_x + int(float(self.terraria_state.get("enemy_x", 0.0)) * scale)
        c.create_oval(hero_mx - 2, mini_y + 11, hero_mx + 2, mini_y + 15, fill="#79c2ff", outline="")
        c.create_oval(enemy_mx - 2, mini_y + 11, enemy_mx + 2, mini_y + 15, fill="#ff8a8a", outline="")

        if isinstance(pickups, list):
            for item in pickups:
                if not isinstance(item, dict):
                    continue
                px = mini_x + int(float(item.get("x", 0.0)) * scale)
                color = "#ff7e8f" if str(item.get("kind", "health")) == "health" else "#ffd98a"
                c.create_rectangle(px - 1, mini_y + 18, px + 1, mini_y + 20, fill=color, outline=color)

        cam_x = float(self.terraria_state.get("camera_x", 0.0))
        viewport_world = width
        cam_w = max(8, int(viewport_world * scale))
        cam_left = mini_x + int(cam_x * scale)
        c.create_rectangle(cam_left, mini_y + 2, cam_left + cam_w, mini_y + mini_h - 2, outline="#f0b35a", width=1)

        if not self._is_duel_active() and self.hero and self.enemy:
            winner = self.hero.name if self.hero.hp > 0 else self.enemy.name
            c.create_rectangle(130, 84, 490, 150, fill="#0f1a2b", outline="#f0b35a", width=2)
            c.create_text(310, 104, text="BATTLE ENDED", fill="#f0b35a", font=("Bahnschrift SemiBold", 16))
            c.create_text(310, 128, text=f"Winner: {winner}", fill="#f2f1e8", font=("Consolas", 11, "bold"))

    def _terraria_loop(self):
        self.terraria_loop_after_id = None
        if not self._battle_window_exists() or not self.terraria_canvas:
            return

        self._terraria_try_spawn_next_wave()
        self._terraria_spawn_pickups()
        self._terraria_hero_movement()
        self._terraria_enemy_ai()
        self._terraria_apply_gravity()
        self._terraria_update_pickups()
        self._terraria_update_projectiles()
        self._terraria_update_effects()
        self._terraria_update_camera()
        self._terraria_draw_world()

        self.terraria_loop_after_id = self.root.after(33, self._terraria_loop)

    def _sync_battle_window_status(self):
        if not self._battle_window_exists():
            return
        if self.battle_weapon_var:
            self.battle_weapon_var.set(f"Weapon: {self.hero_weapon_kind.get()} (1/2/3)")
        if self.hero and self.enemy:
            enemy_type = str(self.terraria_state.get("enemy_archetype", "unknown")).upper() if self.terraria_state else "UNKNOWN"
            wave_number = int(self.terraria_state.get("wave_number", 1)) if self.terraria_state else 1
            self.battle_status_var.set(f"Wave {wave_number}: {self.hero.name} vs {self.enemy.name} [{enemy_type}]")
            self.battle_hero_hp_var.set(f"Hero HP: {self.hero.hp}/{self.hero.max_hp}")
            self.battle_enemy_hp_var.set(f"Enemy HP: {self.enemy.hp}/{self.enemy.max_hp}")
        else:
            self.battle_status_var.set("Waiting for both fighters")
            self.battle_hero_hp_var.set("Hero HP: -")
            self.battle_enemy_hp_var.set("Enemy HP: -")

        ammo = self.terraria_state.get("hero_ammo", {}) if self.terraria_state else {}
        blaster_ammo = int(ammo.get("Blaster", 0)) if isinstance(ammo, dict) else 0
        spear_ammo = int(ammo.get("Spear", 0)) if isinstance(ammo, dict) else 0
        wave_kills = int(self.terraria_state.get("wave_kills", 0)) if self.terraria_state else 0
        self.battle_round_var.set(f"Round: {self.round_count}")
        self.battle_stats_var.set(
            f"Dealt {self.hero_damage_dealt} | Taken {self.hero_damage_taken} | Heal {self.hero_total_heal} | Ammo B:{blaster_ammo} S:{spear_ammo} | Kills {wave_kills}"
        )

    def _end_fight_and_close(self):
        if not self._battle_window_exists():
            return

        if not messagebox.askyesno("End Fight", "End current fight and close battle interface?", parent=self.battle_window):
            return

        self._append_log("Fight ended manually by player.")
        self._add_history("Fight ended manually")
        self.last_action_var.set("Last action: Fight ended manually")

        # Exit duel mode cleanly so normal controls are available again.
        self.enemy = None
        if self.terraria_state:
            self.terraria_state["wave_spawn_pending"] = False

        self._terraria_stop_loop()
        self.terraria_keys.clear()

        if self.battle_window is not None and self.battle_window.winfo_exists():
            self.battle_window.destroy()
        self.battle_window = None
        self.battle_feed = None
        self.terraria_canvas = None

        self._update_status()
        self._refresh_focus_mode()

    def _battle_attack_action(self):
        if not self._battle_ready():
            return

        dmg = max(1, int(self.battle_attack_var.get()))
        weapon = self._current_weapon(dmg)
        self._animate_strike("hero")
        dealt = weapon.strike(self.hero, self.enemy)
        self.last_action_var.set(f"Last action: {self.hero.name} strikes with {weapon.name} for {dealt}")
        self._add_history(f"Battle attack: {self.hero.name} {dealt} via {weapon.name}")

        if self.enemy.hp > 0:
            counter = max(0, int(self.battle_enemy_attack_var.get()))
            if counter > 0:
                self._animate_strike("enemy")
                self.hero.take_damage(counter)
                self._append_log(f"Counter attack: {self.enemy.name} deals {counter}")
                self._add_history(f"Battle counter: {self.enemy.name} {counter}")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self._update_status()

    def _battle_heal_action(self):
        if not self._battle_ready():
            return

        heal = max(1, int(self.battle_heal_var.get()))
        self.hero.heal(heal)
        self.last_action_var.set(f"Last action: {self.hero.name} heals for {heal}")
        self._add_history(f"Battle heal: {self.hero.name} +{heal}")

        if self.enemy.hp > 0:
            pressure = max(0, int(self.battle_enemy_attack_var.get()))
            if pressure > 0:
                self._animate_strike("enemy")
                self.hero.take_damage(pressure)
                self._append_log(f"Pressure hit: {self.enemy.name} interrupts for {pressure}")
                self._add_history(f"Battle pressure: {self.enemy.name} {pressure}")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self._update_status()

    def _battle_manual_round_action(self):
        if not self._battle_ready():
            return

        hero_dmg = max(0, int(self.battle_attack_var.get()))
        if hero_dmg > 0:
            weapon = self._current_weapon(hero_dmg)
            self._animate_strike("hero")
            dealt = weapon.strike(self.hero, self.enemy)
            self.last_action_var.set(f"Last action: {self.hero.name} hits with {weapon.name} for {dealt}")
            self._add_history(f"Manual round: {self.hero.name} {dealt} via {weapon.name}")
        else:
            self._append_log("Manual round: hero attack skipped.")

        if self.enemy.hp > 0:
            enemy_dmg = max(0, int(self.battle_enemy_attack_var.get()))
            if enemy_dmg > 0:
                self._animate_strike("enemy")
                self.hero.take_damage(enemy_dmg)
                self.last_action_var.set(f"Last action: {self.enemy.name} hits for {enemy_dmg}")
                self._add_history(f"Manual round: {self.enemy.name} {enemy_dmg}")
            else:
                self._append_log("Manual round: enemy attack skipped.")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self._append_log("Manual round complete.")
        self._update_status()

    def _draw_hp_bar(self, canvas: tk.Canvas, hp: int, max_hp: int):
        canvas.delete("all")
        width = 320
        height = 20
        ratio = 0.0 if max_hp <= 0 else max(0.0, min(1.0, hp / max_hp))

        if ratio > 0.6:
            fill = "#6fcf87"
        elif ratio > 0.3:
            fill = "#f0b35a"
        else:
            fill = "#e16969"

        canvas.create_rectangle(0, 0, width, height, fill="#11192a", outline="#2f3f60")
        canvas.create_rectangle(0, 0, int(width * ratio), height, fill=fill, outline=fill)
        canvas.create_text(width - 6, height // 2, text=f"{int(ratio * 100)}%", fill="#c8d1e6", anchor="e", font=("Consolas", 9))

    def _flash_hit(self, canvas: tk.Canvas):
        canvas.configure(bg="#5d1e27")
        self.root.after(110, lambda: canvas.configure(bg=self.colors["bg"]))

    def _battle_ready(self) -> bool:
        if not self.hero or not self.enemy:
            messagebox.showwarning("Missing characters", "Create both a hero and an enemy first.")
            return False
        if self.hero.hp <= 0 or self.enemy.hp <= 0:
            messagebox.showinfo("Battle ended", "One fighter is down. Create a new hero or enemy to continue.")
            return False
        return True

    def _unwrap_combatant(self, fighter):
        current = fighter
        while hasattr(current, "_character"):
            current = current._character
        return current

    def _is_same_combatant(self, left, right) -> bool:
        if left is None or right is None:
            return False
        return self._unwrap_combatant(left) is self._unwrap_combatant(right)

    def _current_damage_mode(self):
        mode_name = self.hero_damage_mode.get()
        if mode_name == "Energy":
            return EnergyDamage()
        if mode_name == "Piercing":
            return PiercingDamage()
        return PhysicalDamage()

    def _current_weapon(self, base_damage: int):
        weapon_name = self.hero_weapon_kind.get()
        damage_mode = self._current_damage_mode()
        weapons = {
            "Sword": Sword,
            "Blaster": Blaster,
            "Spear": Spear,
        }
        weapon_cls = weapons.get(weapon_name, Sword)
        return weapon_cls(f"{weapon_name} of the Arena", base_damage, damage_mode)

    def _apply_decorator_damage(self, effect: str, value: int):
        if not self.hero:
            messagebox.showwarning("Missing characters", "Create a hero first.")
            return False

        if effect == "shield":
            self.hero = ShieldDecorator(self.hero, shield_value=value)
            self._hero_buff_state["shield"] = value
            self._append_log(f"Hero shield applied: -{value} incoming damage")
            self._add_history(f"Hero shield: {value}")
            self.last_action_var.set(f"Last action: Shield applied to {self.hero.name}")
        else:
            self.hero = BlessingDecorator(self.hero, healing_bonus=value)
            self._hero_buff_state["blessing"] = value
            self._append_log(f"Hero blessing applied: +{value} healing")
            self._add_history(f"Hero blessing: {value}")
            self.last_action_var.set(f"Last action: Blessing applied to {self.hero.name}")

        logger.log(f"Hero decorated with {effect}={value}", "INFO")
        self._update_status()
        return True

    def apply_hero_shield(self):
        if not self._battle_ready() and not self.hero:
            return
        shield_value = simpledialog.askinteger(
            "Hero Shield",
            "Shield value (damage reduction):",
            initialvalue=5,
            minvalue=1,
            parent=self.root,
        )
        if shield_value is None:
            return
        self._apply_decorator_damage("shield", shield_value)

    def apply_hero_blessing(self):
        if not self._battle_ready() and not self.hero:
            return
        blessing_value = simpledialog.askinteger(
            "Hero Blessing",
            "Healing bonus:",
            initialvalue=4,
            minvalue=1,
            parent=self.root,
        )
        if blessing_value is None:
            return
        self._apply_decorator_damage("blessing", blessing_value)

    def _announce_winner_if_needed(self, defeated: Character):
        if defeated.hp > 0:
            return
        marker = f"{self._unwrap_combatant(defeated).name}:{self.round_count}"
        if self._winner_shown_for == marker:
            return
        self._winner_shown_for = marker

        if self._is_same_combatant(defeated, self.enemy):
            winner = self.hero.name
        elif self._is_same_combatant(defeated, self.hero):
            winner = self.enemy.name
        else:
            winner = "Unknown"

        self.last_action_var.set(f"Last action: {winner} wins the duel")
        self._add_history(f"WIN: {winner} defeated {defeated.name}")
        try:
            self._save_history_snapshot(winner, defeated.name)
        except Exception as err:
            self._append_log(f"Could not save history file: {err}")
        self._show_victory_popup(winner, defeated.name)

    def _show_victory_popup(self, winner: str, defeated: str):
        dialog = tk.Toplevel(self.root)
        dialog.title("Victory")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=self.colors["bg"])
        dialog.geometry("460x320")
        dialog.resizable(False, False)

        frame = tk.Frame(dialog, bg=self.colors["panel"], bd=1, relief="solid", padx=18, pady=16)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        title = tk.Label(
            frame,
            text="Champion of the Arena",
            bg=self.colors["panel"],
            fg=self.colors["accent_alt"],
            font=("Bahnschrift SemiBold", 20),
        )
        title.pack(pady=(2, 8))

        winner_line = tk.Label(
            frame,
            text=f"{winner} claimed victory",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Bahnschrift", 13),
        )
        winner_line.pack()

        subtitle = tk.Label(
            frame,
            text=f"Defeated: {defeated}",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Calibri", 11, "italic"),
        )
        subtitle.pack(pady=(2, 10))

        stats = [
            f"Rounds played: {self.round_count}",
            f"Hero dealt: {self.hero_damage_dealt}",
            f"Hero taken: {self.hero_damage_taken}",
            f"Hero heals: {self.hero_total_heal}",
        ]
        for item in stats:
            tk.Label(
                frame,
                text=item,
                bg=self.colors["panel"],
                fg=self.colors["text"],
                anchor="w",
                font=("Consolas", 10),
            ).pack(fill="x")

        ribbon = tk.Canvas(frame, height=16, bg=self.colors["panel"], highlightthickness=0)
        ribbon.pack(fill="x", pady=(14, 10))
        ribbon.create_rectangle(0, 7, 412, 9, fill=self.colors["accent"], outline="")
        ribbon.create_oval(196, 2, 216, 14, fill=self.colors["accent_alt"], outline="")

        close_btn = tk.Button(
            frame,
            text="Continue",
            command=dialog.destroy,
            bg=self.colors["accent"],
            fg="#081018",
            activebackground="#86ece5",
            activeforeground="#081018",
            relief="flat",
            padx=16,
            pady=7,
            font=("Bahnschrift SemiBold", 10),
        )
        close_btn.pack(pady=(0, 2))
        close_btn.focus_set()

    def _on_damage(self, data):
        c = data["character"]
        amount = int(data.get("amount", 0))
        self._append_log(f"-> {c.name} takes {data['amount']} dmg. Remaining HP: {data['remaining_hp']}")
        if self._is_same_combatant(c, self.hero):
            self.hero_damage_taken += amount
        if self._is_same_combatant(c, self.enemy):
            self.hero_damage_dealt += amount
        self._update_stats()
        if self._is_same_combatant(c, self.hero):
            self._flash_hit(self.hero_hp_canvas)
            self._terraria_spawn_effect(
                {
                    "type": "text",
                    "x": float(self.terraria_state.get("hero_x", 0.0)),
                    "y": float(self.terraria_state.get("hero_y", 0.0)) - 56,
                    "ttl": 20,
                    "text": f"-{amount}",
                    "color": "#ffb7b7",
                }
            )
        elif self._is_same_combatant(c, self.enemy):
            self._flash_hit(self.enemy_hp_canvas)
            self._terraria_spawn_effect(
                {
                    "type": "text",
                    "x": float(self.terraria_state.get("enemy_x", 0.0)),
                    "y": float(self.terraria_state.get("enemy_y", 0.0)) - 58,
                    "ttl": 20,
                    "text": f"-{amount}",
                    "color": "#ffdcb2",
                }
            )
        self._update_status()

    def _on_death(self, data):
        c = data["character"]
        self._append_log(f"-> {c.name} has died.")

        if (
            self._battle_window_exists()
            and self.hero is not None
            and self.hero.hp > 0
            and self._is_same_combatant(c, self.enemy)
            and self.terraria_state
        ):
            self.terraria_state["wave_kills"] = int(self.terraria_state.get("wave_kills", 0)) + 1
            self._terraria_schedule_next_wave()
            self.last_action_var.set(f"Last action: {self.hero.name} cleared the wave")
            self._update_status()
            return

        self._update_status()
        self._announce_winner_if_needed(c)

    def _on_heal(self, data):
        c = data["character"]
        amount = int(data.get("amount", 0))
        self._append_log(f"-> {c.name} heals {data['amount']}. HP now: {data['new_hp']}")
        if self._is_same_combatant(c, self.hero):
            self.hero_total_heal += amount
            self._update_stats()
            self._animate_heal("hero")
            self._terraria_spawn_effect(
                {
                    "type": "text",
                    "x": float(self.terraria_state.get("hero_x", 0.0)),
                    "y": float(self.terraria_state.get("hero_y", 0.0)) - 56,
                    "ttl": 20,
                    "text": f"+{amount}",
                    "color": "#b8ffb6",
                }
            )
        elif self._is_same_combatant(c, self.enemy):
            self._animate_heal("enemy")
            self._terraria_spawn_effect(
                {
                    "type": "text",
                    "x": float(self.terraria_state.get("enemy_x", 0.0)),
                    "y": float(self.terraria_state.get("enemy_y", 0.0)) - 58,
                    "ttl": 20,
                    "text": f"+{amount}",
                    "color": "#b8ffd6",
                }
            )
        self._update_status()

    def _reset_match_progress(self, clear_feed: bool):
        self._winner_shown_for = None
        self.round_count = 0
        self.round_var.set("Round: 0")
        self.last_action_var.set("Last action: waiting...")
        self._reset_stats()
        self.history_list.delete(0, "end")
        self._add_history("Match reset")
        if clear_feed:
            self.feed.configure(state="normal")
            self.feed.delete("1.0", "end")
            self.feed.configure(state="disabled")
            if self.battle_feed and self._battle_window_exists():
                self.battle_feed.configure(state="normal")
                self.battle_feed.delete("1.0", "end")
                self.battle_feed.configure(state="disabled")
            self._append_log("Match reset. Feed cleared.")

    def create_hero(self):
        name = simpledialog.askstring("Create Hero", "Hero name:", parent=self.root)
        if name is None:
            return
        name = name.strip() or "Hero"

        hp = simpledialog.askinteger("Create Hero", "Max HP:", initialvalue=100, minvalue=1, parent=self.root)
        if hp is None:
            return

        self.hero = Character(name, hp)
        self._reset_match_progress(clear_feed=False)
        logger.log(f"Hero created: {self.hero.name} ({self.hero.hp}/{self.hero.max_hp})", "INFO")
        self._append_log(f"Hero created: {self.hero.name} ({self.hero.hp}/{self.hero.max_hp})")
        self._add_history(f"Spawn hero: {self.hero.name}")
        self.last_action_var.set(f"Last action: Hero {self.hero.name} entered the arena")
        self._update_status()
        self._ensure_battle_interface()

    def create_enemy(self):
        enemy_kind = self.enemy_type.get().lower()
        if enemy_kind == "goblin":
            self.enemy = GoblinFactory().create_enemy()
        elif enemy_kind == "orc":
            self.enemy = OrcFactory().create_enemy()
        elif enemy_kind == "troll":
            self.enemy = TrollFactory().create_enemy()
        else:
            self.enemy = RandomEnemyFactory().create_enemy()

        self._reset_match_progress(clear_feed=False)
        logger.log(f"Enemy created: {self.enemy.name} ({self.enemy.hp}/{self.enemy.max_hp})", "INFO")
        self._append_log(f"Enemy created: {self.enemy.name} ({self.enemy.hp}/{self.enemy.max_hp})")
        self._add_history(f"Spawn enemy: {self.enemy.name}")
        self.last_action_var.set(f"Last action: Enemy {self.enemy.name} appeared")
        self._update_status()
        self._ensure_battle_interface()

    def hero_attack(self):
        if not self._battle_ready():
            return

        dmg = simpledialog.askinteger(
            "Hero Attack",
            f"Damage by {self.hero.name}:",
            initialvalue=12,
            minvalue=1,
            parent=self.root,
        )
        if dmg is None:
            return

        weapon = self._current_weapon(dmg)
        self._animate_strike("hero")
        dealt = weapon.strike(self.hero, self.enemy)
        self.last_action_var.set(f"Last action: {self.hero.name} strikes with {weapon.name} for {dealt}")
        self._add_history(f"{self.hero.name} attack: {dealt} via {weapon.name}")

        if self.enemy.hp > 0:
            counter = random.randint(5, 14)
            self._animate_strike("enemy")
            self.hero.take_damage(counter)
            self._append_log(f"Counter attack: {self.enemy.name} deals {counter}")
            self._add_history(f"{self.enemy.name} counter: {counter}")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self._update_status()

    def hero_heal(self):
        if not self._battle_ready():
            return

        heal = simpledialog.askinteger(
            "Hero Heal",
            f"Heal amount for {self.hero.name}:",
            initialvalue=10,
            minvalue=1,
            parent=self.root,
        )
        if heal is None:
            return

        self.hero.heal(heal)
        self.last_action_var.set(f"Last action: {self.hero.name} heals for {heal}")
        self._add_history(f"{self.hero.name} heal: +{heal}")

        if self.enemy.hp > 0:
            pressure = random.randint(3, 11)
            self.hero.take_damage(pressure)
            self._append_log(f"Pressure hit: {self.enemy.name} interrupts for {pressure}")
            self._add_history(f"{self.enemy.name} pressure: {pressure}")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self._update_status()

    def fight_round(self):
        if not self._battle_ready():
            return

        hero_dmg = simpledialog.askinteger(
            "Fight Round",
            f"{self.hero.name} damage (0 to skip):",
            initialvalue=10,
            minvalue=0,
            parent=self.root,
        )
        if hero_dmg is None:
            return

        if hero_dmg > 0:
            weapon = self._current_weapon(hero_dmg)
            self._animate_strike("hero")
            dealt = weapon.strike(self.hero, self.enemy)
            self.last_action_var.set(f"Last action: {self.hero.name} hits with {weapon.name} for {dealt}")
            self._add_history(f"Round hit: {self.hero.name} {dealt} via {weapon.name}")
        else:
            self._append_log("Hero attack skipped.")

        if self.enemy.hp > 0:
            enemy_dmg = simpledialog.askinteger(
                "Fight Round",
                f"{self.enemy.name} damage (0 to skip):",
                initialvalue=8,
                minvalue=0,
                parent=self.root,
            )
            if enemy_dmg is None:
                return
            if enemy_dmg > 0:
                self._animate_strike("enemy")
                self.hero.take_damage(enemy_dmg)
                self.last_action_var.set(f"Last action: {self.enemy.name} hits for {enemy_dmg}")
                self._add_history(f"Round hit: {self.enemy.name} {enemy_dmg}")
            else:
                self._append_log("Enemy attack skipped.")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self._append_log("Round complete.")
        self._update_status()

    def quick_duel(self):
        if not self._battle_ready():
            return

        hero_dmg = random.randint(6, 20)
        weapon = self._current_weapon(hero_dmg)
        self._animate_strike("hero")
        dealt = weapon.strike(self.hero, self.enemy)
        self.last_action_var.set(f"Last action: {self.hero.name} quick-hit with {weapon.name} for {dealt}")
        self._add_history(f"Quick hit: {self.hero.name} {dealt} via {weapon.name}")

        if self.enemy.hp > 0:
            enemy_dmg = random.randint(5, 16)
            self._animate_strike("enemy")
            self.hero.take_damage(enemy_dmg)
            self.last_action_var.set(f"Last action: {self.enemy.name} retaliates for {enemy_dmg}")
            self._add_history(f"Retaliate: {self.enemy.name} {enemy_dmg}")

        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self._append_log("Quick duel complete.")
        self._update_status()

    def reset_match(self):
        if self.hero:
            self.hero.hp = self.hero.max_hp
        if self.enemy:
            self.enemy.hp = self.enemy.max_hp
        self._hero_buff_state = {"shield": 0, "blessing": 0}
        self._reset_match_progress(clear_feed=True)
        self._update_status()

    def show_logs(self):
        logs = logger.get_all_logs()
        messagebox.showinfo("Logger", logs or "No logs yet.")

    def create_faction_kit(self):
        faction = self.faction_var.get()
        if faction == "Sci-Fi":
            factory = SciFiFactionFactory()
        else:
            factory = MedievalFactionFactory()

        self.hero = factory.create_hero()
        self.enemy = factory.create_enemy()
        self._reset_match_progress(clear_feed=False)
        weapon = factory.create_weapon()

        self._append_log(f"Faction kit created: {faction}")
        self._append_log(f"Hero: {self.hero.name} ({self.hero.hp}/{self.hero.max_hp})")
        self._append_log(f"Enemy: {self.enemy.name} ({self.enemy.hp}/{self.enemy.max_hp})")
        self._append_log(f"Weapon: {weapon}")
        self._add_history(f"Faction loadout: {faction}")
        logger.log(f"Faction kit generated: {faction}", "INFO")
        self.last_action_var.set(f"Last action: {faction} faction kit deployed")
        self._update_status()
        self._ensure_battle_interface()

    def clone_prototype_enemy(self):
        key = self.prototype_var.get()
        try:
            self.enemy = self.prototype_registry.clone(key)
        except KeyError:
            self.enemy = self.prototype_registry.clone("goblin_elite")

        custom_name = simpledialog.askstring(
            "Clone Prototype",
            "Custom name for clone (optional):",
            parent=self.root,
        )
        if custom_name:
            self.enemy.name = custom_name.strip()

        self._reset_match_progress(clear_feed=False)
        logger.log(f"Prototype cloned: {self.enemy.name} ({self.enemy.hp}/{self.enemy.max_hp})", "INFO")
        self._append_log(f"Enemy cloned from prototype: {self.enemy.name}")
        self._add_history(f"Clone enemy: {self.enemy.name}")
        self.last_action_var.set(f"Last action: Prototype clone {self.enemy.name} ready")
        self._update_status()
        self._ensure_battle_interface()

    def demo_builder_integrity(self):
        builder = CharacterBuilder()

        configured = (
            builder.name("Demo Knight")
            .max_hp(140)
            .initial_hp(120)
            .description("Hero built with fluent Builder")
            .build()
        )
        default_after_reset = builder.build()

        output = (
            "Builder Demo\n\n"
            f"Configured character: {configured.name}, HP {configured.hp}/{configured.max_hp}, "
            f"description='{configured.description or '(empty)'}'\n"
            f"After reset character: {default_after_reset.name}, "
            f"HP {default_after_reset.hp}/{default_after_reset.max_hp}, "
            f"description='{default_after_reset.description or '(empty)'}'"
        )

        logger.log("Builder integrity demo executed", "INFO")
        self._append_log("Builder demo executed. See popup for details.")
        self._add_history("Builder demo run")
        messagebox.showinfo("Builder Demo", output)

    def demo_adapter_pattern(self):
        legacy_enemy = LegacyEnemy("Retro Drone", 80)
        self.enemy = LegacyEnemyAdapter(legacy_enemy)

        self._reset_match_progress(clear_feed=False)
        self._append_log("Adapter demo: legacy enemy wrapped to Character API")
        self._append_log(f"Adapted enemy: {self.enemy.name} ({self.enemy.hp}/{self.enemy.max_hp})")
        self._add_history(f"Adapter enemy: {self.enemy.name}")
        logger.log("Adapter demo executed", "INFO")
        self.last_action_var.set(f"Last action: Adapter created {self.enemy.name}")
        self._update_status()

    def demo_composite_pattern(self):
        alpha = Squad("Alpha Team")
        alpha.add(CharacterLeaf(Character("Knight", 120)))
        alpha.add(CharacterLeaf(Character("Archer", 85)))

        beta = Squad("Beta Team")
        beta.add(CharacterLeaf(Character("Orc Grunt", 95)))
        beta.add(CharacterLeaf(Character("Goblin Sneak", 55)))

        battalion = Squad("Alliance Battalion")
        battalion.add(alpha)
        battalion.add(beta)

        output = (
            "Composite Demo\n\n"
            f"{alpha.describe()}\n"
            f"{beta.describe()}\n\n"
            f"Combined: {battalion.describe()}"
        )

        self._append_log("Composite demo: squads aggregated recursively")
        self._add_history("Composite squad demo")
        logger.log("Composite demo executed", "INFO")
        messagebox.showinfo("Composite Demo", output)

    def demo_facade_pattern(self):
        facade = ArenaFacade()

        hero_name = simpledialog.askstring("Facade Demo", "Hero name:", initialvalue="Facade Hero", parent=self.root)
        if hero_name is None:
            return
        hero_name = hero_name.strip() or "Facade Hero"

        hero_hp = simpledialog.askinteger("Facade Demo", "Hero HP:", initialvalue=110, minvalue=1, parent=self.root)
        if hero_hp is None:
            return

        enemy_type = simpledialog.askstring(
            "Facade Demo",
            "Enemy type (goblin/orc/troll/random):",
            initialvalue="random",
            parent=self.root,
        )
        if enemy_type is None:
            return
        enemy_type = enemy_type.strip().lower() or "random"

        self.hero, self.enemy = facade.setup_duel(hero_name, hero_hp, enemy_type)
        self._reset_match_progress(clear_feed=False)

        hero_dmg = simpledialog.askinteger("Facade Demo", "Hero damage:", initialvalue=12, minvalue=0, parent=self.root)
        if hero_dmg is None:
            return
        enemy_dmg = simpledialog.askinteger("Facade Demo", "Enemy damage:", initialvalue=8, minvalue=0, parent=self.root)
        if enemy_dmg is None:
            return

        summary = facade.execute_round(hero_dmg, enemy_dmg)
        self.round_count += 1
        self.round_var.set(f"Round: {self.round_count}")
        self.last_action_var.set("Last action: Facade round executed")

        self._append_log(f"Facade duel: {summary['hero']} | {summary['enemy']}")
        self._add_history("Facade demo round")
        logger.log("Facade demo executed", "INFO")
        self._update_status()

    def demo_flyweight_pattern(self):
        goblin_one = self.flyweight_factory.create_enemy("goblin", "Goblin Scout A")
        goblin_two = self.flyweight_factory.create_enemy("goblin", "Goblin Scout B")
        orc_one = self.flyweight_factory.create_enemy("orc", "Orc Patrol")

        output = (
            "Flyweight Demo\n\n"
            f"Cache size: {self.flyweight_factory.cache_size()} ({', '.join(self.flyweight_factory.cached_keys())})\n"
            f"{goblin_one.name}: {goblin_one.hp}/{goblin_one.max_hp}\n"
            f"{goblin_two.name}: {goblin_two.hp}/{goblin_two.max_hp}\n"
            f"{orc_one.name}: {orc_one.hp}/{orc_one.max_hp}\n"
            "Shared state is reused through the flyweight factory."
        )

        self._append_log("Flyweight demo executed")
        self._add_history("Flyweight demo")
        logger.log("Flyweight demo executed", "INFO")
        messagebox.showinfo("Flyweight Demo", output)

    def demo_decorator_pattern(self):
        hero = Character("Decorated Hero", 100)
        shielded = ShieldDecorator(hero, shield_value=8)
        blessed = BlessingDecorator(shielded, healing_bonus=6)

        blessed.take_damage(30)
        blessed.heal(10)

        output = (
            "Decorator Demo\n\n"
            f"Final status: {blessed.name} {blessed.hp}/{blessed.max_hp}\n"
            f"Description: {blessed.description or '(empty)'}\n"
            "ShieldDecorator reduced incoming damage and BlessingDecorator increased healing."
        )

        self._append_log("Decorator demo executed")
        self._add_history("Decorator demo")
        logger.log("Decorator demo executed", "INFO")
        messagebox.showinfo("Decorator Demo", output)

    def demo_bridge_pattern(self):
        hero = Character("Bridge Knight", 120)
        dummy = Character("Bridge Dummy", 140)

        sword = Sword("Lionheart Sword", 18, PhysicalDamage())
        blaster = Blaster("Arc Pulse Blaster", 16, EnergyDamage())
        spear = Spear("Storm Spear", 14, PiercingDamage())

        sword.strike(hero, dummy)
        blaster.strike(hero, dummy)
        spear.strike(hero, dummy)

        output = (
            "Bridge Demo\n\n"
            f"{sword.describe()}\n"
            f"{blaster.describe()}\n"
            f"{spear.describe()}\n\n"
            f"Target after strikes: {dummy.name} {dummy.hp}/{dummy.max_hp}\n"
            "Weapon abstraction is decoupled from damage mode implementors."
        )

        self._append_log("Bridge demo executed")
        self._add_history("Bridge demo")
        logger.log("Bridge demo executed", "INFO")
        messagebox.showinfo("Bridge Demo", output)

    def demo_proxy_pattern(self):
        matches = self.history_proxy.latest_matches(3)
        if not matches:
            messagebox.showinfo("Proxy Demo", "No match history files found.")
            return

        lines = ["Proxy Demo", "", f"Cache loaded: {self.history_proxy.cache_loaded}"]
        for match in matches:
            lines.append(match.name)
            lines.append(self.history_proxy.preview(match, 5))
            lines.append("---")

        self._append_log("Proxy demo executed")
        self._add_history("Proxy demo")
        logger.log("Proxy demo executed", "INFO")
        messagebox.showinfo("Proxy Demo", "\n".join(lines))

    def demo_strategy_pattern(self):
        hero = Character("Strategist Hero", 120)
        dummy = Character("Training Dummy", 160)
        context = AttackContext(BalancedStrategy())

        lines = ["Strategy Demo", ""]
        for strategy in (BalancedStrategy(), AggressiveStrategy(), DefensiveStrategy(), ChaosStrategy()):
            context.set_strategy(strategy)
            dealt = context.attack(hero, dummy, 12)
            lines.append(f"{strategy.name.capitalize()}: {dealt} dmg -> Dummy {dummy.hp}/{dummy.max_hp}")

        self._append_log("Strategy demo executed")
        self._add_history("Strategy demo")
        logger.log("Strategy demo executed", "INFO")
        messagebox.showinfo("Strategy Demo", "\n".join(lines))

    def demo_observer_pattern(self):
        subject = Subject()
        feed = BattleFeedObserver()
        stats = BattleStatsObserver()

        subject.attach(feed)
        subject.attach(stats)

        subject.notify("hero_attack", {"damage": 11})
        subject.notify("hero_attack", {"damage": 14})
        subject.notify("enemy_counter", {"damage": 7})

        lines = ["Observer Demo", "", "Feed:"]
        lines.extend([f"- {entry}" for entry in feed.messages])
        lines.append("")
        lines.append(f"Stats: {stats.counters}")

        self._append_log("Observer demo executed")
        self._add_history("Observer demo")
        logger.log("Observer demo executed", "INFO")
        messagebox.showinfo("Observer Demo", "\n".join(lines))

    def demo_command_pattern(self):
        hero = Character("Command Hero", 100)
        enemy = Character("Command Enemy", 90)
        invoker = CommandInvoker()

        invoker.execute(DamageCommand(enemy, 18))
        invoker.execute(HealCommand(hero, 12))

        before = f"After execute: {hero.name}={hero.hp}/{hero.max_hp}, {enemy.name}={enemy.hp}/{enemy.max_hp}"

        invoker.undo_last()
        invoker.undo_last()
        after = f"After undo x2: {hero.name}={hero.hp}/{hero.max_hp}, {enemy.name}={enemy.hp}/{enemy.max_hp}"

        self._append_log("Command demo executed")
        self._add_history("Command demo")
        logger.log("Command demo executed", "INFO")
        messagebox.showinfo("Command Demo", f"Command Demo\n\n{before}\n{after}")

    def demo_memento_pattern(self):
        hero = Character("Memento Hero", 110)
        hero.description = "checkpoint"

        caretaker = MementoCaretaker()
        caretaker.push(CharacterStateOriginator.save(hero))

        hero.take_damage(35)
        hero.heal(6)
        current_state = f"Current: {hero.name} {hero.hp}/{hero.max_hp}"

        snapshot = caretaker.pop()
        if snapshot:
            CharacterStateOriginator.restore(hero, snapshot)
        restored_state = f"Restored: {hero.name} {hero.hp}/{hero.max_hp}"

        self._append_log("Memento demo executed")
        self._add_history("Memento demo")
        logger.log("Memento demo executed", "INFO")
        messagebox.showinfo("Memento Demo", f"Memento Demo\n\n{current_state}\n{restored_state}")

    def demo_iterator_pattern(self):
        history = CombatLogCollection()
        history.add("Hero spawned")
        history.add("Enemy spawned")
        history.add("Hero attacks for 12")
        history.add("Enemy counters for 8")

        lines = ["Iterator Demo", "", "Forward:"]
        lines.extend([f"- {item}" for item in history])
        lines.append("")
        lines.append("Reverse:")
        lines.extend([f"- {item}" for item in history.reversed_iter()])

        self._append_log("Iterator demo executed")
        self._add_history("Iterator demo")
        logger.log("Iterator demo executed", "INFO")
        messagebox.showinfo("Iterator Demo", "\n".join(lines))


def run_gui():
    root = tk.Tk()
    GoFArenaGUI(root)
    root.mainloop()
