import json
import os
import random
from typing import Dict, Any, Tuple, Type
from maze_topology import SquareCellGrid, HexCellGrid, TriCellGrid, PolarCellGrid, Grid
from maze_algorithms import (
    RecursiveBacktracker, RandomizedPrims, AldousBroder,
    BinaryTree, Wilsons, Kruskals, Sidewinder, RecursiveDivision,
    HuntAndKill, Ellers, MazeGenerator
)

class AdventureEngine:
    def __init__(self, profile_path: str = "player_profile.json"):
        self.profile_path = profile_path
        self.data = self.load_profile()

    def load_profile(self) -> Dict[str, Any]:
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r") as f:
                    data = json.load(f)
                    # Migrating old profiles
                    if "exp" not in data: data["exp"] = 0
                    if "level_history" not in data: data["level_history"] = []
                    return data
            except Exception:
                pass
        return {"skill_level": 1, "total_mazes": 0, "exp": 0, "level_history": []}

    def save_profile(self):
        with open(self.profile_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_next_maze_params(self) -> Dict[str, Any]:
        level = self.data["skill_level"]
        
        # Difficulty Scaling Logic - Expanded for larger mazes
        rows = 10 + min(level * 2, 60)
        cols = 15 + min(level * 2, 80)
        levels = 1 + (level // 12)
        
        # Dark Mode / FOV Logic: Probability increases with skill level
        dark_mode = False
        fov_radius = None
        if level > 3:
            dark_mode = random.random() < min(0.1 + (level * 0.05), 0.8)
            if dark_mode:
                # FOV radius shrinks as level increases (harder)
                base_rad = 10 # in cells
                fov_radius = max(3, base_rad - (level // 10))

        # Topology progression
        grid_classes = [SquareCellGrid]
        if level > 5: grid_classes.append(TriCellGrid)
        if level > 10: grid_classes.append(PolarCellGrid)
        if level > 15: grid_classes.append(HexCellGrid)
        GridClass = random.choice(grid_classes)
        
        # Algorithm progression
        algorithms = [
            (BinaryTree, "Binary Tree"), (Sidewinder, "Sidewinder")
        ]
        if level > 3:
            algorithms += [(RandomizedPrims, "Prim's"), (RecursiveDivision, "Rec. Division")]
        if level > 7:
            algorithms += [(Kruskals, "Kruskal's"), (HuntAndKill, "Hunt & Kill")]
        if level > 12:
            algorithms += [(RecursiveBacktracker, "Backtracker"), (Wilsons, "Wilson's"), (AldousBroder, "Aldous-Broder")]
        
        AlgoClass, gen_name = random.choice(algorithms)
        
        return {
            "GridClass": GridClass,
            "shape": "rectangle" if GridClass != PolarCellGrid else "circle",
            "rows": rows,
            "cols": cols,
            "levels": min(levels, 6),
            "generator": AlgoClass(),
            "gen_name": gen_name,
            "animate": level < 5,
            "braid_pct": 0.0,
            "show_trace": True,
            "random_endpoints": level > 8,
            "dark_mode": dark_mode,
            "fov_radius": fov_radius
        }

    def process_result(self, time_taken: float, steps: int, used_solution: bool, used_map: bool, maze_difficulty: int):
        self.data["total_mazes"] += 1
        
        # Calculate performance multiplier
        perf = 1.0
        if used_solution: perf *= 0.2
        if used_map: perf *= 0.8
        
        # Time bonus
        time_bonus = max(0.5, 2.0 - (time_taken / 60.0))
        
        exp_gain = int(100 * maze_difficulty * perf * time_bonus)
        self.data["exp"] += exp_gain
        
        # Level up logic
        prev_level = self.data["skill_level"]
        if exp_gain > 50:
            self.data["skill_level"] += 1
            if exp_gain > 150: # Critical win
                self.data["skill_level"] += 1
        
        self.data["level_history"].append({
            "level": prev_level,
            "exp_gain": exp_gain,
            "time": time_taken,
            "difficulty": maze_difficulty
        })
        self.save_profile()
