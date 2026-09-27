# creative_menu.py
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

from ...core import settings
from ...core.catalog import CELL_TYPES, GENERATORS, MAX_LEVELS, SHAPES, SIZES
from ..controls import key_char
from ..gfx import touch_size, u
from ..widgets import IS_MOBILE, MenuButton, MenuScreen, themed_label

class CreativeMenuScreen(MenuScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cell_idx, self.shape_idx, self.size_idx, self.gen_idx = 0, 0, 1, 0
        self.animate, self.multi_path, self.levels = True, False, 1
        self.randomize_start_end, self.show_trace = True, True
        self.explorative_map, self.collect_stars = False, False
        # (key, label, value getter, action)
        self.options = [
            ("g", "Cell Shape", lambda: CELL_TYPES[self.cell_idx][0], lambda: self._cycle("cell_idx", len(CELL_TYPES))),
            ("f", "Maze Form", lambda: SHAPES[self.shape_idx].upper(), lambda: self._cycle("shape_idx", len(SHAPES))),
            ("z", "Size", lambda: SIZES[self.size_idx][0], lambda: self._cycle("size_idx", len(SIZES))),
            ("a", "Algorithm", lambda: GENERATORS[self.gen_idx][0], lambda: self._cycle("gen_idx", len(GENERATORS))),
            ("v", "Animation", lambda: "ENABLED" if self.animate else "DISABLED", lambda: self._toggle("animate")),
            ("m", "Multi-Path", lambda: self._on_off(self.multi_path), lambda: self._toggle("multi_path")),
            ("l", "3D Levels", lambda: str(self.levels), lambda: setattr(self, "levels", self.levels % MAX_LEVELS + 1)),
            ("e", "Random Start/End", lambda: self._on_off(self.randomize_start_end), lambda: self._toggle("randomize_start_end")),
            ("r", "Show Trace", lambda: self._on_off(self.show_trace), lambda: self._toggle("show_trace")),
            ("x", "Explorative Map", lambda: self._on_off(self.explorative_map), lambda: self._toggle("explorative_map")),
            ("s", "Collect Stars", lambda: self._on_off(self.collect_stars), lambda: self._toggle("collect_stars")),
            ("t", "Theme", lambda: settings.theme.name.upper(), self.app_toggle_theme),
        ]
        self.selection = len(self.options)  # START

    @staticmethod
    def _on_off(v): return "ON" if v else "OFF"
    def _cycle(self, attr, n): setattr(self, attr, (getattr(self, attr) + 1) % n)
    def _toggle(self, attr): setattr(self, attr, not getattr(self, attr))

    def app_toggle_theme(self):
        self.app.toggle_theme()

    def build_ui(self):
        self.clear_widgets()
        root = AnchorLayout()
        col = BoxLayout(orientation="vertical", spacing=u(10), size_hint=(None, None), width=min(u(980), Window.width - u(32)))
        col.add_widget(themed_label("CREATIVE / TRAINING MODE", 30, bold=True, size_hint_y=None, height=u(60)))

        row_h = touch_size(40)
        grid = GridLayout(cols=2, spacing=u(8), size_hint_y=None)
        grid.height = (row_h + u(8)) * ((len(self.options) + 1) // 2)
        self._option_buttons = []
        for key, label, getter, action in self.options:
            text = f"{label}: {getter()}" if IS_MOBILE else f"[{key.upper()}] {label}: {getter()}"
            b = MenuButton(text, 16, size_hint_y=None, height=row_h)
            b.bind(on_release=lambda *_, a=action: self._activate(a))
            grid.add_widget(b); self._option_buttons.append(b)
        col.add_widget(grid)

        actions = BoxLayout(spacing=u(12), size_hint_y=None, height=touch_size(52))
        start, back = MenuButton("START", 22), MenuButton("BACK", 18, size_hint_x=0.4)
        start.bind(on_release=lambda *_: self.start_game())
        back.bind(on_release=lambda *_: self.on_back())
        actions.add_widget(start); actions.add_widget(back)
        col.add_widget(actions)

        if not IS_MOBILE:
            col.add_widget(themed_label("Letter keys change options | ENTER: Start | ESC: Back", 12,
                                        settings.theme.WALL_COLOR, size_hint_y=None, height=u(30)))
        col.height = sum(c.height for c in col.children) + col.spacing * (len(col.children) - 1)
        root.add_widget(col)
        self.add_widget(root)
        self.set_focusables(self._option_buttons + [start, back], self.selection)

    def _activate(self, action):
        action()
        self.build_ui()

    def on_key(self, key, codepoint, modifiers) -> bool:
        ch = key_char(key)
        for k, _, _, action in self.options:
            if ch == k:
                self.selection = len(self.options)  # keep focus on START like the original menu
                self._activate(action); return True
        return super().on_key(key, codepoint, modifiers)

    def start_game(self):
        _, GridClass = CELL_TYPES[self.cell_idx]
        _, rows, cols = SIZES[self.size_idx]
        gen_name, GenClass = GENERATORS[self.gen_idx]
        self.app.start_game(GridClass=GridClass, shape=SHAPES[self.shape_idx], rows=rows, cols=cols, levels=self.levels,
                            generator=GenClass(), gen_name=gen_name, animate=self.animate,
                            braid_pct=0.5 if self.multi_path else 0.0, show_trace=self.show_trace,
                            randomize_start_end=self.randomize_start_end, mode="CREATIVE",
                            explorative_map=self.explorative_map, collect_stars=self.collect_stars)

    def on_back(self):
        self.app.go("menu")
