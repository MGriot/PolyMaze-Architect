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
                    profile = data.get("skill_profile", {})
                    # Calculate an aggregate level for display
                    avg_lvl = sum(profile.values()) / len(profile) if profile else data.get("skill_level", 1)
                    return {
                        "exists": True,
                        "level": round(avg_lvl, 1),
                        "exp": data.get("exp", 0),
                        "total_mazes": data.get("total_mazes", 0)
                    }
            except Exception: pass
        return {"exists": False, "level": 1.0, "exp": 0, "total_mazes": 0}

    def load_profile(self) -> Dict[str, Any]:
        default_data = {
            "skill_profile": {
                "spatial": 1.0,    # Rows, Cols, Levels
                "perception": 1.0, # FOV, Fog of War
                "structural": 1.0, # Topologies, Algorithms
                "efficiency": 1.0, # Braiding, Momentum
                "collection": 1.0  # Star challenges
            },
            "total_mazes": 0,
            "exp": 0,
            "momentum": 0,
            "level_history": []
        }
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r") as f:
                    data = json.load(f)
                    # Migrate old profiles to new vector system
                    if "skill_profile" not in data:
                        old_lvl = float(data.get("skill_level", 1))
                        data["skill_profile"] = {k: old_lvl for k in default_data["skill_profile"]}
                    if "collection" not in data["skill_profile"]:
                        data["skill_profile"]["collection"] = 1.0
                    if "momentum" not in data: data["momentum"] = 0
                    return data
            except Exception: pass
        return default_data

    def get_next_maze_params(self) -> Dict[str, Any]:
        p = self.data["skill_profile"]
        
        # ... (previous logic for spatial, perception, etc.)
        rows = int(10 + min(p["spatial"] * 2.5, 110))
        cols = int(15 + min(p["spatial"] * 3.0, 140))
        levels = int(1 + min(p["spatial"] // 8, 5))
        
        # 2. Perceptual Challenges
        explorative_map = False
        if p["perception"] > 3.0:
            explorative_map = random.random() < min((p["perception"] - 3) * 0.15, 0.95)
            
        dark_mode = False
        fov_radius = None
        if p["perception"] > 5.0:
            dark_mode = random.random() < min((p["perception"] - 5) * 0.1, 0.85)
            if dark_mode:
                base_rad = 12
                fov_radius = max(2.5, base_rad - (p["perception"] // 4))

        # 3. Collection Challenge
        collect_stars = False
        if p["collection"] > 2.0:
            collect_stars = random.random() < min((p["collection"] - 2) * 0.2, 0.9)

        # 4. Structural Complexity
        grid_classes = [SquareCellGrid]
        if p["structural"] > 4: grid_classes.append(TriCellGrid)
        if p["structural"] > 8: grid_classes.append(PolarCellGrid)
        if p["structural"] > 12: grid_classes.append(HexCellGrid)
        GridClass = random.choice(grid_classes)
        
        algorithms = [(BinaryTree, "Binary Tree"), (Sidewinder, "Sidewinder")]
        if p["structural"] > 3: algorithms += [(RandomizedPrims, "Prim's"), (RecursiveDivision, "Rec. Division")]
        if p["structural"] > 7: algorithms += [(Kruskals, "Kruskal's"), (HuntAndKill, "Hunt & Kill")]
        if p["structural"] > 11: algorithms += [(RecursiveBacktracker, "Backtracker"), (Wilsons, "Wilson's"), (AldousBroder, "Aldous-Broder")]
        if p["structural"] > 15: algorithms += [(Ellers, "Eller's")]
        AlgoClass, gen_name = random.choice(algorithms)
        
        braid_pct = min(0.5, p["efficiency"] * 0.03)

        return {
            "GridClass": GridClass,
            "shape": "rectangle" if GridClass != PolarCellGrid else "circle",
            "rows": rows, "cols": cols, "levels": levels,
            "generator": AlgoClass(), "gen_name": gen_name,
            "animate": p["structural"] < 5.0,
            "braid_pct": braid_pct,
            "show_trace": True,
            "random_endpoints": p["spatial"] > 6.0,
            "dark_mode": dark_mode,
            "fov_radius": fov_radius,
            "explorative_map": explorative_map,
            "collect_stars": collect_stars
        }

    def process_reset(self):
        """Penalty for manual reset in adventure mode."""
        loss = int(50 * self.data["skill_profile"]["spatial"])
        self.data["exp"] = max(0, self.data["exp"] - loss)
        self.data["momentum"] = max(-3, self.data["momentum"] - 2)
        # Slight decay in all vectors
        for k in self.data["skill_profile"]:
            self.data["skill_profile"][k] = max(1.0, self.data["skill_profile"][k] - 0.1)
        self.save_profile()
        return loss

    def process_result(self, time_taken: float, steps: int, used_solution: bool, used_map: bool, maze_difficulty: int, stars_collected: int = 0):
        self.data["total_mazes"] += 1
        p = self.data["skill_profile"]
        
        complexity_rating = maze_difficulty / 10.0
        expected_time = complexity_rating * 15.0 
        speed_ratio = expected_time / max(1.0, time_taken)
        
        tool_penalty = 1.0
        if used_solution: tool_penalty *= 0.2 # Harsher penalty
        if used_map: tool_penalty *= 0.6
        
        perf_score = speed_ratio * tool_penalty
        if stars_collected > 0:
            perf_score *= (1.0 + (stars_collected * 0.15))

        # Update Momentum
        if tool_penalty > 0.9 and speed_ratio > 1.1:
            self.data["momentum"] += 1
        elif tool_penalty < 0.5 or speed_ratio < 0.4:
            self.data["momentum"] = max(-3, self.data["momentum"] - 1)
        else:
            self.data["momentum"] = 0

        growth_rate = 0.2 + (max(0, self.data["momentum"]) * 0.1)
        
        if perf_score > 0.8: # Success threshold lowered but growth scaled
            p["spatial"] += growth_rate * 1.2
            p["structural"] += growth_rate * 0.8
            if not used_map: p["perception"] += growth_rate * 1.5
            if not used_solution: p["efficiency"] += growth_rate * 1.0
            if stars_collected == 3: p["collection"] += growth_rate * 2.0
        else: # Failure/Heavy struggle
            for k in p: p[k] = max(1.0, p[k] - 0.15)
            
        exp_gain = int(100 * complexity_rating * perf_score)
        self.data["exp"] += exp_gain
        
        self.data["level_history"].append({
            "profile_snapshot": p.copy(),
            "exp_gain": exp_gain,
            "time": time_taken,
            "score": perf_score,
            "stars": stars_collected
        })
        self.save_profile()
