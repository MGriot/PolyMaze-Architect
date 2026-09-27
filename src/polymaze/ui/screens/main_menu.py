# main_menu.py
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout

from ...core import settings
from ..gfx import touch_size, u
from ..widgets import IS_MOBILE, MenuButton, MenuScreen, themed_label

class MainMenuScreen(MenuScreen):
    def build_ui(self):
        self.clear_widgets()
        root = AnchorLayout()
        col = BoxLayout(orientation="vertical", spacing=u(16), size_hint=(None, None), width=u(520))
        col.add_widget(themed_label("POLY MAZE ARCHITECT", 40, bold=True, size_hint_y=None, height=u(90)))

        entries = [("ADVENTURE", lambda *_: self.app.go("profiles")),
                   ("CREATIVE / TRAINING", lambda *_: self.app.go("creative"))]
        if not IS_MOBILE: entries.append(("QUIT", lambda *_: self.app.stop()))
        buttons = []
        for text, action in entries:
            b = MenuButton(text, 24, size_hint_y=None, height=touch_size(56))
            b.bind(on_release=action)
            col.add_widget(b); buttons.append(b)

        hint = "Tap to select" if IS_MOBILE else "UP/DOWN: Select | ENTER: Confirm | ESC: Quit"
        col.add_widget(themed_label(hint, 12, settings.theme.WALL_COLOR, size_hint_y=None, height=u(40)))
        col.height = sum(c.height for c in col.children) + col.spacing * (len(col.children) - 1)
        root.add_widget(col)
        self.add_widget(root)
        self.set_focusables(buttons, self.selection)

    def on_back(self):
        self.app.stop()
