# game.py
"""Gameplay screen: owns the GameState and routes keyboard, touch and button input to it."""
import os
import traceback
from typing import Optional

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen

from ...core.game_state import GameState
from ..controls import (DIRECTION_KEYS, ENTER_KEYS, K_BACKSPACE, K_ESCAPE, K_TAB, ZOOM_IN_KEYS,
                        ZOOM_OUT_KEYS, ZOOM_RESET_KEYS, Gestures, key_char)
from ..gfx import u
from ..hud import Hud
from ..map_overlay import MapView
from ..maze_widget import MazeView
from ..widgets import themed_label

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state: Optional[GameState] = None
        self.show_map = False
        self._params = None
        self._tick_event = None
        self._held_keys = set()

        self.layout = FloatLayout()
        self.maze = MazeView()
        self.layout.add_widget(self.maze)
        self.map_view = MapView()
        self.hud = self._make_hud()
        self.layout.add_widget(self.hud)
        self.add_widget(self.layout)
        self.loading = themed_label("BUILDING MAZE...", 20, bold=True)

        self.gestures = Gestures(self.maze, on_hold=self._walk_toward, on_pinch=self._pinch,
                                 on_pinch_start=self._pinch_start, on_wheel=self._wheel)
        self.maze.bind(on_touch_down=lambda w, t: self.gestures.touch_down(t),
                       on_touch_move=lambda w, t: self.gestures.touch_move(t),
                       on_touch_up=lambda w, t: self.gestures.touch_up(t))

    def _make_hud(self) -> Hud:
        return Hud(actions={
            "map": self.toggle_map, "solve": self.toggle_solution, "solver": self.cycle_solver,
            "trace": self.toggle_trace, "fov": self.toggle_fov,
            "zoom_in": lambda: self.zoom(+1), "zoom_out": lambda: self.zoom(-1),
            "menu": self.leave, "continue": self.continue_after_win,
            "stairs_up": lambda: self.take_stairs("U"), "stairs_down": lambda: self.take_stairs("D"),
        })

    @property
    def app(self):
        return App.get_running_app()

    # --- Lifecycle ---
    def start(self, params: dict):
        """Queues a new maze; generation runs after the loading label has been drawn."""
        self._params = params
        self.state = None
        self._set_map(False)
        self.hud.hide_victory()
        if self.loading.parent is None: self.layout.add_widget(self.loading)
        Clock.schedule_once(self._build_state, 0.05)

    def _build_state(self, *_):
        try:
            self.state = GameState(data_dir=self.app.user_data_dir, **self._params)
        except Exception:
            traceback.print_exc()
            self.app.go("menu")
            return
        finally:
            if self.loading.parent: self.layout.remove_widget(self.loading)
        top_margin, bottom_margin = u(80), u(60)
        self.maze.set_state(self.state, top_margin, bottom_margin)
        self.hud.configure(self.state)
        self.hud.update(self.state, self.maze.camera.zoom)

    def on_enter(self, *args):
        Window.bind(on_key_up=self._on_key_up)
        self._tick_event = Clock.schedule_interval(self._tick, 1 / 60.0)

    def on_leave(self, *args):
        Window.unbind(on_key_up=self._on_key_up)
        if self._tick_event: self._tick_event.cancel(); self._tick_event = None
        self.gestures.reset(); self._held_keys.clear()

    def _tick(self, dt):
        s = self.state
        if not s: return
        try:
            if self.show_map:
                dx = sum(DIRECTION_KEYS[k][0] for k in self._held_keys)
                dy = sum(DIRECTION_KEYS[k][1] for k in self._held_keys)
                s.step_solver()
                self.map_view.tick(dx, dy)
            else:
                self.maze.tick()
            self.hud.update(s, self.maze.camera.zoom)
            if s.game_won: self.hud.show_victory(s)
        except Exception:
            traceback.print_exc()

    # --- Actions ---
    def _ready(self) -> bool:
        return bool(self.state) and not self.state.generating

    def toggle_map(self):
        if self._ready(): self._set_map(not self.show_map)

    def _set_map(self, shown: bool):
        self.show_map = shown
        if shown:
            self.state.toggle_map(True)
            if self.map_view.parent is None: self.layout.add_widget(self.map_view, index=1)  # above maze, below HUD
            self.map_view.set_state(self.state)
        elif self.map_view.parent:
            self.layout.remove_widget(self.map_view)

    def toggle_solution(self):
        if self._ready(): self.state.toggle_solution()

    def cycle_solver(self):
        if self._ready(): self.state.cycle_solver()

    def toggle_trace(self):
        if self.state: self.state.show_trace = not self.state.show_trace

    def toggle_fov(self):
        if self.state and self.state.mode == "CREATIVE": self.state.show_fov = not self.state.show_fov

    def zoom(self, direction: int):
        if not self.state: return
        if self.show_map: self.map_view.zoom_by(0.05 * direction)
        else: self.maze.zoom_by(0.1 * direction)

    def take_stairs(self, direction: str):
        if self._ready() and self.state.take_stairs(direction): self.maze.snap_player()

    def screenshot(self):
        path = Window.screenshot(name=os.path.join(self.app.user_data_dir, "maze_export.png"))  # Kivy appends a 4-digit counter
        if path: self.hud.toast(f"Saved {os.path.basename(path)}")

    def leave(self):
        """Back to the menu this run came from (ESC / MENU / Android back)."""
        if self.show_map: self._set_map(False); return
        mode = self.state.mode if self.state else (self._params or {}).get("mode", "CREATIVE")
        self.app.go("profiles" if mode == "ADVENTURE" else "creative")

    def abandon(self):
        """BACKSPACE: give up this run (adventure penalty applies) and return to the main menu."""
        if self.state: self.state.abandon()
        self.app.go("menu")

    def continue_after_win(self):
        s = self.state
        if not (s and s.game_won): return
        if s.mode == "ADVENTURE":
            self.start(dict(mode="ADVENTURE", adventure_slot=s.adventure_slot, **s.next_adventure_params()))
        else:
            self.app.go("creative")

    # --- Touch ---
    def _walk_toward(self, touch):
        """Tap/hold walks toward the finger; a swipe walks in the swipe direction."""
        if not self._ready() or self.show_map: return
        vec = Gestures.swipe_vector(touch)
        if vec is None:
            px, py = self.maze.player_screen_pos()
            vec = (touch.x - px, touch.y - py)
        self.state.move(vec)

    def _pinch_start(self):
        self._pinch_zoom = self.maze.camera.zoom

    def _pinch(self, factor):
        self.maze.camera.set_zoom(self._pinch_zoom * factor); self.maze.camera.apply()

    def _wheel(self, zoom_in: bool):
        self.zoom(+1 if zoom_in else -1)

    # --- Keyboard ---
    def _on_key_up(self, window, key, *args):
        self._held_keys.discard(key)

    def on_key(self, key: int, codepoint: str, modifiers) -> bool:
        s = self.state
        if key == K_ESCAPE:
            self.leave(); return True
        if not s or s.generating: return True
        if s.game_won:
            if key in ENTER_KEYS: self.continue_after_win()
            return True

        ch = key_char(key)
        if key in DIRECTION_KEYS: self._held_keys.add(key)
        if key == K_BACKSPACE: self.abandon(); return True
        if ch == "m": self.toggle_map(); return True
        if ch == "v": self.toggle_fov(); return True
        if ch == "x": self.toggle_solution(); return True
        if ch == "r": self.toggle_trace(); return True
        if key == K_TAB: self.cycle_solver(); return True
        if ch == "p": self.screenshot(); return True

        if self.show_map:
            if key in ZOOM_IN_KEYS: self.zoom(+1)
            elif key in ZOOM_OUT_KEYS: self.zoom(-1)
            elif key in ZOOM_RESET_KEYS: self.map_view.fit()
            return True  # arrows/WASD pan the map while held

        if key in ZOOM_IN_KEYS: self.zoom(+1)
        elif key in ZOOM_OUT_KEYS: self.zoom(-1)
        elif key in ZOOM_RESET_KEYS: self.maze.reset_zoom()
        elif key in DIRECTION_KEYS: s.move(DIRECTION_KEYS[key])
        elif ch in ("q", "u"): self.take_stairs("U")
        elif ch in ("e", "j"): self.take_stairs("D")
        return True

    def invalidate_theme(self):
        self.maze.invalidate_theme()
        self.map_view.invalidate_theme()
        self.layout.remove_widget(self.hud)
        self.hud = self._make_hud()
        self.layout.add_widget(self.hud)
        self.loading = themed_label("BUILDING MAZE...", 20, bold=True)
