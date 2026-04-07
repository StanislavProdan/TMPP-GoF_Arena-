"""Tkinter interface for GoF Arena.
"""

import random
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
        self.root.geometry("1080x640")
        self.root.minsize(960, 560)

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

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        self.root.configure(bg="#111522")
        style.configure("Header.TLabel", background="#111522", foreground="#f2f5ff", font=("Segoe UI", 18, "bold"))
        style.configure("SubHeader.TLabel", background="#111522", foreground="#96a2bf", font=("Segoe UI", 10))
        style.configure("Card.TLabelframe", background="#1a2236", foreground="#dfe6ff")
        style.configure("Card.TLabelframe.Label", background="#1a2236", foreground="#dfe6ff", font=("Segoe UI", 10, "bold"))
        style.configure("Card.TFrame", background="#1a2236")
        style.configure("ArenaName.TLabel", background="#1a2236", foreground="#f8fbff", font=("Segoe UI", 12, "bold"))
        style.configure("ArenaMeta.TLabel", background="#1a2236", foreground="#a8b4d6", font=("Segoe UI", 10))
        style.configure("Emphasis.TButton", font=("Segoe UI", 10, "bold"))

    def _build_layout(self):
        title = ttk.Label(
            self.root,
            text="GoF Arena",
            style="Header.TLabel",
            anchor="center",
        )
        title.pack(fill="x", padx=12, pady=(12, 8))

        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        left_shell = ttk.Frame(body, style="Card.TFrame")
        left_shell.pack(side="left", fill="y")

        self.left_canvas = tk.Canvas(
            left_shell,
            width=320,
            bg="#111522",
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
            bg="#111522",
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
        ttk.Label(controls, text="Enemy type:").pack(anchor="w", padx=8, pady=(4, 0))
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
        ttk.Label(controls, text="Hero Weapon:").pack(anchor="w", padx=8, pady=(0, 0))
        self.hero_weapon_kind = tk.StringVar(value="Sword")
        ttk.Combobox(
            controls,
            textvariable=self.hero_weapon_kind,
            values=["Sword", "Blaster", "Spear"],
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))

        ttk.Label(controls, text="Damage mode:").pack(anchor="w", padx=8, pady=(0, 0))
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
        ttk.Label(controls, text="Faction:").pack(anchor="w", padx=8, pady=(4, 0))
        ttk.Combobox(
            controls,
            textvariable=self.faction_var,
            values=["Medieval", "Sci-Fi"],
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))
        ttk.Button(controls, text="5) Create Faction Kit", command=self.create_faction_kit).pack(fill="x", padx=8, pady=(0, 6))

        self.prototype_var = tk.StringVar(value="goblin_elite")
        ttk.Label(controls, text="Prototype:").pack(anchor="w", padx=8, pady=(4, 0))
        ttk.Combobox(
            controls,
            textvariable=self.prototype_var,
            values=["goblin_elite", "orc_berserker", "troll_ancient"],
            state="readonly",
            width=24,
        ).pack(fill="x", padx=8, pady=(2, 4))
        ttk.Button(controls, text="6) Clone Prototype", command=self.clone_prototype_enemy).pack(fill="x", padx=8, pady=(0, 6))

        ttk.Button(controls, text="7) Builder Demo", command=self.demo_builder_integrity).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="8) Adapter Demo", command=self.demo_adapter_pattern).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="9) Composite Demo", command=self.demo_composite_pattern).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="10) Facade Demo", command=self.demo_facade_pattern).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="11) Flyweight Demo", command=self.demo_flyweight_pattern).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="12) Decorator Demo", command=self.demo_decorator_pattern).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="13) Bridge Demo", command=self.demo_bridge_pattern).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="14) Proxy Demo", command=self.demo_proxy_pattern).pack(fill="x", padx=8, pady=4)
        ttk.Button(controls, text="Reset Match", command=self.reset_match).pack(fill="x", padx=8, pady=4)

        ttk.Separator(controls, orient="horizontal").pack(fill="x", padx=8, pady=8)
        ttk.Button(controls, text="Exit", command=self.root.destroy).pack(fill="x", padx=8, pady=(0, 8))

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
            bg="#0f1528",
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
            bg="#111522",
            fg="#e7ecff",
            relief="flat",
            highlightthickness=0,
            selectbackground="#2d3958",
            activestyle="none",
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
            bg="#111522",
            fg="#e7ecff",
            insertbackground="#e7ecff",
            relief="flat",
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
        self.arena_canvas.create_rectangle(0, 0, 560, 115, fill="#121c3b", outline="", tags="bg")
        self.arena_canvas.create_rectangle(0, 115, 560, 190, fill="#1b2f27", outline="", tags="bg")
        self.arena_canvas.create_line(0, 115, 560, 115, fill="#2a3f72", width=2, tags="bg")
        for x in range(30, 560, 60):
            self.arena_canvas.create_line(x, 120, x - 16, 190, fill="#264635", width=1, tags="bg")

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

        self.arena_canvas.create_oval(x - 12, y - 48, x + 12, y - 24, fill=palette["head"], outline="", tags=("sprites", tag))
        self.arena_canvas.create_rectangle(x - 14, y - 24, x + 14, y + 16, fill=palette["body"], outline="", tags=("sprites", tag))
        self.arena_canvas.create_line(x, y + 16, x - 9, y + 42, fill=palette["accent"], width=3, tags=("sprites", tag))
        self.arena_canvas.create_line(x, y + 16, x + 9, y + 42, fill=palette["accent"], width=3, tags=("sprites", tag))
        self.arena_canvas.create_line(x - 11 * direction, y - 6, x - 25 * direction, y + 8, fill=palette["accent"], width=3, tags=("sprites", tag))
        self.arena_canvas.create_line(x + 11 * direction, y - 6, x + 30 * direction, y - 16, fill="#dfe7ff", width=3, tags=("sprites", tag))
        self.arena_canvas.create_text(x, y + 58, text=name, fill="#e8edff", font=("Segoe UI", 9, "bold"), tags=("sprites", tag))

    def _render_arena_sprites(self):
        self.arena_canvas.delete("sprites")

        hx, hy = self.hero_anchor
        ex, ey = self.enemy_anchor

        if self.hero:
            self._draw_character_sprite("hero_sprite", hx, hy, self.hero.name, is_enemy=False)
        else:
            self.arena_canvas.create_text(hx, hy + 12, text="No Hero", fill="#8ea1cb", font=("Segoe UI", 10), tags="sprites")

        if self.enemy:
            self._draw_character_sprite("enemy_sprite", ex, ey, self.enemy.name, is_enemy=True)
        else:
            self.arena_canvas.create_text(ex, ey + 12, text="No Enemy", fill="#8ea1cb", font=("Segoe UI", 10), tags="sprites")

    def _animate_strike(self, attacker: str):
        if not self.hero or not self.enemy:
            return

        if attacker == "hero":
            tag = "hero_sprite"
            direction = 1
            target_x, target_y = self.enemy_anchor
            slash_color = "#9bd2ff"
        else:
            tag = "enemy_sprite"
            direction = -1
            target_x, target_y = self.hero_anchor
            slash_color = "#ffb3b3"

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
        ring = self.arena_canvas.create_oval(x - 18, y - 30, x + 18, y + 6, outline="#69ff9d", width=2, tags="anim")
        plus = self.arena_canvas.create_text(x, y - 12, text="+", fill="#a1ffc4", font=("Segoe UI", 14, "bold"), tags="anim")
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
        self.feed.configure(state="normal")
        self.feed.insert("end", f"{message}\n")
        self.feed.see("end")
        self.feed.configure(state="disabled")

    def _add_history(self, message: str):
        self.history_list.insert("end", message)
        # Keep only last 5 important actions.
        while self.history_list.size() > 5:
            self.history_list.delete(0)
        self.history_list.see("end")

    def _history_items(self):
        return list(self.history_list.get(0, "end"))

    def _update_stats(self):
        self.stats_dealt_var.set(f"Hero dealt: {self.hero_damage_dealt}")
        self.stats_taken_var.set(f"Hero taken: {self.hero_damage_taken}")
        self.stats_heal_var.set(f"Hero heals: {self.hero_total_heal}")

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

    def _draw_hp_bar(self, canvas: tk.Canvas, hp: int, max_hp: int):
        canvas.delete("all")
        width = 320
        height = 20
        ratio = 0.0 if max_hp <= 0 else max(0.0, min(1.0, hp / max_hp))

        if ratio > 0.6:
            fill = "#3ecf6d"
        elif ratio > 0.3:
            fill = "#f0bb3c"
        else:
            fill = "#e05252"

        canvas.create_rectangle(0, 0, width, height, fill="#232d45", outline="#2d3958")
        canvas.create_rectangle(0, 0, int(width * ratio), height, fill=fill, outline=fill)

    def _flash_hit(self, canvas: tk.Canvas):
        canvas.configure(bg="#6b1f2b")
        self.root.after(110, lambda: canvas.configure(bg="#111522"))

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
        messagebox.showinfo("Victory", f"{winner} wins!\n\n{defeated.name} has been defeated.")

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
        elif self._is_same_combatant(c, self.enemy):
            self._flash_hit(self.enemy_hp_canvas)
        self._update_status()

    def _on_death(self, data):
        c = data["character"]
        self._append_log(f"-> {c.name} has died.")
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
        elif self._is_same_combatant(c, self.enemy):
            self._animate_heal("enemy")
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


def run_gui():
    root = tk.Tk()
    GoFArenaGUI(root)
    root.mainloop()
