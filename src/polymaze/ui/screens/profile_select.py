# profile_select.py
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from ...core import settings
from ...core.adventure import PROFILE_SLOTS, AdventureEngine, delete_profile
from ..controls import ENTER_KEYS, K_DELETE, K_ESCAPE
from ..gfx import rgba, touch_size, u
from ..widgets import IS_MOBILE, MenuButton, MenuScreen, themed_label

class ProfileSelectScreen(MenuScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._confirm: Popup = None

    def build_ui(self):
        self.clear_widgets()
        data_dir = self.app.user_data_dir
        root = AnchorLayout()
        col = BoxLayout(orientation="vertical", spacing=u(14), size_hint=(None, None), width=u(640))
        col.add_widget(themed_label("SELECT ADVENTURE PROFILE", 30, bold=True, size_hint_y=None, height=u(70)))

        buttons = []
        for i, slot in enumerate(PROFILE_SLOTS):
            info = AdventureEngine.get_profile_info(slot, data_dir)
            status = (f"LVL {info['level']} | EXP {info['exp']} | MAZES {info['total_mazes']}"
                      if info["exists"] else "EMPTY SLOT")
            row = BoxLayout(spacing=u(10), size_hint_y=None, height=touch_size(70))
            play = MenuButton(f"SLOT {slot}\n{status}", 18)
            play.bind(on_release=lambda *_, s=slot: self.play(s))
            row.add_widget(play); buttons.append(play)
            if info["exists"]:
                reset = MenuButton("RESET", 14, size_hint_x=None, width=u(110))
                reset.bind(on_release=lambda *_, s=slot: self.ask_reset(s))
                row.add_widget(reset)
            col.add_widget(row)

        back = MenuButton("BACK", 18, size_hint_y=None, height=touch_size(48))
        back.bind(on_release=lambda *_: self.on_back())
        col.add_widget(back); buttons.append(back)

        hint = "Tap a slot to play" if IS_MOBILE else "UP/DOWN: Select | ENTER: Play | DEL: Reset Slot | ESC: Back"
        col.add_widget(themed_label(hint, 12, settings.theme.WALL_COLOR, size_hint_y=None, height=u(36)))
        col.height = sum(c.height for c in col.children) + col.spacing * (len(col.children) - 1)
        root.add_widget(col)
        self.add_widget(root)
        self.set_focusables(buttons, self.selection)

    def play(self, slot: int):
        params = AdventureEngine(slot, self.app.user_data_dir).get_next_maze_params()
        self.app.start_game(mode="ADVENTURE", adventure_slot=slot, **params)

    def ask_reset(self, slot: int):
        if not AdventureEngine.get_profile_info(slot, self.app.user_data_dir)["exists"]: return
        t = settings.theme
        body = BoxLayout(orientation="vertical", spacing=u(12), padding=u(12))
        body.add_widget(themed_label(f"Erase all progress in slot {slot}?", 18))
        buttons = BoxLayout(spacing=u(12), size_hint_y=None, height=touch_size(48))
        yes, no = MenuButton("ERASE", 18), MenuButton("CANCEL", 18)
        buttons.add_widget(yes); buttons.add_widget(no); body.add_widget(buttons)
        popup = Popup(title="Reset profile", content=body, size_hint=(None, None), size=(u(460), touch_size(48) + u(190)),
                      auto_dismiss=True, separator_color=rgba(t.HIGHLIGHT_COLOR), background="",
                      background_color=rgba(t.BG_COLOR, 250), title_color=rgba(t.TEXT_COLOR))
        yes.bind(on_release=lambda *_: self._do_reset(slot))
        no.bind(on_release=lambda *_: popup.dismiss())
        popup.bind(on_dismiss=lambda *_: setattr(self, "_confirm", None))
        self._confirm, self._confirm_slot = popup, slot
        popup.open()

    def _do_reset(self, slot: int):
        delete_profile(slot, self.app.user_data_dir)
        if self._confirm: self._confirm.dismiss()
        self.build_ui()

    def on_key(self, key, codepoint, modifiers) -> bool:
        if self._confirm:
            if key in ENTER_KEYS: self._do_reset(self._confirm_slot)
            elif key == K_ESCAPE: self._confirm.dismiss()
            return True
        if key == K_DELETE and self.selection < len(PROFILE_SLOTS):
            self.ask_reset(PROFILE_SLOTS[self.selection]); return True
        return super().on_key(key, codepoint, modifiers)

    def on_back(self):
        self.app.go("menu")
