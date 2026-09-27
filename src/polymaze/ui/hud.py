# hud.py
"""In-game overlay: status bar, floor minimap, touch buttons, stair prompt and victory panel."""
from typing import Callable, Dict

from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget

from ..core import settings
from ..core.game_state import GameState
from .gfx import rgba, touch_size, u
from .widgets import IS_MOBILE, MenuButton, paint_background, themed_label

KEY_HINTS = "WASD: Move | Q/E: Stairs | X: Sol | TAB: Solver | R: Trace | V: FOV | +/-: Zoom | 0: Reset | M: Map | P: Shot | ESC: Menu"

class FloorMinimap(Widget):
    """Stack of floor boxes; the current floor is highlighted."""
    def draw(self, levels: int, current: int):
        self.canvas.clear()
        if levels <= 1: return
        t = settings.theme
        box_h, gap = u(20), u(5)
        self.size = (u(60), levels * (box_h + gap) + u(15))
        with self.canvas:
            Color(*rgba(t.BG_COLOR, 120)); Rectangle(pos=self.pos, size=self.size)
            for i in range(levels):
                Color(*(rgba(t.HIGHLIGHT_COLOR) if i == current else rgba((128, 128, 128, 150))))
                Rectangle(pos=(self.x + u(10), self.y + u(10) + i * (box_h + gap)), size=(u(40), box_h))

