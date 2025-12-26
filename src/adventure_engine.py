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
                "efficiency": 1.0  # Braiding, Momentum
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
                    if "momentum" not in data: data["momentum"] = 0
                    return data
            except Exception: pass
        return default_data

    def save_profile(self):
        with open(self.profile_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def get_next_maze_params(self) -> Dict[str, Any]:
        p = self.data["skill_profile"]
        
        # 1. Spatial Scaling (1.0 -> 50.0 range)
        rows = int(10 + min(p["spatial"] * 2.5, 110))
        cols = int(15 + min(p["spatial"] * 3.0, 140))
        levels = int(1 + min(p["spatial"] // 8, 5))
        
        # 2. Perceptual Challenges
        # Fog of War starts appearing at perception > 3
        explorative_map = False
        if p["perception"] > 3.0:
            explorative_map = random.random() < min((p["perception"] - 3) * 0.15, 0.95)
            
        # Dark mode starts appearing at perception > 5
        dark_mode = False
        fov_radius = None
        if p["perception"] > 5.0:
            dark_mode = random.random() < min((p["perception"] - 5) * 0.1, 0.85)
            if dark_mode:
                base_rad = 12
                # Radius shrinks as perception increases
                fov_radius = max(2.5, base_rad - (p["perception"] // 4))

        # 3. Structural Complexity (Topologies)
        grid_classes = [SquareCellGrid]
        if p["structural"] > 4: grid_classes.append(TriCellGrid)
        if p["structural"] > 8: grid_classes.append(PolarCellGrid)
        if p["structural"] > 12: grid_classes.append(HexCellGrid)
        GridClass = random.choice(grid_classes)
        
        # 4. Algorithm Complexity
        algorithms = [(BinaryTree, "Binary Tree"), (Sidewinder, "Sidewinder")]
        if p["structural"] > 3: algorithms += [(RandomizedPrims, "Prim's"), (RecursiveDivision, "Rec. Division")]
        if p["structural"] > 7: algorithms += [(Kruskals, "Kruskal's"), (HuntAndKill, "Hunt & Kill")]
        if p["structural"] > 11: algorithms += [(RecursiveBacktracker, "Backtracker"), (Wilsons, "Wilson's"), (AldousBroder, "Aldous-Broder")]
        if p["structural"] > 15: algorithms += [(Ellers, "Eller's")]
        AlgoClass, gen_name = random.choice(algorithms)
        
        # 5. Efficiency (Braid)
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
            "explorative_map": explorative_map
        }

    def process_result(self, time_taken: float, steps: int, used_solution: bool, used_map: bool, maze_difficulty: int):
        self.data["total_mazes"] += 1
        p = self.data["skill_profile"]
        
        # Calculate performance factors
        # 1. Speed factor (expected ~1 sec per complexity unit)
        complexity_rating = maze_difficulty / 10.0
        expected_time = complexity_rating * 15.0 # baseline
        speed_ratio = expected_time / max(1.0, time_taken)
        
        # 2. Penalty for tools
        tool_penalty = 1.0
        if used_solution: tool_penalty *= 0.3
        if used_map: tool_penalty *= 0.7
        
        perf_score = speed_ratio * tool_penalty
        
        # Update Momentum
        if tool_penalty > 0.9 and speed_ratio > 1.2:
            self.data["momentum"] += 1
        elif tool_penalty < 0.5 or speed_ratio < 0.5:
            self.data["momentum"] = max(-2, self.data["momentum"] - 1)
        else:
            self.data["momentum"] = 0

        # ADAPTIVE GROWTH LOGIC
        # Boost spatial if they solved a big maze efficiently
        growth_rate = 0.2 + (max(0, self.data["momentum"]) * 0.1)
        
        if perf_score > 1.0: # Success
            p["spatial"] += growth_rate * 1.2
            p["structural"] += growth_rate * 0.8
            # Only grow perception if they didn't use the map
            if not used_map: p["perception"] += growth_rate * 1.5
            if not used_solution: p["efficiency"] += growth_rate * 1.0
        else: # Struggle
            # Stabilize or slightly reduce
            p["spatial"] = max(1.0, p["spatial"] - 0.1)
            p["perception"] = max(1.0, p["perception"] - 0.2)
            
        # Experience gain
        exp_gain = int(100 * complexity_rating * perf_score)
        self.data["exp"] += exp_gain
        
        self.data["level_history"].append({
            "profile_snapshot": p.copy(),
            "exp_gain": exp_gain,
            "time": time_taken,
            "score": perf_score
        })
        self.save_profile()
