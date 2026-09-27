# settings.py
import json
import os
from typing import Dict, Tuple

APP_TITLE = "PolyMaze Architect"

# Default desktop window (mobile uses the full screen)
DEFAULT_WINDOW_SIZE = (1280, 800)

# Grid rendering
CELL_RADIUS = 45
FOV_RAYS = 60

DEFAULT_THEME = "dark"
THEMES_FILE = os.path.join(os.path.dirname(__file__), "themes.json")

Color = Tuple[int, ...]

_REQUIRED_KEYS = ["BG_COLOR", "WALL_COLOR", "PLAYER_COLOR", "GOAL_COLOR"]
_FALLBACK_THEME = {
    "BG_COLOR": [20, 20, 20],
    "WALL_COLOR": [180, 180, 180],
    "PLAYER_COLOR": [50, 205, 50],
    "GOAL_COLOR": [220, 20, 60],
    "PATH_TRACE_COLOR": [65, 105, 225],
    "COLOR_SOL_BFS": [0, 255, 255],
    "COLOR_SOL_DFS": [255, 165, 0],
    "COLOR_SOL_ASTAR": [255, 215, 0],
    "TEXT_COLOR": [255, 255, 255],
    "GENERATION_COLOR": [50, 205, 50],
    "HIGHLIGHT_COLOR": [255, 215, 0],
}

# Fixed accent colors that do not change with the theme
STAR_COLOR: Color = (255, 215, 0)
STAR_COLLECTED_COLOR: Color = (100, 100, 0, 100)
STAIR_UP_COLOR: Color = (0, 127, 255)
STAIR_DOWN_COLOR: Color = (165, 42, 42)
STAIR_PROMPT_COLOR: Color = (0, 255, 255)
GRID_OUTLINE_COLOR: Color = (60, 60, 60)
FOG_LEGEND_COLOR: Color = (128, 128, 128)

def load_all_themes() -> Dict[str, Dict[str, list]]:
    try:
        if not os.path.exists(THEMES_FILE): return {}
        with open(THEMES_FILE, "r") as f:
            data = json.load(f)
        return {name: colors for name, colors in data.items() if all(k in colors for k in _REQUIRED_KEYS)}
    except Exception:
        return {}

class Theme:
    """Active color palette. Attribute names match the keys in themes.json."""
    def __init__(self):
        self.all_themes = load_all_themes()
        self.name = DEFAULT_THEME
        self.apply(DEFAULT_THEME)

    def apply(self, name: str):
        colors = dict(_FALLBACK_THEME)
        colors.update(self.all_themes.get(name, self.all_themes.get(DEFAULT_THEME, {})))
        self.name = name if name in self.all_themes else DEFAULT_THEME
        for key, value in colors.items():
            setattr(self, key, tuple(value))

    def toggle(self):
        self.apply("light" if self.name == "dark" else "dark")

    @property
    def solver_colors(self):
        return [self.COLOR_SOL_BFS, self.COLOR_SOL_DFS, self.COLOR_SOL_ASTAR]

theme = Theme()
