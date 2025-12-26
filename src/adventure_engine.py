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
    def __init__(self, slot: int = 1):
        self.slot = slot
        self.profile_path = f"player_profile_{slot}.json"
        self.data = self.load_profile()

    @staticmethod
    def get_profile_info(slot: int) -> Dict[str, Any]:
        path = f"player_profile_{slot}.json"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    return {
                        "exists": True,
                        "level": data.get("skill_level", 1),
                        "exp": data.get("exp", 0),
                        "total_mazes": data.get("total_mazes", 0)
                    }
            except Exception: pass
        return {"exists": False, "level": 1, "exp": 0, "total_mazes": 0}

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
        
        # Difficulty Scaling Logic - Expanded for more granular progression
        rows = 10 + min(level * 3, 110)
        cols = 15 + min(level * 3, 140)
        levels = 1 + (level // 8)
        
        # Fog of War / Explorative Map Logic
        explorative_map = False
        if level > 2:
            # Probability increases with level
            explorative_map = random.random() < min(0.2 + (level * 0.08), 0.9)

        # Dark Mode / FOV Logic
        dark_mode = False
        fov_radius = None
        if level > 5:
            dark_mode = random.random() < min(0.1 + (level * 0.06), 0.85)
            if dark_mode:
                base_rad = 12
                fov_radius = max(2.5, base_rad - (level // 7))

        # Topology progression
        grid_classes = [SquareCellGrid]
        if level > 4: grid_classes.append(TriCellGrid)
        if level > 8: grid_classes.append(PolarCellGrid)
        if level > 12: grid_classes.append(HexCellGrid)
        GridClass = random.choice(grid_classes)
        
        # Algorithm progression
        algorithms = [(BinaryTree, "Binary Tree"), (Sidewinder, "Sidewinder")]
        if level > 3: algorithms += [(RandomizedPrims, "Prim's"), (RecursiveDivision, "Rec. Division")]
        if level > 7: algorithms += [(Kruskals, "Kruskal's"), (HuntAndKill, "Hunt & Kill")]
        if level > 11: algorithms += [(RecursiveBacktracker, "Backtracker"), (Wilsons, "Wilson's"), (AldousBroder, "Aldous-Broder")]
        if level > 15: algorithms += [(Ellers, "Eller's")]
        
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
            "braid_pct": min(0.5, level * 0.02), # Multi-path becomes common at high levels
            "show_trace": True,
            "random_endpoints": level > 6,
            "dark_mode": dark_mode,
            "fov_radius": fov_radius,
            "explorative_map": explorative_map
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
