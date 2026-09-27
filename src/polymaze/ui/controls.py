# controls.py
"""Input handling shared by the game and map views: key codes and touch gestures."""
import math
from typing import Callable, Dict, Optional, Tuple

from kivy.clock import Clock
from kivy.metrics import dp

# Kivy keycodes (SDL2)
K_BACKSPACE, K_TAB, K_ENTER, K_ESCAPE, K_DELETE = 8, 9, 13, 27, 127
K_UP, K_DOWN, K_RIGHT, K_LEFT = 273, 274, 275, 276
K_NUMPAD0, K_NUMPAD_MINUS, K_NUMPAD_PLUS, K_NUMPAD_ENTER = 256, 269, 270, 271

ENTER_KEYS = {K_ENTER, K_NUMPAD_ENTER}
ZOOM_IN_KEYS = {ord("="), ord("+"), K_NUMPAD_PLUS}
ZOOM_OUT_KEYS = {ord("-"), K_NUMPAD_MINUS}
ZOOM_RESET_KEYS = {ord("0"), K_NUMPAD0}
DIRECTION_KEYS: Dict[int, Tuple[int, int]] = {
    K_UP: (0, 1), K_DOWN: (0, -1), K_LEFT: (-1, 0), K_RIGHT: (1, 0),
    ord("w"): (0, 1), ord("s"): (0, -1), ord("a"): (-1, 0), ord("d"): (1, 0),
}

def key_char(key: int) -> Optional[str]:
    """Lower-case letter for a keycode, or None."""
    return chr(key) if 97 <= key <= 122 else None

class Gestures:
    """Turns raw touches on a widget into high-level callbacks.

    - one finger held: ``on_hold(touch)`` fires at once and then repeats while held
      (used for tap/hold-to-walk)
    - one finger dragged: ``on_drag(dx, dy)`` in screen pixels (used to pan the map)
    - two fingers: ``on_pinch(factor)`` relative to the zoom when the pinch started
    - mouse wheel: ``on_wheel(zoom_in)``
    """
    HOLD_REPEAT = 0.14

    def __init__(self, widget, on_hold: Callable = None, on_drag: Callable = None,
                 on_pinch: Callable = None, on_wheel: Callable = None, on_pinch_start: Callable = None):
        self.widget = widget
        self.on_hold, self.on_drag = on_hold, on_drag
        self.on_pinch, self.on_wheel, self.on_pinch_start = on_pinch, on_wheel, on_pinch_start
        self.touches = []
        self._pinch_dist = None
        self._hold_event = None

    @staticmethod
    def swipe_vector(touch) -> Optional[Tuple[float, float]]:
        """Drag vector since touch-down, or None if the finger has barely moved."""
        dx, dy = touch.x - touch.ox, touch.y - touch.oy
        return (dx, dy) if math.hypot(dx, dy) > dp(24) else None

    def touch_down(self, touch) -> bool:
        if not self.widget.collide_point(*touch.pos): return False
        if touch.is_mouse_scrolling:
            if self.on_wheel and touch.button in ("scrolldown", "scrollup"):
                self.on_wheel(touch.button == "scrolldown")
            return True
        touch.grab(self.widget)
        self.touches.append(touch)
        if len(self.touches) == 2:
            self._cancel_hold()
            self._pinch_dist = self._distance()
            if self.on_pinch_start: self.on_pinch_start()
        elif len(self.touches) == 1 and self.on_hold:
            self.on_hold(touch)
            self._hold_event = Clock.schedule_interval(lambda dt: self.on_hold(touch), self.HOLD_REPEAT)
        return True

    def touch_move(self, touch) -> bool:
        if touch.grab_current is not self.widget: return False
        if len(self.touches) >= 2 and self._pinch_dist:
            if self.on_pinch: self.on_pinch(self._distance() / self._pinch_dist)
        elif len(self.touches) == 1 and self.on_drag:
            self.on_drag(touch.dx, touch.dy)
        return True

    def touch_up(self, touch) -> bool:
        if touch.grab_current is not self.widget: return False
        touch.ungrab(self.widget)
        if touch in self.touches: self.touches.remove(touch)
        if len(self.touches) < 2: self._pinch_dist = None
        if not self.touches: self._cancel_hold()
        return True

    def reset(self):
        self._cancel_hold()
        self.touches, self._pinch_dist = [], None

    def _distance(self) -> float:
        a, b = self.touches[0], self.touches[1]
        return max(1.0, math.hypot(a.x - b.x, a.y - b.y))

    def _cancel_hold(self):
        if self._hold_event:
            self._hold_event.cancel()
            self._hold_event = None
