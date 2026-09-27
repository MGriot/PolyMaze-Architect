# app.py
"""Kivy application: window setup, screen routing, global keyboard dispatch."""
import os

from kivy.config import Config
from kivy.utils import platform

from ..core import settings

# Must run before kivy.core.window is imported anywhere.
if platform not in ("android", "ios"):
    Config.set("graphics", "width", str(settings.DEFAULT_WINDOW_SIZE[0]))
    Config.set("graphics", "height", str(settings.DEFAULT_WINDOW_SIZE[1]))
    Config.set("graphics", "minimum_width", "800")
    Config.set("graphics", "minimum_height", "500")
Config.set("kivy", "exit_on_escape", "0")                   # ESC / Android back are handled per screen
Config.set("input", "mouse", "mouse,multitouch_on_demand")  # no red multitouch dots on right-click

from kivy.app import App  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.uix.screenmanager import NoTransition, ScreenManager  # noqa: E402

from ..core.adventure import migrate_legacy_profiles  # noqa: E402
from .gfx import rgba  # noqa: E402
from .screens.creative_menu import CreativeMenuScreen  # noqa: E402
from .screens.game import GameScreen  # noqa: E402
from .screens.main_menu import MainMenuScreen  # noqa: E402
from .screens.profile_select import ProfileSelectScreen  # noqa: E402

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

class PolyMazeApp(App):
    title = settings.APP_TITLE

    def build(self):
        icon = os.path.join(ASSETS_DIR, "icon.png")
        if os.path.exists(icon): self.icon = icon
        migrate_legacy_profiles(self.user_data_dir)
        Window.clearcolor = rgba(settings.theme.BG_COLOR)

        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(MainMenuScreen(name="menu"))
        self.sm.add_widget(ProfileSelectScreen(name="profiles"))
        self.sm.add_widget(CreativeMenuScreen(name="creative"))
        self.sm.add_widget(GameScreen(name="game"))

        Window.bind(on_key_down=self._on_key_down, on_resize=self._on_resize)
        return self.sm

    def go(self, screen: str):
        self.sm.current = screen

    def start_game(self, **params):
        self.sm.get_screen("game").start(params)
        self.sm.current = "game"

    def toggle_theme(self):
        settings.theme.toggle()
        Window.clearcolor = rgba(settings.theme.BG_COLOR)
        self.sm.get_screen("game").invalidate_theme()

    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        handler = getattr(self.sm.current_screen, "on_key", None)
        return bool(handler and handler(key, codepoint, modifiers))

    def _on_resize(self, *_):
        screen = self.sm.current_screen
        if hasattr(screen, "build_ui"): screen.build_ui()

def run():
    PolyMazeApp().run()
