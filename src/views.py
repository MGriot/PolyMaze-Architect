# views.py
import arcade
import arcade.shape_list
import config
import math
import os
import random
import time
import traceback
from typing import List, Tuple, Optional, Type, Iterator
from maze_topology import SquareCellGrid, HexCellGrid, TriCellGrid, PolarCellGrid, Grid, Cell
from maze_algorithms import (
    RecursiveBacktracker, RandomizedPrims, AldousBroder,
    BinaryTree, Wilsons, Kruskals, Sidewinder, RecursiveDivision,
    HuntAndKill, Ellers,
    MazeGenerator, MazeSolver, BFS_Solver, DFS_Solver, AStar_Solver
)
from renderer import MazeRenderer

class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.cell_types: List[Tuple[str, Type[Grid]]] = [
            ("Square", SquareCellGrid), 
            ("Hexagonal", HexCellGrid), 
            ("Triangular", TriCellGrid), 
            ("Polar", PolarCellGrid)
        ]
        self.cell_idx: int = 0
        self.shapes: List[str] = ["rectangle", "circle", "triangle", "hexagon"]
        self.shape_idx: int = 0
        self.sizes: List[Tuple[str, int, int]] = [
            ("Small", 11, 15), 
            ("Medium", 21, 31), 
            ("Large", 31, 41)
        ]
        self.size_idx: int = 1
        self.generators: List[Tuple[str, Type[MazeGenerator]]] = [
            ("Backtracker", RecursiveBacktracker), ("Prim's", RandomizedPrims),
            ("Aldous-Broder", AldousBroder), ("Wilson's", Wilsons),
            ("Binary Tree", BinaryTree), ("Kruskal's", Kruskals),
            ("Sidewinder", Sidewinder), ("Rec. Division", RecursiveDivision),
            ("Hunt & Kill", HuntAndKill), ("Eller's", Ellers)
        ]
        self.gen_idx: int = 0
        self.animate: bool = True
        self.multi_path: bool = False
        self.levels: int = 1
        self.show_trace: bool = True
        self.random_endpoints: bool = False
        self.title_text: Optional[arcade.Text] = None
        self.option_texts: List[arcade.Text] = []

    def on_show_view(self):
        arcade.set_background_color(config.BG_COLOR)
        self.setup_ui()

    def setup_ui(self):
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        self.title_text = arcade.Text("POLY MAZE ARCHITECT", cw, ch + 220, config.TEXT_COLOR, font_size=40, anchor_x="center")
        self.update_options()

    def update_options(self):
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        options = [
            f"G: Cell Shape -> {self.cell_types[self.cell_idx][0]}",
            f"F: Maze Form -> {self.shapes[self.shape_idx].upper()}",
            f"Z: Size -> {self.sizes[self.size_idx][0]}",
            f"A: Algorithm -> {self.generators[self.gen_idx][0]}",
            f"V: Animation -> {'ENABLED' if self.animate else 'DISABLED'}",
            f"M: Multi-Path -> {'ON' if self.multi_path else 'OFF'}",
            f"L: 3D Levels -> {self.levels}",
            f"E: Random Endpoints -> {'ON' if self.random_endpoints else 'OFF'}",
            f"R: Show Trace -> {'ON' if self.show_trace else 'OFF'}",
            f"T: Theme -> {config.CURRENT_THEME_NAME.upper()}",
            "", "PRESS ENTER TO START", "PRESS ESC TO QUIT"
        ]
        self.option_texts = []
        for i, line in enumerate(options):
            color = config.WALL_COLOR if ":" in line else config.HIGHLIGHT_COLOR
            self.option_texts.append(arcade.Text(line, cw, ch + 130 - (i * 32), color, font_size=16, anchor_x="center"))

    def on_draw(self):
        self.clear()
        if self.title_text: self.title_text.draw()
        for text in self.option_texts: text.draw()

    def on_key_press(self, key: int, modifiers: int):
        changed = True
        if key == arcade.key.G: self.cell_idx = (self.cell_idx + 1) % len(self.cell_types)
        elif key == arcade.key.F: self.shape_idx = (self.shape_idx + 1) % len(self.shapes)
        elif key == arcade.key.Z: self.size_idx = (self.size_idx + 1) % len(self.sizes)
        elif key == arcade.key.A: self.gen_idx = (self.gen_idx + 1) % len(self.generators)
        elif key == arcade.key.V: self.animate = not self.animate
        elif key == arcade.key.M: self.multi_path = not self.multi_path
        elif key == arcade.key.L: self.levels = (self.levels % 4) + 1
        elif key == arcade.key.E: self.random_endpoints = not self.random_endpoints
        elif key == arcade.key.R: self.show_trace = not self.show_trace
        elif key == arcade.key.T:
            config.apply_theme("light" if config.CURRENT_THEME_NAME == "dark" else "dark")
            arcade.set_background_color(config.BG_COLOR); self.setup_ui()
        elif key == arcade.key.ENTER: self.start_game(); changed = False
        elif key == arcade.key.ESCAPE: arcade.exit(); changed = False
        else: changed = False
        if changed: self.update_options()

    def start_game(self):
        _, GridClass = self.cell_types[self.cell_idx]
        shape = self.shapes[self.shape_idx]; _, rows, cols = self.sizes[self.size_idx]
        gen_name, GenClass = self.generators[self.gen_idx]
        game = GameView(); game.setup(GridClass, shape, rows, cols, self.levels, GenClass(), gen_name, self.animate, 0.5 if self.multi_path else 0.0, self.show_trace, self.random_endpoints)
        self.window.show_view(game)

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.grid: Optional[Grid] = None
        self.renderer: Optional[MazeRenderer] = None
        self.wall_shapes_layers: List[arcade.shape_list.ShapeElementList] = [] 
        self.stair_shapes_layers: List[arcade.shape_list.ShapeElementList] = [] 
        self.grid_shapes: Optional[arcade.shape_list.ShapeElementList] = None 
        self.player_sprite: Optional[arcade.Sprite] = None
        self.player_list: arcade.SpriteList = arcade.SpriteList()
        self.player_cell: Optional[Cell] = None
        self.target_pos: Optional[Tuple[float, float]] = None
        self.current_level: int = 0
        self.path_history: List[Tuple[Tuple[float, float], int]] = [] 
        self.show_trace: bool = True
        self.current_solver_idx: int = 0
        self.solvers: List[Tuple[MazeSolver, str, Tuple[int, int, int]]] = [
            (BFS_Solver(), "BFS", config.COLOR_SOL_BFS), 
            (DFS_Solver(), "DFS", config.COLOR_SOL_DFS), 
            (AStar_Solver(), "A*", config.COLOR_SOL_ASTAR)
        ]
        self.solution_path: List[Tuple[int, int, int]] = [] 
        self.show_solution: bool = False
        self.solving: bool = False
        self.sol_iterator: Optional[Iterator] = None
        self.gen_iterator: Optional[Iterator] = None
        self.generating: bool = False
        self.hud_text_1: Optional[arcade.Text] = None
        self.hud_text_2: Optional[arcade.Text] = None
        self.status_text: Optional[arcade.Text] = None
        self.stair_prompt: Optional[arcade.Text] = None
        self.current_stair_options: List[Tuple[int, str]] = []
        self.top_margin: int = 80
        self.bottom_margin: int = 60
        self.show_map: bool = False
        self.map_wall_shapes: List[arcade.shape_list.ShapeElementList] = [] 
        self.map_stair_shapes: List[arcade.shape_list.ShapeElementList] = []
        self.start_time: float = 0
        self.solve_duration: float = 0
        self.game_won: bool = False
        self.cells_visited: set = set()
        self.start_pos: Tuple[int, int, int] = (0,0,0)
        self.end_pos: Tuple[int, int, int] = (0,0,0)

    def setup(self, GridClass: Type[Grid], shape: str, rows: int, cols: int, levels: int, generator: MazeGenerator, gen_name: str, animate: bool, braid_pct: float, show_trace: bool, random_endpoints: bool):
        self.gen_name, self.grid = gen_name, GridClass(rows, cols, levels)
        self.grid.mask_shape(shape)
        if GridClass == HexCellGrid: gtype = "hex"
        elif GridClass == TriCellGrid: gtype = "tri"
        elif GridClass == PolarCellGrid: gtype = "polar"
        else: gtype = "rect"
        
        avail_h = config.SCREEN_HEIGHT - self.top_margin - self.bottom_margin
        if gtype == "hex": rad = avail_h / (rows * 1.5 + 0.5)
        elif gtype == "tri": rad = avail_h / (rows + 1.5)
        elif gtype == "polar": rad = avail_h / (2 * (rows + 3))
        else: rad = avail_h / (2 * rows + 2)
        
        self.renderer = MazeRenderer(self.grid, rad, gtype, self.top_margin, self.bottom_margin)
        self.show_trace, self.current_level, self.path_history, self.solution_path, self.show_map, self.game_won = show_trace, 0, [], [], False, False
        self.cells_visited, self.player_list, self.grid_shapes = set(), arcade.SpriteList(), arcade.shape_list.ShapeElementList()
        
        for cell in self.grid.each_cell():
            if cell.level == 0:
                cx, cy = self.renderer.get_pixel(cell.row, cell.column)
                if gtype == "hex": pts = [(cx + rad*math.cos(math.radians(a)), cy + rad*math.sin(math.radians(a))) for a in [30, 90, 150, 210, 270, 330]]
                elif gtype == "tri": pts = self.renderer.get_tri_verts(cell.row, cell.column, cx, cy, rad)
                else: pts = [(cx-rad, cy-rad), (cx+rad, cy-rad), (cx+rad, cy+rad), (cx-rad, cy+rad)]
                self.grid_shapes.append(arcade.shape_list.create_line_loop(pts, (60, 60, 60), 1))
        
        self.setup_ui_text()
        valid_cells = list(self.grid.each_cell())
        if valid_cells:
            if random_endpoints:
                self.start_pos = (random.choice(valid_cells).row, random.choice(valid_cells).column, 0)
                self.end_pos = (random.choice(valid_cells).row, random.choice(valid_cells).column, levels-1)
            else:
                valid_cells.sort(key=lambda c: (c.level, c.row, c.column))
                self.start_pos = (valid_cells[0].row, valid_cells[0].column, 0)
                self.end_pos = (valid_cells[-1].row, valid_cells[-1].column, levels-1)
        
        if animate: self.generating, self.gen_iterator = True, generator.generate_step(self.grid)
        else:
            generator.generate(self.grid)
            if braid_pct > 0: self.grid.braid(braid_pct)
            self.finish_generation()

    def setup_ui_text(self):
        self.hud_text_1 = arcade.Text("", 20, config.SCREEN_HEIGHT-35, config.TEXT_COLOR, font_size=14, bold=True)
        self.hud_text_2 = arcade.Text("WASD/ARROWS: Move | X: Sol | TAB: AI | M: Architectural Map | P: Print | ESC: Menu", 20, config.SCREEN_HEIGHT-60, config.WALL_COLOR, font_size=11)
        self.status_text = arcade.Text("GENERATING...", config.SCREEN_WIDTH/2, 30, config.TEXT_COLOR, font_size=16, anchor_x="center")
        self.stair_prompt = arcade.Text("", config.SCREEN_WIDTH/2, 30, arcade.color.CYAN, font_size=18, anchor_x="center", bold=True)
        self.update_hud()

    def update_hud(self):
        l_str = f"Floor {self.current_level+1}/{self.grid.levels}" if self.grid and self.grid.levels > 1 else ""
        if self.hud_text_1: self.hud_text_1.text = f"{self.gen_name.upper()} ARCHITECT | {l_str}"

    def finish_generation(self):
        self.generating = False
        self.wall_shapes_layers = [self.renderer.create_wall_shapes(l) for l in range(self.grid.levels)]
        self.stair_shapes_layers = [self.renderer.create_stair_shapes(l) for l in range(self.grid.levels)]
        self.generate_map_shapes()
        sr, sc, sl = self.start_pos
        self.player_cell = self.grid.get_cell(sr, sc, sl)
        px, py = self.renderer.get_pixel(sr, sc)
        rad = int(self.renderer.cell_radius * 0.3)
        self.player_sprite = arcade.Sprite(); self.player_sprite.texture = arcade.make_circle_texture(rad*2, config.PLAYER_COLOR)
        self.player_sprite.center_x, self.player_sprite.center_y = px, py
        self.player_list.append(self.player_sprite)
        self.target_pos, self.path_history, self.start_time, self.cells_visited = (px, py), [((px, py), sl)], time.time(), set([(sr, sc, sl)])
        self.update_hud()

    def generate_map_shapes(self):
        self.map_wall_shapes = [self.renderer.create_wall_shapes(l, scale=0.35, offset=(0, (l-(self.grid.levels-1)/2)*config.SCREEN_HEIGHT*0.22), thickness_mult=0.5) for l in range(self.grid.levels)]
        self.map_stair_shapes = [self.renderer.create_stair_shapes(l, scale=0.35, offset=(0, (l-(self.grid.levels-1)/2)*config.SCREEN_HEIGHT*0.22)) for l in range(self.grid.levels)]

    def draw_map_overlay(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT, (0,0,0,235))
        arcade.draw_text("EXPLODED ARCHITECTURAL VIEW", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT-40, arcade.color.CYAN, font_size=20, anchor_x="center", bold=True)
        for l in range(self.grid.levels):
            off = (0, (l-(self.grid.levels-1)/2)*config.SCREEN_HEIGHT*0.22); p_center = self.renderer.get_pixel(self.grid.rows//2, self.grid.columns//2, 0.35, off)
            arcade.draw_lbwh_rectangle_filled(p_center[0]-200, p_center[1]-150, 400, 300, (50, 50, 50, 100))
            self.map_wall_shapes[l].draw(); self.map_stair_shapes[l].draw()
            if l == self.current_level and self.player_cell: px, py = self.renderer.get_pixel(self.player_cell.row, self.player_cell.column, 0.35, off); arcade.draw_circle_filled(px, py, 5, config.PLAYER_COLOR)

    def draw_minimap(self):
        if self.grid.levels <= 1: return
        x, y = config.SCREEN_WIDTH-40, config.SCREEN_HEIGHT-100; arcade.draw_lbwh_rectangle_filled(x-30, y-60, 60, 120, (0,0,0,120))
        for i in range(self.grid.levels):
            color = arcade.color.CYAN if i == self.current_level else (100, 100, 100, 150)
            arcade.draw_lbwh_rectangle_filled(x-20, y-50+i*25, 40, 20, color)

    def draw_victory(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT, (0,0,0,200)); cw, ch = config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2
        arcade.draw_text("CONGRATULATIONS!", cw, ch+80, arcade.color.GOLD, font_size=36, anchor_x="center", bold=True)
        stats = [f"Time: {int(self.solve_duration)}s", f"Cells: {len(self.cells_visited)}", "", "PRESS ENTER TO RESTART"]
        for i, line in enumerate(stats): arcade.draw_text(line, cw, ch-20-i*30, config.HIGHLIGHT_COLOR if "ENTER" in line else config.TEXT_COLOR, font_size=16, anchor_x="center")

    def on_draw(self):
        self.clear()
        if self.generating:
            self.grid_shapes.draw()
            for cell in self.grid.each_cell():
                cx, cy = self.renderer.get_pixel(cell.row, cell.column)
                for link in cell.get_links():
                    if link.level == cell.level: lx, ly = self.renderer.get_pixel(link.row, link.column); arcade.draw_line(cx, cy, lx, ly, config.GENERATION_COLOR, 3)
            self.status_text.draw(); return
        if self.show_map: self.draw_map_overlay(); return
        if len(self.wall_shapes_layers) > self.current_level: self.wall_shapes_layers[self.current_level].draw()
        if len(self.stair_shapes_layers) > self.current_level: self.stair_shapes_layers[self.current_level].draw()
        if self.show_solution and self.solution_path:
            pts = [self.renderer.get_pixel(r, c) for r, c, l in self.solution_path if l == self.current_level]
            if len(pts) > 1: arcade.draw_line_strip(pts, self.solvers[self.current_solver_idx][2], 4)
        if self.show_trace and len(self.path_history) > 1:
            pts = [p for p, l in self.path_history if l == self.current_level]
            if len(pts) > 1: arcade.draw_line_strip(pts, config.PATH_TRACE_COLOR, 2)
        if self.current_level == self.end_pos[2]: gx, gy = self.renderer.get_pixel(self.end_pos[0], self.end_pos[1]); arcade.draw_circle_filled(gx, gy, self.renderer.cell_radius*0.4, config.GOAL_COLOR)
        self.player_list.draw(); self.hud_text_1.draw(); self.hud_text_2.draw(); self.draw_minimap()
        if self.current_stair_options and self.stair_prompt: self.stair_prompt.draw()
        if self.game_won: self.draw_victory()

    def on_update(self, delta_time: float):
        if self.generating:
            try:
                for _ in range(50): next(self.gen_iterator)
            except (StopIteration, TypeError): self.finish_generation()
            return
        if self.game_won: return
        if self.solving and self.sol_iterator:
            try:
                for _ in range(5): self.solution_path = next(self.sol_iterator)
            except StopIteration: self.solving = False
        if self.player_sprite and self.target_pos:
            dx, dy = self.target_pos[0]-self.player_sprite.center_x, self.target_pos[1]-self.player_sprite.center_y
            self.player_sprite.center_x += dx*0.4; self.player_sprite.center_y += dy*0.4
        if self.player_cell:
            r, c, l = self.player_cell.row, self.player_cell.column, self.player_cell.level; self.cells_visited.add((r, c, l))
            if (r, c, l) == self.end_pos: self.game_won, self.solve_duration = True, time.time()-self.start_time; return
            if self.show_trace and self.player_sprite and (not self.path_history or (self.player_sprite.center_x-self.path_history[-1][0][0])**2 + (self.player_sprite.center_y-self.path_history[-1][0][1])**2 > 25): self.path_history.append(((self.player_sprite.center_x, self.player_sprite.center_y), self.current_level))
            self.current_stair_options = []
            for link in self.player_cell.get_links():
                if link.level > l: self.current_stair_options.append((link.level, "U"))
                elif link.level < l: self.current_stair_options.append((link.level, "D"))
            if self.stair_prompt: self.stair_prompt.text = f"STAIRS: Press {' / '.join(['['+o[1]+']' for o in self.current_stair_options])} to move" if self.current_stair_options else ""

    def on_key_press(self, key: int, modifiers: int):
        if self.generating or self.game_won:
            if self.game_won and key == arcade.key.ENTER: self.window.show_view(MenuView())
            return
        if key == arcade.key.M: self.show_map = not self.show_map; return
        if self.show_map: return
        dir_map = {arcade.key.UP: (0, 1), arcade.key.DOWN: (0, -1), arcade.key.LEFT: (-1, 0), arcade.key.RIGHT: (1, 0), arcade.key.W: (0, 1), arcade.key.S: (0, -1), arcade.key.A: (-1, 0), arcade.key.D: (1, 0)}
        if key in dir_map:
            dx_key, dy_key = dir_map[key]; best_n, best_score = None, -1.0
            if self.player_cell:
                px, py = self.renderer.get_pixel(self.player_cell.row, self.player_cell.column)
                for n in self.player_cell.get_links():
                    if n.level != self.player_cell.level: continue
                    nx, ny = self.renderer.get_pixel(n.row, n.column); dx_n, dy_n = nx-px, ny-py; mag = math.sqrt(dx_n*dx_n + dy_n*dy_n)
                    if mag == 0: continue
                    score = (dx_n/mag * dx_key) + (dy_n/mag * dy_key)
                    if score > 0.4 and score > best_score: best_score, best_n = score, n
                if best_n: self.player_cell, self.target_pos = best_n, self.renderer.get_pixel(best_n.row, best_n.column)
        elif key in [arcade.key.U, arcade.key.D]:
            td = "U" if key == arcade.key.U else "D"
            for lv, ds in self.current_stair_options:
                if ds == td and self.player_cell:
                    self.current_level = lv; target = self.grid.get_cell(self.player_cell.row, self.player_cell.column, lv) if self.grid else None
                    if target and self.player_cell.is_linked(target): self.player_cell = target; px, py = self.renderer.get_pixel(target.row, target.column); self.player_sprite.center_x, self.player_sprite.center_y = px, py; self.target_pos = (px, py); self.update_hud(); break
        elif key == arcade.key.X:
            self.show_solution = not self.show_solution
            if self.show_solution and self.grid: self.solving, self.sol_iterator = True, self.solvers[self.current_solver_idx][0].solve_step(self.grid, self.grid.get_cell(*self.start_pos), self.grid.get_cell(*self.end_pos))
        elif key == arcade.key.TAB:
            self.current_solver_idx = (self.current_solver_idx + 1) % len(self.solvers); self.update_hud()
            if self.show_solution and self.grid: self.solving, self.sol_iterator = True, self.solvers[self.current_solver_idx][0].solve_step(self.grid, self.grid.get_cell(*self.start_pos), self.grid.get_cell(*self.end_pos))
        elif key == arcade.key.P: arcade.get_image().save("maze_export.png")
        elif key == arcade.key.ESCAPE: self.window.show_view(MenuView())

    def on_key_release(self, key: int, modifiers: int): pass