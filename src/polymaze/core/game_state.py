# game_state.py
"""Game rules for one maze run, independent of any UI toolkit."""
import math
import random
import time
from typing import Callable, Iterator, List, Optional, Set, Tuple, Type

from . import settings
from .adventure import AdventureEngine
from .algorithms import MazeGenerator, MazeSolver, BFS_Solver, DFS_Solver, AStar_Solver
from .catalog import grid_type_for
from .geometry import MazeGeometry
from .topology import Grid, Cell

Pos3 = Tuple[int, int, int]

class GameState:
    def __init__(self, GridClass: Type[Grid], shape: str, rows: int, cols: int, levels: int,
                 generator: MazeGenerator, gen_name: str, animate: bool, braid_pct: float,
                 show_trace: bool, randomize_start_end: bool, mode: str = "CREATIVE",
                 adventure_slot: int = 1, explorative_map: bool = False, collect_stars: bool = False,
                 dark_mode: bool = False, fov_radius: Optional[float] = None, data_dir: str = ".",
                 clock: Callable[[], float] = time.time, **_):
        self.clock = clock
        self.mode, self.gen_name, self.braid_pct = mode, gen_name, braid_pct
        self.adventure_slot, self.data_dir = adventure_slot, data_dir
        self.explorative_map, self.collect_stars = explorative_map, collect_stars
        self.show_trace, self.randomize_start_end = show_trace, randomize_start_end
        self.show_fov = dark_mode
        self.fov_radius_cells: float = fov_radius or 6.0

        self.grid = GridClass(rows, cols, levels)
        self.grid.mask_shape(shape)
        self.geometry = MazeGeometry(self.grid, settings.CELL_RADIUS, grid_type_for(GridClass))

        self.player_cell: Optional[Cell] = None
        self.current_level = 0
        self.start_pos: Pos3 = (0, 0, 0); self.end_pos: Pos3 = (0, 0, 0)
        self.path_history: List[Tuple[Tuple[int, int], int]] = []
        self.cells_visited: Set[Pos3] = set()
        self.stars: List[Cell] = []; self.stars_collected: Set[Cell] = set()
        self.step_count = 0; self.start_time = 0.0; self.solve_duration = 0.0
        self.game_won = False
        self.used_solution = False; self.used_map = False
        self.adventure_result: Optional[dict] = None

        self.solvers: List[Tuple[MazeSolver, str]] = [(BFS_Solver(), "BFS"), (DFS_Solver(), "DFS"), (AStar_Solver(), "A*")]
        self.current_solver_idx = 0
        self.solution_path: List[Pos3] = []
        self.show_solution = False; self.solving = False
        self.sol_iterator: Optional[Iterator] = None
        self._multi_sol_shown = False

        self.generating = False
        self.gen_iterator: Optional[Iterator] = None
        if animate:
            self.generating, self.gen_iterator = True, generator.generate_step(self.grid)
        else:
            generator.generate(self.grid); self.finish_generation()

    # --- Generation ---
    def step_generation(self) -> bool:
        """Advances the animated generator by one frame's worth of steps. Returns True when done."""
        if not self.generating: return True
        # Adaptive generation speed based on grid size
        steps_per_frame = max(50, self.grid.size() // 100)
        try:
            for _ in range(steps_per_frame): next(self.gen_iterator)
        except (StopIteration, TypeError):
            self.finish_generation()
        return not self.generating

    def finish_generation(self):
        if self.braid_pct > 0: self.grid.braid(self.braid_pct)
        self.generating = False

        # Select Start and End points (Avoiding stairs)
        all_cells = list(self.grid.each_cell())
        non_stair_cells = [c for c in all_cells if not self._has_stairs(c)]
        valid_cells = non_stair_cells if len(non_stair_cells) >= 2 else all_cells

        if valid_cells:
            if self.randomize_start_end:
                s_c = random.choice(valid_cells); e_c = random.choice(valid_cells)
                while e_c == s_c and len(valid_cells) > 1: e_c = random.choice(valid_cells)
            else:
                valid_cells.sort(key=lambda c: (c.level, c.row, c.column))
                s_c, e_c = valid_cells[0], valid_cells[-1]
            self.start_pos, self.end_pos = self._pos(s_c), self._pos(e_c)

        if self.collect_stars:
            # Exclude Start, End, AND Stairs (cells with vertical links)
            potential = [c for c in self.grid.each_cell()
                         if self._pos(c) not in (self.start_pos, self.end_pos) and not self._has_stairs(c)]
            self.stars = random.sample(potential, 3) if len(potential) >= 3 else potential

        self.player_cell = self.grid.get_cell(*self.start_pos)
        self.current_level = self.start_pos[2]
        self.path_history = [(self.start_pos[:2], self.start_pos[2])]
        self.cells_visited = {self.start_pos}
        self.start_time = self.clock()

    @staticmethod
    def _pos(cell: Cell) -> Pos3:
        return (cell.row, cell.column, cell.level)

    @staticmethod
    def _has_stairs(cell: Cell) -> bool:
        return any(n.level != cell.level for n in cell.get_links())

    # --- Movement ---
    def move(self, direction: Tuple[float, float]) -> bool:
        """Moves to the linked neighbor that best matches a direction vector (any length)."""
        if self.generating or self.game_won or not self.player_cell: return False
        dx_key, dy_key = direction
        mag_key = math.hypot(dx_key, dy_key)
        if mag_key == 0: return False
        dx_key, dy_key = dx_key / mag_key, dy_key / mag_key

        best_n, best_score = None, -1.0
        px, py = self.geometry.get_pixel(self.player_cell.row, self.player_cell.column)
        for n in self.player_cell.get_links():
            if n.level != self.player_cell.level: continue
            nx, ny = self.geometry.get_pixel(n.row, n.column)
            dx_n, dy_n = nx - px, ny - py; mag = math.hypot(dx_n, dy_n)
            if mag == 0: continue
            score = (dx_n/mag * dx_key) + (dy_n/mag * dy_key)
            if score > 0.4 and score > best_score: best_score, best_n = score, n
        if not best_n: return False
        self.player_cell = best_n; self.step_count += 1
        self._on_enter_cell()
        return True

    @property
    def stair_options(self) -> List[Tuple[int, str]]:
        if not self.player_cell: return []
        options = []
        for link in self.player_cell.get_links():
            if link.level > self.player_cell.level: options.append((link.level, "U"))
            elif link.level < self.player_cell.level: options.append((link.level, "D"))
        return options

    def take_stairs(self, direction: str) -> bool:
        """direction is "U" or "D"."""
        if self.generating or self.game_won or not self.player_cell: return False
        for lv, ds in self.stair_options:
            if ds != direction: continue
            target = self.grid.get_cell(self.player_cell.row, self.player_cell.column, lv)
            if target and self.player_cell.is_linked(target):
                self.player_cell, self.current_level = target, lv; self.step_count += 1
                self._on_enter_cell()
                return True
        return False

    def _on_enter_cell(self):
        pos = self._pos(self.player_cell)
        self.cells_visited.add(pos)
        if self.collect_stars:
            for star in self.stars:
                if self._pos(star) == pos: self.stars_collected.add(star)
        if self.show_trace and (not self.path_history or self.path_history[-1] != (pos[:2], pos[2])):
            self.path_history.append((pos[:2], pos[2]))
        if pos == self.end_pos and self.all_stars_collected:
            self._win()

    @property
    def all_stars_collected(self) -> bool:
        return not self.collect_stars or len(self.stars_collected) == len(self.stars)

    # --- Scoring ---
    def elapsed(self) -> int:
        return int(self.solve_duration) if self.game_won else int(self.clock() - self.start_time)

    def difficulty(self) -> int:
        """Granular difficulty for the adaptive learning model."""
        base_diff = (self.grid.rows * self.grid.columns * self.grid.levels) / 100.0
        if self.show_fov: base_diff *= 1.5
        if self.explorative_map: base_diff *= 1.3
        return int(base_diff)

    def _win(self):
        self.game_won, self.solve_duration = True, self.clock() - self.start_time
        self.show_solution = self.solving = False
        if self.mode == "ADVENTURE":
            engine = AdventureEngine(self.adventure_slot, self.data_dir)
            engine.process_result(self.solve_duration, self.step_count, self.used_solution, self.used_map,
                                  self.difficulty(), len(self.stars_collected))
            self.adventure_result = AdventureEngine.get_profile_info(self.adventure_slot, self.data_dir)

    def next_adventure_params(self) -> dict:
        return AdventureEngine(self.adventure_slot, self.data_dir).get_next_maze_params()

    def abandon(self) -> int:
        """Manual reset. Applies the adventure penalty and returns the EXP lost."""
        if self.mode != "ADVENTURE" or self.game_won: return 0
        return AdventureEngine(self.adventure_slot, self.data_dir).process_reset()

    # --- Tools ---
    def toggle_map(self, shown: bool):
        if shown: self.used_map = True

    def toggle_solution(self):
        """Tiered: 1st press solves to goal, 2nd (stars pending) routes through stars, 3rd hides."""
        if self.generating or self.game_won or not self.player_cell: return
        solver = self.solvers[self.current_solver_idx][0]
        goal = self.grid.get_cell(*self.end_pos)
        if not self.show_solution:
            self.show_solution = self.used_solution = True
            self.solving, self.sol_iterator = True, solver.solve_step(self.grid, self.player_cell, goal)
        elif self.collect_stars and not self.all_stars_collected and not self._multi_sol_shown:
            pending = [s for s in self.stars if s not in self.stars_collected]
            self.solving, self.sol_iterator = True, solver.solve_multi(self.grid, self.player_cell, pending, goal)
            self._multi_sol_shown = True
        else:
            self.show_solution = self.solving = False
            self._multi_sol_shown = False

    def cycle_solver(self):
        self.current_solver_idx = (self.current_solver_idx + 1) % len(self.solvers)
        if self.show_solution and self.player_cell:
            self._multi_sol_shown = False
            goal = self.grid.get_cell(*self.end_pos)
            self.solving, self.sol_iterator = True, self.solvers[self.current_solver_idx][0].solve_step(self.grid, self.player_cell, goal)

    @property
    def solver_name(self) -> str:
        return self.solvers[self.current_solver_idx][1]

    def step_solver(self, steps: int = 5):
        if not (self.solving and self.sol_iterator): return
        try:
            for _ in range(steps): self.solution_path = next(self.sol_iterator)
        except StopIteration:
            self.solving = False

    # --- Rendering helpers ---
    def player_world_pos(self) -> Tuple[float, float]:
        if not self.player_cell: return self.geometry.get_pixel(*self.start_pos[:2])
        return self.geometry.get_pixel(self.player_cell.row, self.player_cell.column)

    def fov_radius_world(self) -> float:
        return self.geometry.cell_radius * self.fov_radius_cells
