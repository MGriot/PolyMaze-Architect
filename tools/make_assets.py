"""Renders the app icon and splash screen from a seeded maze.

Writes src/polymaze/assets/{icon.png, icon.ico, presplash.png}. Run from the repo root:
    python tools/make_assets.py
"""
import os
import random
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy.config import Config  # noqa: E402
Config.set("graphics", "window_state", "hidden")

from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.graphics import Color, Fbo, PopMatrix, PushMatrix, Rectangle, RoundedRectangle, Scale, Translate  # noqa: E402

from polymaze.core import settings  # noqa: E402
from polymaze.core.algorithms import AStar_Solver, RecursiveBacktracker  # noqa: E402
from polymaze.core.geometry import MazeGeometry  # noqa: E402
from polymaze.core.topology import HexCellGrid  # noqa: E402
from polymaze.ui.gfx import circle, polygon_meshes, polyline, rgba  # noqa: E402

OUT = os.path.join(ROOT, "src", "polymaze", "assets")
T = settings.theme

def maze_geometry(rows, cols, seed):
    random.seed(seed)
    grid = HexCellGrid(rows, cols)
    grid.mask_shape("hexagon")
    RecursiveBacktracker().generate(grid)
    return MazeGeometry(grid, settings.CELL_RADIUS, "hex")

def render(path, size, rows, cols, seed, rounded):
    w, h = size
    geo = maze_geometry(rows, cols, seed)
    cells = sorted(geo.grid.each_cell(), key=lambda c: (c.row, c.column))
    start, goal = cells[0], cells[-1]
    route = [(r, c) for r, c, _ in AStar_Solver().solve(geo.grid, start, goal)]
    mw, mh = geo.get_maze_size()
    zoom = min(w / mw, h / mh) * (0.78 if rounded else 0.6)

    fbo = Fbo(size=size, with_stencilbuffer=False)
    with fbo:
        Color(0, 0, 0, 0); Rectangle(pos=(0, 0), size=size)
        Color(*rgba(T.BG_COLOR))
        if rounded: RoundedRectangle(pos=(0, 0), size=size, radius=[w * 0.18])
        else: Rectangle(pos=(0, 0), size=size)
        PushMatrix(); Translate(w / 2, h / 2); Scale(zoom, zoom, 1)
        Color(*rgba(T.WALL_COLOR))
        for mesh in polygon_meshes(geo.get_occlusion_polygons(0)): fbo.add(mesh)
        Color(*rgba(T.COLOR_SOL_ASTAR))
        fbo.add(polyline([geo.get_pixel(r, c) for r, c in route], geo.cell_radius * 0.35))
        Color(*rgba(T.GOAL_COLOR)); fbo.add(circle(*geo.get_pixel(goal.row, goal.column), geo.cell_radius * 0.55))
        Color(*rgba(T.PLAYER_COLOR)); fbo.add(circle(*geo.get_pixel(start.row, start.column), geo.cell_radius * 0.55))
        PopMatrix()
    fbo.draw()
    fbo.texture.save(path, flipped=False)
    print("wrote", path)

def png_to_ico(png_path, ico_path):
    """Windows .ico containing a single 256x256 PNG image (supported since Vista)."""
    data = open(png_path, "rb").read()
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(data), 6 + 16)
    with open(ico_path, "wb") as f:
        f.write(header + entry + data)
    print("wrote", ico_path)

class Maker(App):
    def build(self):
        from kivy.uix.widget import Widget
        Clock.schedule_once(self.make, 0)
        return Widget()

    def make(self, *_):
        os.makedirs(OUT, exist_ok=True)
        icon = os.path.join(OUT, "icon.png")
        render(icon, (512, 512), 7, 7, 3, rounded=True)
        render(os.path.join(OUT, "icon256.png"), (256, 256), 7, 7, 3, rounded=True)
        png_to_ico(os.path.join(OUT, "icon256.png"), os.path.join(OUT, "icon.ico"))
        os.remove(os.path.join(OUT, "icon256.png"))
        render(os.path.join(OUT, "presplash.png"), (1280, 720), 9, 17, 11, rounded=False)
        os._exit(0)  # App.stop() trips a Kivy wm_pen bug when the window is hidden

if __name__ == "__main__":
    Maker().run()
