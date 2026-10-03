"""Captures the README/docs screenshots from the running Kivy app.

Writes docs/img/*.png at the default 1280x800 window size. Profiles are seeded in a
throwaway folder, so your real saves are never touched. Run from the repo root:
    python tools/capture_screenshots.py
"""
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "img")
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("KIVY_NO_ARGS", "1")

DATA_DIR = tempfile.mkdtemp(prefix="polymaze-shots-")
os.chdir(DATA_DIR)  # migrate_legacy_profiles() moves profiles out of the CWD

from polymaze.ui.app import PolyMazeApp  # noqa: E402  (sets the window Config first)

from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402

from polymaze.core.adventure import AdventureEngine  # noqa: E402
from polymaze.core.algorithms import (AStar_Solver, HuntAndKill, RandomizedPrims,  # noqa: E402
                                      RecursiveBacktracker, Wilsons)
from polymaze.core.topology import HexCellGrid, PolarCellGrid, SquareCellGrid, TriCellGrid  # noqa: E402
from polymaze.ui.maze_widget import MazeView  # noqa: E402

# Overview shots frame the whole maze; normally the camera follows the player.
FRAMING = {"overview": False}
_tick = MazeView.tick

def _framed_tick(self):
    _tick(self)
    if self.state and FRAMING["overview"]:
        self.camera.x = self.camera.y = 0.0
        self.camera.apply()

MazeView.tick = _framed_tick

DEMO_PROFILES = {  # slot: (skill vector, exp, mazes)
    1: (dict(spatial=6.4, perception=5.6, structural=9.2, efficiency=3.1, collection=4.0), 4210, 23),
    2: (dict(spatial=2.2, perception=1.5, structural=2.6, efficiency=1.3, collection=1.0), 640, 5),
}

def seed_profiles():
    for slot, (skills, exp, mazes) in DEMO_PROFILES.items():
        eng = AdventureEngine(slot, DATA_DIR)
        eng.data.update(skill_profile=skills, exp=exp, total_mazes=mazes)
        eng.save_profile()

def creative(GridClass, Gen, gen_name, shape="rectangle", rows=21, cols=31, levels=1, **extra):
    params = dict(GridClass=GridClass, shape=shape, rows=rows, cols=cols, levels=levels, generator=Gen(),
                  gen_name=gen_name, animate=False, braid_pct=0.0, show_trace=True, randomize_start_end=False,
                  mode="CREATIVE", explorative_map=False, collect_stars=False)
    params.update(extra)
    return params

def walk(state, steps):
    """Moves the player along the A* route to the exit on the current floor, never stopping on a stair."""
    start = state.grid.get_cell(*state.start_pos)
    goal = state.grid.get_cell(*state.end_pos)
    def step_to(r, c):
        px, py = state.geometry.get_pixel(state.player_cell.row, state.player_cell.column)
        nx, ny = state.geometry.get_pixel(r, c)
        state.move((nx - px, ny - py))

    for i, (r, c, level) in enumerate(AStar_Solver().solve(state.grid, start, goal)[1:]):
        if level != state.current_level or (i >= steps and not state.stair_options): break
        step_to(r, c)
    if state.stair_options:  # its STAIRS button would cover the shot
        flat = [n for n in state.player_cell.get_links()
                if n.level == state.current_level and all(m.level == n.level for m in n.get_links())]
        if flat: step_to(flat[0].row, flat[0].column)

class Capture(PolyMazeApp):
    @property
    def user_data_dir(self):
        return DATA_DIR

    def on_start(self):
        seed_profiles()
        game = self.sm.get_screen("game")
        creative_menu = self.sm.get_screen("creative")

        def setup_creative():
            creative_menu.cell_idx, creative_menu.shape_idx, creative_menu.gen_idx = 1, 13, 3  # Hexagonal, hexagon, Wilson's
            creative_menu.levels, creative_menu.collect_stars = 2, True
            self.go("creative")

        def play(params, seed, steps=0, solve=False, zoom=0.0, show_map=False, overview=True):
            def start():
                FRAMING["overview"] = overview
                random.seed(seed)
                self.start_game(**params)
            def act():
                walk(game.state, steps)
                if solve: game.toggle_solution()
                if zoom: game.maze.zoom_by(zoom)
                if show_map: game.toggle_map()
            return [(start, 1.0), (act, 2.5)]

        # (step, seconds to wait before the next step); a str step saves a screenshot with that name
        self.steps = [
            (lambda: self.go("menu"), 0.5), "main-menu",
            (lambda: self.go("profiles"), 0.5), "profiles",
            (setup_creative, 0.5), "creative-setup",
            *play(creative(SquareCellGrid, RecursiveBacktracker, "Backtracker"), 7, steps=14, solve=True), "game-square",
            *play(creative(HexCellGrid, Wilsons, "Wilson's", shape="hexagon", rows=19, cols=23), 3, steps=12), "game-hex",
            *play(creative(TriCellGrid, RandomizedPrims, "Prim's", shape="triangle", rows=21, cols=41), 5, steps=12), "game-tri",
            *play(creative(PolarCellGrid, RecursiveBacktracker, "Backtracker", shape="circle", rows=12, cols=12), 11, steps=10), "game-polar",
            *play(creative(SquareCellGrid, HuntAndKill, "Hunt & Kill", rows=31, cols=41, dark_mode=True, fov_radius=7.0, braid_pct=0.5),
                  4, steps=18, zoom=0.9, overview=False), "game-fov",
            *play(creative(SquareCellGrid, RandomizedPrims, "Prim's", rows=15, cols=23, collect_stars=True,
                           randomize_start_end=True), 9, steps=10), "game-stars",
            *play(creative(SquareCellGrid, RecursiveBacktracker, "Backtracker", levels=2, rows=13, cols=19), 2,
                  steps=12, solve=True, show_map=True), "map-view",
        ]
        os.makedirs(OUT, exist_ok=True)
        Clock.schedule_once(self._next, 1.0)

    def _next(self, *_):
        if not self.steps:
            print("screenshots written to", OUT, flush=True)
            os._exit(0)  # mirrors tools/make_assets.py
        step = self.steps.pop(0)
        if isinstance(step, str):
            path = os.path.join(OUT, f"{step}.png")
            os.replace(Window.screenshot(name=path), path)  # Kivy inserts a counter: step0001.png
            print("wrote", path, flush=True)
            Clock.schedule_once(self._next, 0.2)
        else:
            action, wait = step
            action()
            Clock.schedule_once(self._next, wait)

if __name__ == "__main__":
    Capture().run()
