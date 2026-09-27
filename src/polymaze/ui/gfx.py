# gfx.py
"""Kivy drawing helpers: colors, batched meshes, world-space text, camera."""
import math
from typing import Dict, Iterable, List, Sequence, Tuple

from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle, Scale, Translate
from kivy.metrics import dp

Point = Tuple[float, float]

# Kivy meshes use 16-bit indices, so large mazes are split into several meshes.
MAX_VERTS_PER_MESH = 60000

def rgba(color: Sequence[int], alpha: int = None) -> Tuple[float, float, float, float]:
    """(r, g, b[, a]) in 0-255 to a Kivy 0-1 tuple."""
    a = alpha if alpha is not None else (color[3] if len(color) > 3 else 255)
    return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, a / 255.0)

def ui_scale() -> float:
    """UI size multiplier: 1.0 on an 800 px tall desktop window, grows with screen height on phones."""
    return max(0.6, min(dp(1), Window.height / 800.0))

def u(value: float) -> float:
    return value * ui_scale()

def touch_size(value: float = 44) -> float:
    """Height for tappable controls: scaled, but never below a comfortable finger size."""
    return max(u(value), dp(40))

def polygon_meshes(polygons: Iterable[Sequence[Point]]) -> List[Mesh]:
    """Batches convex polygons into as few triangle meshes as possible."""
    meshes, verts, idx, n = [], [], [], 0
    for poly in polygons:
        k = len(poly)
        if k < 3: continue
        if n + k > MAX_VERTS_PER_MESH:
            meshes.append(Mesh(vertices=verts, indices=idx, mode="triangles"))
            verts, idx, n = [], [], 0
        for x, y in poly: verts.extend((x, y, 0.0, 0.0))
        for i in range(1, k - 1): idx.extend((n, n + i, n + i + 1))
        n += k
    if idx: meshes.append(Mesh(vertices=verts, indices=idx, mode="triangles"))
    return meshes

def fan_mesh(center: Point, outline: Sequence[Point]) -> Mesh:
    """Filled star-shaped polygon (FOV, stars) as a triangle fan around ``center``."""
    mesh = Mesh(mode="triangle_fan")
    set_fan(mesh, center, outline)
    return mesh

def set_fan(mesh: Mesh, center: Point, outline: Sequence[Point]):
    verts = [center[0], center[1], 0.0, 0.0]
    for x, y in list(outline) + [outline[0]] if outline else []:
        verts.extend((x, y, 0.0, 0.0))
    mesh.vertices = verts
    mesh.indices = list(range(len(verts) // 4))

def segment_quads(segments: Iterable[Tuple[Point, Point]], width: float) -> List[List[Point]]:
    """Thick line segments as quads, so they can be batched with polygon_meshes."""
    quads, hw = [], width / 2.0
    for (x1, y1), (x2, y2) in segments:
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy)
        if d == 0: continue
        nx, ny = -dy / d * hw, dx / d * hw
        quads.append([(x1 - nx, y1 - ny), (x2 - nx, y2 - ny), (x2 + nx, y2 + ny), (x1 + nx, y1 + ny)])
    return quads

def polyline(points: Sequence[Point], width: float) -> Line:
    """Line strip whose total thickness is ``width`` world units."""
    flat = [v for p in points for v in p]
    return Line(points=flat, width=max(1.01, width / 2.0), joint="round", cap="round")

def circle(cx: float, cy: float, r: float) -> Ellipse:
    return Ellipse(pos=(cx - r, cy - r), size=(2 * r, 2 * r))

_text_cache: Dict[Tuple[str, float, bool], object] = {}

def text_texture(text: str, font_size: float, bold: bool = False):
    key = (text, font_size, bold)
    tex = _text_cache.get(key)
    if tex is None:
        label = CoreLabel(text=text, font_size=font_size, bold=bold)
        label.refresh()
        tex = _text_cache[key] = label.texture
    return tex

def text_rect(text: str, x: float, y: float, font_size: float, bold: bool = False,
              anchor_x: str = "center", anchor_y: str = "center") -> Rectangle:
    """White text as a textured rectangle; tint it with a preceding Color."""
    tex = text_texture(text, font_size, bold)
    w, h = tex.size
    px = x - w / 2 if anchor_x == "center" else (x - w if anchor_x == "right" else x)
    py = y - h / 2 if anchor_y == "center" else (y - h if anchor_y == "top" else y)
    return Rectangle(texture=tex, pos=(px, py), size=(w, h))

class Camera:
    """2D camera: world point (x, y) is shown at the widget centre, scaled by zoom."""
    def __init__(self, min_zoom: float = 0.05, max_zoom: float = 3.0):
        self.x = self.y = 0.0
        self.zoom = 1.0
        self.min_zoom, self.max_zoom = min_zoom, max_zoom
        self._center = Translate()
        self._scale = Scale(1.0)
        self._offset = Translate()
        self._widget = None

    def instructions(self, widget):
        """Adds the transform to the current canvas context (call inside ``with canvas:`` after PushMatrix)."""
        self._widget = widget
        return self._center, self._scale, self._offset

    def set_zoom(self, zoom: float):
        self.zoom = max(self.min_zoom, min(self.max_zoom, zoom))

    def apply(self):
        w = self._widget
        self._center.xy = (w.x + w.width / 2.0, w.y + w.height / 2.0)
        self._scale.xyz = (self.zoom, self.zoom, 1.0)
        self._offset.xy = (-self.x, -self.y)

    def screen_to_world(self, sx: float, sy: float) -> Point:
        w = self._widget
        return ((sx - (w.x + w.width / 2.0)) / self.zoom + self.x,
                (sy - (w.y + w.height / 2.0)) / self.zoom + self.y)

    def world_to_screen(self, wx: float, wy: float) -> Point:
        w = self._widget
        return ((wx - self.x) * self.zoom + w.x + w.width / 2.0,
                (wy - self.y) * self.zoom + w.y + w.height / 2.0)
