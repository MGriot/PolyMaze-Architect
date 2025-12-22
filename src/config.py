# config.py
import json
import os

# Screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
SCREEN_TITLE = "PolyMaze Architect: Multi-Algo"

# Grid
CELL_SIZE = 30
WALL_THICKNESS = 2
ROWS = 21
COLS = 31

# Physics
MOVEMENT_SPEED = 6

# Theme handling
DEFAULT_THEME = "dark"
THEMES_FILE = os.path.join(os.path.dirname(__file__), "themes.json")

def load_all_themes():
    try:
        if not os.path.exists(THEMES_FILE): return {}
        with open(THEMES_FILE, "r") as f:
            data = json.load(f)
            # Basic validation
            valid_themes = {}
            required_keys = ["BG_COLOR", "WALL_COLOR", "PLAYER_COLOR", "GOAL_COLOR"]
            for name, colors in data.items():
                if all(k in colors for k in required_keys):
                    valid_themes[name] = colors
            return valid_themes
    except Exception:
        return {}

ALL_THEMES = load_all_themes()
CURRENT_THEME_NAME = DEFAULT_THEME

# Initialize colors with default theme
def apply_theme(theme_name):
    global CURRENT_THEME_NAME, BG_COLOR, WALL_COLOR, PLAYER_COLOR, GOAL_COLOR, PATH_TRACE_COLOR
    global COLOR_SOL_BFS, COLOR_SOL_DFS, COLOR_SOL_ASTAR, TEXT_COLOR, GENERATION_COLOR, HIGHLIGHT_COLOR
    
    theme = ALL_THEMES.get(theme_name, ALL_THEMES.get(DEFAULT_THEME))
    if not theme:
        # Fallback if themes.json is missing or broken
        BG_COLOR = (20, 20, 20)
        WALL_COLOR = (180, 180, 180)
        PLAYER_COLOR = (50, 205, 50)
        GOAL_COLOR = (220, 20, 60)
        PATH_TRACE_COLOR = (65, 105, 225)
        COLOR_SOL_BFS = (0, 255, 255)
        COLOR_SOL_DFS = (255, 165, 0)
        COLOR_SOL_ASTAR = (255, 215, 0)
        TEXT_COLOR = (255, 255, 255)
        GENERATION_COLOR = (50, 205, 50)
        HIGHLIGHT_COLOR = (255, 215, 0)
        return

    CURRENT_THEME_NAME = theme_name
    BG_COLOR = tuple(theme["BG_COLOR"])
    WALL_COLOR = tuple(theme["WALL_COLOR"])
    PLAYER_COLOR = tuple(theme["PLAYER_COLOR"])
    GOAL_COLOR = tuple(theme["GOAL_COLOR"])
    PATH_TRACE_COLOR = tuple(theme["PATH_TRACE_COLOR"])
    COLOR_SOL_BFS = tuple(theme["COLOR_SOL_BFS"])
    COLOR_SOL_DFS = tuple(theme["COLOR_SOL_DFS"])
    COLOR_SOL_ASTAR = tuple(theme["COLOR_SOL_ASTAR"])
    TEXT_COLOR = tuple(theme["TEXT_COLOR"])
    GENERATION_COLOR = tuple(theme["GENERATION_COLOR"])
    HIGHLIGHT_COLOR = tuple(theme["HIGHLIGHT_COLOR"])

# Initial application
apply_theme(DEFAULT_THEME)