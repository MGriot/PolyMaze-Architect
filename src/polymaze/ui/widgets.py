# widgets.py
"""Themed widgets and a keyboard-navigable menu screen base."""
from typing import List

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.utils import platform

from ..core import settings
from .controls import ENTER_KEYS, K_DOWN, K_ESCAPE, K_UP
from .gfx import rgba, u

IS_MOBILE = platform in ("android", "ios")

def themed_label(text: str, size: float, color=None, bold: bool = False, **kwargs) -> Label:
    color = color or settings.theme.TEXT_COLOR
    return Label(text=text, font_size=round(u(size)), bold=bold, color=rgba(color), **kwargs)

class MenuButton(Button):
    """Flat button that shows keyboard focus with the theme highlight color."""
    def __init__(self, text: str = "", font_size: float = 20, **kwargs):
        super().__init__(text=text, font_size=round(u(font_size)), background_normal="",
                         background_down="", halign="center", valign="middle", **kwargs)
        self.bind(size=self._wrap)
        self.set_focus(False)

    def _wrap(self, *_):
        self.text_size = (self.width - u(12), None)

    def set_focus(self, focused: bool):
        t = settings.theme
        self.background_color = rgba(t.HIGHLIGHT_COLOR, 60) if focused else rgba(t.WALL_COLOR, 28)
        self.color = rgba(t.HIGHLIGHT_COLOR if focused else t.TEXT_COLOR)
        self.bold = focused

def paint_background(widget, color, alpha: int = 255):
    with widget.canvas.before:
        c = Color(*rgba(color, alpha))
        r = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(r, "pos", widget.pos), size=lambda *_: setattr(r, "size", widget.size))
    return c

class MenuScreen(Screen):
    """Screen whose ``focusables`` can be walked with UP/DOWN and activated with ENTER."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focusables: List[MenuButton] = []
        self.selection = 0

    @property
    def app(self):
        return App.get_running_app()

    def build_ui(self):
        """Clears and rebuilds the widget tree (called on enter, resize and theme change)."""
        raise NotImplementedError

    def on_pre_enter(self, *args):
        self.build_ui()

    def set_focusables(self, buttons: List[MenuButton], selection: int = 0):
        self.focusables = buttons
        self.selection = min(selection, len(buttons) - 1)
        self._show_focus()

    def _show_focus(self):
        for i, b in enumerate(self.focusables): b.set_focus(i == self.selection)

    def on_key(self, key: int, codepoint: str, modifiers) -> bool:
        if not self.focusables: return False
        if key == K_UP: self.selection = (self.selection - 1) % len(self.focusables); self._show_focus(); return True
        if key == K_DOWN: self.selection = (self.selection + 1) % len(self.focusables); self._show_focus(); return True
        if key in ENTER_KEYS: self.focusables[self.selection].trigger_action(duration=0); return True
        if key == K_ESCAPE: self.on_back(); return True
        return False

    def on_back(self):
        pass