class Hud(FloatLayout):
    def __init__(self, actions: Dict[str, Callable], **kwargs):
        super().__init__(**kwargs)
        self.actions = actions
        t = settings.theme
        bar_h = u(40)

        top = BoxLayout(size_hint=(1, None), height=bar_h, pos_hint={"top": 1}, padding=(u(20), 0))
        paint_background(top, t.BG_COLOR, 180)
        self.title = themed_label("", 13, bold=True, halign="left", valign="middle")
        self.stats = themed_label("", 13, t.HIGHLIGHT_COLOR, bold=True, halign="right", valign="middle")
        for lbl in (self.title, self.stats):
            lbl.bind(size=lambda l, *_: setattr(l, "text_size", l.size))
            top.add_widget(lbl)
        self.add_widget(top)

        self.hints = None
        if not IS_MOBILE:
            self.hints = themed_label(KEY_HINTS, 10, t.WALL_COLOR, halign="left", valign="middle",
                                      size_hint=(None, None), height=u(24))
            self.hints.bind(size=lambda l, *_: setattr(l, "text_size", (l.width - u(40), l.height)))
            self.add_widget(self.hints)
        self._bar_h = bar_h

        # Right-hand tool column (tap targets for touch; also clickable on desktop)
        self.tools = BoxLayout(orientation="vertical", spacing=u(6), size_hint=(None, None), width=max(u(96), touch_size(40) * 1.9),
                               pos_hint={"right": 0.99, "center_y": 0.5})
        self.tool_buttons: Dict[str, MenuButton] = {}
        for key, label in (("map", "MAP"), ("solve", "SOLVE"), ("solver", "BFS"), ("trace", "TRACE"),
                           ("fov", "FOV"), ("zoom_in", "ZOOM +"), ("zoom_out", "ZOOM -"), ("menu", "MENU")):
            b = MenuButton(label, 13, size_hint_y=None, height=touch_size(40))
            b.bind(on_release=lambda *_, k=key: self.actions[k]())
            self.tool_buttons[key] = b
        self._layout_tools(show_fov=False)
        self.add_widget(self.tools)

        self.minimap = FloorMinimap(size_hint=(None, None))
        self.add_widget(self.minimap)
        self.bind(pos=self._reposition, size=self._reposition)

        # Bottom centre: generation status, stair buttons, toast
        self.status = themed_label("GENERATING...", 16, size_hint=(1, None), height=u(40), pos_hint={"x": 0, "y": 0.02})
        self.add_widget(self.status)
        self.stairs = BoxLayout(spacing=u(12), size_hint=(None, None), height=touch_size(48), pos_hint={"center_x": 0.5, "y": 0.09})
        self.stair_up = MenuButton("STAIRS UP" if IS_MOBILE else "STAIRS UP [Q]", 16)
        self.stair_down = MenuButton("STAIRS DOWN" if IS_MOBILE else "STAIRS DOWN [E]", 16)
        self.stair_up.bind(on_release=lambda *_: self.actions["stairs_up"]())
        self.stair_down.bind(on_release=lambda *_: self.actions["stairs_down"]())
        self._stair_key = None

        self.victory = None

    def _layout_tools(self, show_fov: bool):
        self.tools.clear_widgets()
        for key, b in self.tool_buttons.items():
            if key == "fov" and not show_fov: continue
            self.tools.add_widget(b)
        n = len(self.tools.children)
        self.tools.height = n * touch_size(40) + (n - 1) * self.tools.spacing

    def configure(self, state: GameState):
        self._layout_tools(show_fov=state.mode == "CREATIVE")
        self.hide_victory()

    def _reposition(self, *_):
        below_bar = self.top - self._bar_h
        if self.hints:
            self.hints.width = self.width
            self.hints.pos = (self.x, below_bar - u(4) - self.hints.height)
            below_bar = self.hints.y
        self.minimap.x = self.x + u(12)
        self.minimap.top = below_bar - u(12)

    def update(self, state: GameState, zoom: float):
        star_str = f" | STARS: {len(state.stars_collected)}/{len(state.stars)}" if state.collect_stars else ""
        self.title.text = f"{state.gen_name.upper()} ARCHITECT | Floor {state.current_level+1}/{state.grid.levels}{star_str}"
        self.stats.text = f"STEPS: {state.step_count} | TIME: {state.elapsed()}s | Zoom: {zoom:.1f}x"
        self.minimap.draw(state.grid.levels, state.current_level)
        self._reposition()
        self.tool_buttons["solver"].text = state.solver_name
        self.tool_buttons["solve"].set_focus(state.show_solution)
        self.tool_buttons["trace"].set_focus(state.show_trace)
        self.tool_buttons["fov"].set_focus(state.show_fov)
        self.tools.opacity = 0 if state.generating else 1
        self.tools.disabled = state.generating

        if state.generating:
            if self.status.parent is None: self.add_widget(self.status)
            self.status.text = "GENERATING..."
        elif self.status.text == "GENERATING...":
            self.status.text = ""
        self._update_stairs(state)

    def _update_stairs(self, state: GameState):
        dirs = tuple(sorted({d for _, d in state.stair_options})) if not (state.generating or state.game_won) else ()
        if dirs == self._stair_key: return
        self._stair_key = dirs
        self.stairs.clear_widgets()
        if self.stairs.parent: self.remove_widget(self.stairs)
        if not dirs: return
        if "U" in dirs: self.stairs.add_widget(self.stair_up)
        if "D" in dirs: self.stairs.add_widget(self.stair_down)
        self.stairs.width = len(dirs) * u(230) + (len(dirs) - 1) * self.stairs.spacing
        self.add_widget(self.stairs)

    def toast(self, text: str):
        self.status.text = text

    # --- Victory ---
    def show_victory(self, state: GameState):
        if self.victory: return
        t = settings.theme
        panel = BoxLayout(orientation="vertical", spacing=u(8), padding=u(30), size_hint=(1, 1))
        paint_background(panel, t.BG_COLOR, 230)
        panel.add_widget(Widget())
        panel.add_widget(themed_label("CONGRATULATIONS!", 36, t.HIGHLIGHT_COLOR, bold=True, size_hint_y=None, height=u(60)))
        lines = [f"Time: {int(state.solve_duration)}s", f"Steps: {state.step_count}", f"Cells Visited: {len(state.cells_visited)}"]
        if state.collect_stars: lines.append(f"Stars Collected: {len(state.stars_collected)}/{len(state.stars)}")
        cont = "PLAY AGAIN"
        if state.mode == "ADVENTURE" and state.adventure_result:
            r = state.adventure_result
            lines += [f"ADVENTURE LVL: {r['level']}", f"TOTAL EXP: {r['exp']}", f"MAZES SOLVED: {r['total_mazes']}"]
            cont = "NEXT CHALLENGE"
        for line in lines:
            panel.add_widget(themed_label(line, 16, size_hint_y=None, height=u(30)))
        buttons = BoxLayout(spacing=u(12), size_hint=(None, None), height=touch_size(52), width=u(520), pos_hint={"center_x": 0.5})
        go = MenuButton(cont if IS_MOBILE else f"{cont} [ENTER]", 18)
        menu = MenuButton("MENU", 18, size_hint_x=0.4)
        go.set_focus(True)
        go.bind(on_release=lambda *_: self.actions["continue"]())
        menu.bind(on_release=lambda *_: self.actions["menu"]())
        buttons.add_widget(go); buttons.add_widget(menu)
        panel.add_widget(Widget(size_hint_y=None, height=u(10)))
        panel.add_widget(buttons)
        panel.add_widget(Widget())
        self.victory = panel
        self.add_widget(panel)

    def hide_victory(self):
        if self.victory:
            self.remove_widget(self.victory)
            self.victory = None
