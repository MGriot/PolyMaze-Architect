# views.py
import arcade
import arcade.camera
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
from adventure_engine import AdventureEngine

class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.options = ["ADVENTURE", "CREATIVE / TRAINING"]
        self.selection = 0
        self.title_text: Optional[arcade.Text] = None
        self.option_texts: List[arcade.Text] = []

    def on_show_view(self):
        arcade.set_background_color(config.BG_COLOR)
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        self.title_text = arcade.Text("POLY MAZE ARCHITECT", cw, ch + 150, config.TEXT_COLOR, font_size=40, anchor_x="center", bold=True)
        self.update_ui()

    def update_ui(self):
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        self.option_texts = []
        for i, opt in enumerate(self.options):
            color = config.HIGHLIGHT_COLOR if i == self.selection else config.WALL_COLOR
            text = f"> {opt} <" if i == self.selection else opt
            self.option_texts.append(arcade.Text(text, cw, ch - (i * 60), color, font_size=24, anchor_x="center"))

    def on_draw(self):
        self.clear()
        if self.title_text: self.title_text.draw()
        for t in self.option_texts: t.draw()
        arcade.draw_text("UP/DOWN: Select | ENTER: Confirm | ESC: Quit", config.SCREEN_WIDTH/2, 50, config.WALL_COLOR, font_size=12, anchor_x="center")

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.UP: self.selection = (self.selection - 1) % len(self.options); self.update_ui()
        elif key == arcade.key.DOWN: self.selection = (self.selection + 1) % len(self.options); self.update_ui()
        elif key == arcade.key.ENTER:
            if self.selection == 0: self.window.show_view(ProfileSelectView())
            else: self.window.show_view(CreativeMenuView())
        elif key == arcade.key.ESCAPE: arcade.exit()

class ProfileSelectView(arcade.View):
    def __init__(self):
        super().__init__()
        self.slots = [1, 2, 3]
        self.selection = 0
        self.profiles_info = [AdventureEngine.get_profile_info(s) for s in self.slots]
        self.title_text: Optional[arcade.Text] = None
        self.slot_texts: List[arcade.Text] = []

    def on_show_view(self):
        arcade.set_background_color(config.BG_COLOR)
        cw = config.SCREEN_WIDTH / 2
        self.title_text = arcade.Text("SELECT ADVENTURE PROFILE", cw, config.SCREEN_HEIGHT - 100, config.TEXT_COLOR, font_size=30, anchor_x="center", bold=True)
        self.update_ui()

    def update_ui(self):
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        self.slot_texts = []
        for i, info in enumerate(self.profiles_info):
            color = config.HIGHLIGHT_COLOR if i == self.selection else config.WALL_COLOR
            y = ch + 80 - (i * 120)
            status = f"LVL {info['level']} | EXP {info['exp']} | MAZES {info['total_mazes']}" if info['exists'] else "EMPTY SLOT"
            prefix = "> " if i == self.selection else "  "
            self.slot_texts.append(arcade.Text(f"{prefix}SLOT {i+1}", cw, y, color, font_size=20, anchor_x="center", bold=True))
            self.slot_texts.append(arcade.Text(status, cw, y - 30, color, font_size=14, anchor_x="center"))

    def on_draw(self):
        self.clear()
        if self.title_text: self.title_text.draw()
        for t in self.slot_texts: t.draw()
        arcade.draw_text("UP/DOWN: Select | ENTER: Play | DEL: Reset Slot | ESC: Back", config.SCREEN_WIDTH/2, 50, config.WALL_COLOR, font_size=12, anchor_x="center")

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.UP: self.selection = (self.selection - 1) % len(self.slots); self.update_ui()
        elif key == arcade.key.DOWN: self.selection = (self.selection + 1) % len(self.slots); self.update_ui()
        elif key == arcade.key.ESCAPE: self.window.show_view(MainMenuView())
        elif key == arcade.key.ENTER:
            engine = AdventureEngine(self.slots[self.selection])
            params = engine.get_next_maze_params()
            game = GameView()
            game.setup(mode="ADVENTURE", adventure_slot=self.slots[self.selection], **params)
            self.window.show_view(game)
        elif key == arcade.key.DELETE:
            path = f"player_profile_{self.slots[self.selection]}.json"
            if os.path.exists(path): os.remove(path)
            self.profiles_info[self.selection] = AdventureEngine.get_profile_info(self.slots[self.selection])
            self.update_ui()

class CreativeMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.cell_types: List[Tuple[str, Type[Grid]]] = [("Square", SquareCellGrid), ("Hexagonal", HexCellGrid), ("Triangular", TriCellGrid), ("Polar", PolarCellGrid)]
        self.cell_idx: int = 0
        self.shapes: List[str] = ["rectangle", "circle", "triangle", "hexagon"]
        self.shape_idx: int = 0
        self.sizes: List[Tuple[str, int, int]] = [("Small", 11, 15), ("Medium", 21, 31), ("Large", 31, 41)]
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
        self.random_endpoints: bool = True
        self.title_text: Optional[arcade.Text] = None
        self.option_texts: List[arcade.Text] = []

    def on_show_view(self):
        arcade.set_background_color(config.BG_COLOR)
        self.setup_ui()

    def setup_ui(self):
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        self.title_text = arcade.Text("CREATIVE / TRAINING MODE", cw, ch + 220, config.TEXT_COLOR, font_size=30, anchor_x="center", bold=True)
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
            "", "PRESS ENTER TO START", "PRESS ESC TO BACK"
        ]
        self.option_texts = []
        for i, line in enumerate(options):
            color = config.WALL_COLOR if ":" in line else config.HIGHLIGHT_COLOR
            self.option_texts.append(arcade.Text(line, cw, ch + 130 - (i * 32), color, font_size=16, anchor_x="center"))

    def on_draw(self):
        try:
            self.clear()
            if self.title_text: self.title_text.draw()
            for text in self.option_texts: text.draw()
        except Exception: traceback.print_exc()

    def on_key_press(self):
        changed = True
        if key == arcade.key.G: self.cell_idx = (self.cell_idx + 1) % len(self.cell_types)
        elif key == arcade.key.F: self.shape_idx = (self.shape_idx + 1) % len(self.shapes)
        elif key == arcade.key.Z: self.size_idx = (self.size_idx + 1) % len(self.sizes)
        elif key == arcade.key.A: self.gen_idx = (self.gen_idx + 1) % len(self.generators)
        elif key == arcade.key.V: self.animate = not self.animate
        elif key == arcade.key.M: self.multi_path = not self.multi_path
        elif key == arcade.key.L: self.levels = (self.levels % 6) + 1
        elif key == arcade.key.E: self.random_endpoints = not self.random_endpoints
        elif key == arcade.key.R: self.show_trace = not self.show_trace
        elif key == arcade.key.T:
            config.apply_theme("light" if config.CURRENT_THEME_NAME == "dark" else "dark")
            arcade.set_background_color(config.BG_COLOR); self.setup_ui()
        elif key == arcade.key.ENTER: self.start_game(); changed = False
        elif key == arcade.key.ESCAPE: self.window.show_view(MainMenuView()); changed = False
        else: changed = False
        if changed: self.update_options()

    def start_game(self):
        game = GameView(); mode = "CREATIVE"
        _, GridClass = self.cell_types[self.cell_idx]; shape = self.shapes[self.shape_idx]; _, rows, cols = self.sizes[self.size_idx]
        gen_name, GenClass = self.generators[self.gen_idx]
        game.setup(GridClass, shape, rows, cols, self.levels, GenClass(), gen_name, self.animate, 0.5 if self.multi_path else 0.0, self.show_trace, self.random_endpoints, mode=mode)
        self.window.show_view(game)

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.grid: Optional[Grid] = None; self.renderer: Optional[MazeRenderer] = None
        self.wall_shapes_layers: List[arcade.shape_list.ShapeElementList] = [] 
        self.stair_shapes_layers: List[arcade.shape_list.ShapeElementList] = [] 
        self.grid_shapes: Optional[arcade.shape_list.ShapeElementList] = None 
        self.player_sprite: Optional[arcade.Sprite] = None; self.player_list: arcade.SpriteList = arcade.SpriteList()
        self.player_cell: Optional[Cell] = None; self.target_pos: Optional[Tuple[float, float]] = None
        self.current_level: int = 0; self.braid_pct: float = 0.0
        self.path_history: List[Tuple[Tuple[int, int], int]] = []; self.show_trace: bool = True
        self.current_solver_idx: int = 0
        self.solvers: List[Tuple[MazeSolver, str, Tuple[int, int, int]]] = [(BFS_Solver(), "BFS", config.COLOR_SOL_BFS), (DFS_Solver(), "DFS", config.COLOR_SOL_DFS), (AStar_Solver(), "A*", config.COLOR_SOL_ASTAR)]
        self.solution_path: List[Tuple[int, int, int]] = []; self.show_solution: bool = False; self.solving: bool = False
        self.sol_iterator: Optional[Iterator] = None; self.gen_iterator: Optional[Iterator] = None; self.generating: bool = False
        self.hud_text_1: Optional[arcade.Text] = None; self.hud_text_2: Optional[arcade.Text] = None; self.hud_stats: Optional[arcade.Text] = None
        self.status_text: Optional[arcade.Text] = None; self.stair_prompt: Optional[arcade.Text] = None
        self.current_stair_options: List[Tuple[int, str]] = []; self.top_margin: int = 80; self.bottom_margin: int = 60
        self.show_map: bool = False; self.map_wall_shapes: List[arcade.shape_list.ShapeElementList] = []; self.map_stair_shapes: List[arcade.shape_list.ShapeElementList] = []
        self.game_won: bool = False; self.cells_visited: set = set()
        self.start_pos: Tuple[int, int, int] = (0,0,0); self.end_pos: Tuple[int, int, int] = (0,0,0)
        self.step_count: int = 0; self.start_time: float = 0; self.solve_duration: float = 0
        self.mode: str = "CREATIVE"; self.used_solution: bool = False; self.used_map: bool = False
        self.adventure_slot: int = 1
        self.maze_camera = arcade.camera.Camera2D(); self.gui_camera = arcade.camera.Camera2D()

    def setup(self, GridClass: Type[Grid], shape: str, rows: int, cols: int, levels: int, generator: MazeGenerator, gen_name: str, animate: bool, braid_pct: float, show_trace: bool, random_endpoints: bool, mode: str = "CREATIVE", **kwargs):
        self.gen_name, self.braid_pct, self.grid, self.mode = gen_name, braid_pct, GridClass(rows, cols, levels), mode
        self.used_solution, self.used_map = False, False
<<<<<<< Updated upstream
=======
        self.adventure_slot = kwargs.get("adventure_slot", 1)
        self.show_fov = kwargs.get("dark_mode", False)
        self.fov_radius_cells = kwargs.get("fov_radius", 6.0)
>>>>>>> Stashed changes
        self.grid.mask_shape(shape)
        rad = 45; gtype = "hex" if GridClass == HexCellGrid else ("tri" if GridClass == TriCellGrid else ("polar" if GridClass == PolarCellGrid else "rect"))
        self.renderer = MazeRenderer(self.grid, rad, gtype, self.top_margin, self.bottom_margin)
        self.show_trace, self.current_level, self.path_history, self.solution_path, self.show_map, self.game_won = show_trace, 0, [], [], False, False
        self.cells_visited, self.player_list, self.grid_shapes, self.step_count = set(), arcade.SpriteList(), arcade.shape_list.ShapeElementList(), 0
        for cell in self.grid.each_cell():
            if cell.level == 0:
                cx, cy = self.renderer.get_pixel(cell.row, cell.column)
                if gtype == "hex": pts = [(cx + rad*math.cos(math.radians(a)), cy + rad*math.sin(math.radians(a))) for a in [30, 90, 150, 210, 270, 330]]
                elif gtype == "tri": pts = self.renderer.get_tri_verts(cell.row, cell.column, cx, cy, rad)
                else: pts = [(cx-rad, cy-rad), (cx+rad, cy-rad), (cx+rad, cy+rad), (cx-rad, cy+rad)]
                self.grid_shapes.append(arcade.shape_list.create_line_loop(pts, (60, 60, 60), 1))
        self.setup_ui_text(); valid_cells = list(self.grid.each_cell())
        if valid_cells:
            if random_endpoints:
                s_c = random.choice(valid_cells); e_c = random.choice(valid_cells)
                while e_c == s_c and len(valid_cells)>1: e_c = random.choice(valid_cells)
                self.start_pos, self.end_pos = (s_c.row, s_c.column, s_c.level), (e_c.row, e_c.column, e_c.level)
            else:
                valid_cells.sort(key=lambda c: (c.level, c.row, c.column))
                s_c, e_c = valid_cells[0], valid_cells[-1]; self.start_pos, self.end_pos = (s_c.row, s_c.column, s_c.level), (e_c.row, e_c.column, e_c.level)
        gx, gy = self.renderer.get_pixel(self.grid.rows//2, self.grid.columns//2); self.maze_camera.position = (gx, gy)
        
        # Adaptive Zoom Logic
        maze_w, maze_h = self.renderer.get_maze_size()
        avail_w = config.SCREEN_WIDTH * 0.9
        avail_h = (config.SCREEN_HEIGHT - self.top_margin - self.bottom_margin) * 0.9
        self.maze_camera.zoom = min(avail_w / maze_w, avail_h / maze_h, 1.5)
        
        if animate: self.generating, self.gen_iterator = True, generator.generate_step(self.grid)
        else: generator.generate(self.grid); self.finish_generation()

    def setup_ui_text(self):
        self.hud_text_1 = arcade.Text("", 20, config.SCREEN_HEIGHT-25, config.TEXT_COLOR, font_size=12, bold=True)
        self.hud_text_2 = arcade.Text("WASD: Move | X: Sol | R: Trace | +/-: Zoom | 0: Reset | M: Map | ESC: Menu", 20, config.SCREEN_HEIGHT-65, config.WALL_COLOR, font_size=10)
        self.hud_stats = arcade.Text("", config.SCREEN_WIDTH-20, config.SCREEN_HEIGHT-25, config.HIGHLIGHT_COLOR, font_size=12, anchor_x="right", bold=True)
        self.status_text = arcade.Text("GENERATING...", config.SCREEN_WIDTH/2, 30, config.TEXT_COLOR, font_size=16, anchor_x="center")
        self.stair_prompt = arcade.Text("", config.SCREEN_WIDTH/2, 30, arcade.color.CYAN, font_size=18, anchor_x="center", bold=True); self.update_hud()

    def update_hud(self):
        if not self.grid: return
        l_str, z_str = f"Floor {self.current_level+1}/{self.grid.levels}", f"Zoom: {self.maze_camera.zoom:.1f}x"
        t_spent = int(time.time()-self.start_time) if not self.game_won else int(self.solve_duration)
        if self.hud_text_1: self.hud_text_1.text = f"{self.gen_name.upper()} ARCHITECT | {l_str}"
        if self.hud_stats: self.hud_stats.text = f"STEPS: {self.step_count} | TIME: {t_spent}s | {z_str} | FPS: {int(arcade.get_fps())}"

    def scroll_to_player(self, instant=False):
        if not self.player_sprite: return
        if instant: self.maze_camera.position = (self.player_sprite.center_x, self.player_sprite.center_y)
        else: cx, cy = self.maze_camera.position; self.maze_camera.position = (cx+(self.player_sprite.center_x-cx)*0.1, cy+(self.player_sprite.center_y-cy)*0.1)

    def finish_generation(self):
        try:
            if self.braid_pct > 0: self.grid.braid(self.braid_pct)
            self.generating = False; self.wall_shapes_layers = [self.renderer.create_wall_shapes(l) for l in range(self.grid.levels)]
            self.stair_shapes_layers = [self.renderer.create_stair_shapes(l) for l in range(self.grid.levels)]; self.generate_map_shapes()
            sr, sc, sl = self.start_pos; self.player_cell = self.grid.get_cell(sr, sc, sl); px, py = self.renderer.get_pixel(sr, sc)
            self.player_sprite = arcade.Sprite(); self.player_sprite.texture = arcade.make_circle_texture(int(self.renderer.cell_radius*0.6), config.PLAYER_COLOR)
            self.player_sprite.center_x, self.player_sprite.center_y = px, py; self.player_list.append(self.player_sprite)
            self.target_pos, self.path_history, self.start_time, self.cells_visited = (px, py), [((sr, sc), sl)], time.time(), set([(sr, sc, sl)]); self.update_hud(); self.scroll_to_player(True)
        except Exception: traceback.print_exc()

    def generate_map_shapes(self):
        self.map_wall_shapes = [self.renderer.create_wall_shapes(l, scale=0.35, offset=(0, (l-(self.grid.levels-1)/2)*config.SCREEN_HEIGHT*0.22), thickness_mult=0.5) for l in range(self.grid.levels)]
        self.map_stair_shapes = [self.renderer.create_stair_shapes(l, scale=0.35, offset=(0, (l-(self.grid.levels-1)/2)*config.SCREEN_HEIGHT*0.22)) for l in range(self.grid.levels)]

    def draw_map_overlay(self):
        overlay_color = config.BG_COLOR + (235,)
        arcade.draw_lbwh_rectangle_filled(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT, overlay_color)
        arcade.draw_text("EXPLODED ARCHITECTURAL VIEW", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT-40, config.HIGHLIGHT_COLOR, font_size=20, anchor_x="center", bold=True)
        for l in range(self.grid.levels):
            off = (0, (l-(self.grid.levels-1)/2)*config.SCREEN_HEIGHT*0.22); pc = self.renderer.get_pixel(self.grid.rows//2, self.grid.columns//2, 0.35, off)
            # Use a slightly contrasting box for each level
            box_color = (128, 128, 128, 100) if config.CURRENT_THEME_NAME == "dark" else (200, 200, 200, 100)
            arcade.draw_lbwh_rectangle_filled(pc[0]-200, pc[1]-150, 400, 300, box_color); self.map_wall_shapes[l].draw(); self.map_stair_shapes[l].draw()
            if self.show_solution and self.solution_path:
                pts = [self.renderer.get_pixel(r,c,0.35,off) for r,c,lv in self.solution_path if lv==l]
                if len(pts)>1: 
                    sol_colors = [config.COLOR_SOL_BFS, config.COLOR_SOL_DFS, config.COLOR_SOL_ASTAR]
                    arcade.draw_line_strip(pts, sol_colors[self.current_solver_idx], 2)
            if self.show_trace and len(self.path_history)>1:
                pts = [self.renderer.get_pixel(r,c,0.35,off) for (r,c),lv in self.path_history if lv==l]
                if len(pts)>1: arcade.draw_line_strip(pts, config.PATH_TRACE_COLOR, 1)
            if l==self.start_pos[2]: px,py = self.renderer.get_pixel(self.start_pos[0],self.start_pos[1],0.35,off); arcade.draw_circle_filled(px,py,4,config.TEXT_COLOR)
            if l==self.end_pos[2]: px,py = self.renderer.get_pixel(self.end_pos[0],self.end_pos[1],0.35,off); arcade.draw_circle_filled(px,py,4,config.GOAL_COLOR)
            if l==self.current_level and self.player_cell: px,py = self.renderer.get_pixel(self.player_cell.row,self.player_cell.column,0.35,off); arcade.draw_circle_filled(px,py,5,config.PLAYER_COLOR)

    def draw_minimap(self):
        if self.grid.levels <= 1: return
        x, y = config.SCREEN_WIDTH-40, config.SCREEN_HEIGHT-100; 
        bg_color = config.BG_COLOR + (120,)
        arcade.draw_lbwh_rectangle_filled(x-30, y-60, 60, 120, bg_color)
        for i in range(self.grid.levels): arcade.draw_lbwh_rectangle_filled(x-20, y-50+i*25, 40, 20, config.HIGHLIGHT_COLOR if i == self.current_level else (128, 128, 128, 150))

    def draw_victory(self):
        overlay_color = config.BG_COLOR + (230,)
        arcade.draw_lbwh_rectangle_filled(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT, overlay_color); cw, ch = config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2
        arcade.draw_text("CONGRATULATIONS!", cw, ch+120, config.HIGHLIGHT_COLOR, font_size=36, anchor_x="center", bold=True)
        lines, msg = [f"Time: {int(self.solve_duration)}s", f"Cells Visited: {len(self.cells_visited)}"], "PRESS ENTER TO RESTART"
        if self.mode == "ADVENTURE":
            engine = AdventureEngine(self.adventure_slot); level, exp, total = engine.data["skill_level"], engine.data["exp"], engine.data["total_mazes"]
            lines.append(f"ADVENTURE LVL: {level}"); lines.append(f"TOTAL EXP: {exp}"); lines.append(f"MAZES SOLVED: {total}"); msg = f"LEVEL COMPLETE! PRESS ENTER FOR NEXT CHALLENGE"
        lines.append(""); lines.append(msg)
        for i, line in enumerate(lines): arcade.draw_text(line, cw, ch+40-i*30, config.HIGHLIGHT_COLOR if "ENTER" in line else config.TEXT_COLOR, font_size=16, anchor_x="center")

    def on_draw(self):
        try:
            self.clear()
            if self.show_map: self.gui_camera.use(); self.draw_map_overlay(); return
            self.maze_camera.use()
            
            if self.generating:
                self.grid_shapes.draw()
                for cell in self.grid.each_cell():
                    cx, cy = self.renderer.get_pixel(cell.row, cell.column)
                    for link in cell.get_links():
                        if link.level == cell.level: lx, ly = self.renderer.get_pixel(link.row, link.column); arcade.draw_line(cx, cy, lx, ly, config.GENERATION_COLOR, 3)
            else:
                if len(self.wall_shapes_layers) > self.current_level: self.wall_shapes_layers[self.current_level].draw()
                if len(self.stair_shapes_layers) > self.current_level: self.stair_shapes_layers[self.current_level].draw()
                if self.show_solution and self.solution_path:
                    pts = [self.renderer.get_pixel(r,c) for r,c,lv in self.solution_path if lv==self.current_level]
                    if len(pts)>1: 
                        # Get current theme color for the solver
                        sol_colors = [config.COLOR_SOL_BFS, config.COLOR_SOL_DFS, config.COLOR_SOL_ASTAR]
                        color = sol_colors[self.current_solver_idx]
                        arcade.draw_line_strip(pts, color, 4)
                if self.show_trace and len(self.path_history)>1:
                    pts = [self.renderer.get_pixel(r,c) for (r,c),lv in self.path_history if lv==self.current_level]
                    if len(pts)>1: arcade.draw_line_strip(pts, config.PATH_TRACE_COLOR, 2)
                if self.current_level == self.end_pos[2]: gx, gy = self.renderer.get_pixel(self.end_pos[0], self.end_pos[1]); arcade.draw_circle_filled(gx, gy, self.renderer.cell_radius*0.4, config.GOAL_COLOR)
                self.player_list.draw()
            
            self.gui_camera.use()
            if self.generating: 
                if self.status_text: self.status_text.draw()
            else:
                hud_bg = config.BG_COLOR + (180,)
                arcade.draw_lbwh_rectangle_filled(0, config.SCREEN_HEIGHT-40, config.SCREEN_WIDTH, 40, hud_bg)
                if self.hud_text_1: self.hud_text_1.draw()
                if self.hud_stats: self.hud_stats.draw()
                if self.hud_text_2: self.hud_text_2.draw()
                self.draw_minimap()
                if self.current_stair_options and self.stair_prompt: self.stair_prompt.draw()
                if self.game_won: self.draw_victory()
        except Exception: traceback.print_exc()

    def on_update(self, delta_time: float):
        try:
            if self.generating:
                try: 
                    for _ in range(50): next(self.gen_iterator)
                except (StopIteration, TypeError): self.finish_generation()
                self.scroll_to_player(); return
            self.scroll_to_player()
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
                if self.show_trace and (not self.path_history or self.path_history[-1][0] != (r, c) or self.path_history[-1][1] != l): self.path_history.append(((r, c), l))
                self.current_stair_options = []
                for link in self.player_cell.get_links():
                    if link.level > l: self.current_stair_options.append((link.level, "U"))
                    elif link.level < l: self.current_stair_options.append((link.level, "D"))
                if self.stair_prompt: self.stair_prompt.text = f"STAIRS: Press {' / '.join(['['+o[1]+']' for o in self.current_stair_options])} to move" if self.current_stair_options else ""
            self.update_hud()
        except Exception: traceback.print_exc()

    def on_key_press(self, key: int, modifiers: int):
        if self.generating or (self.game_won and key != arcade.key.ENTER): return
        if self.game_won and key == arcade.key.ENTER:
            if self.mode == "ADVENTURE":
                engine = AdventureEngine(self.adventure_slot); diff = self.grid.levels * (self.grid.rows * self.grid.columns // 100)
                engine.process_result(self.solve_duration, self.step_count, self.used_solution, self.used_map, int(diff))
                params = engine.get_next_maze_params(); game = GameView(); game.setup(mode="ADVENTURE", adventure_slot=self.adventure_slot, **params); self.window.show_view(game)
            else: self.window.show_view(CreativeMenuView())
            return
        if key == arcade.key.M: self.show_map = not self.show_map; self.used_map = True if self.show_map else self.used_map; return
        if key == arcade.key.X:
            self.show_solution = not self.show_solution; self.used_solution = True if self.show_solution else self.used_solution
            if self.show_solution and self.grid: self.solving, self.sol_iterator = True, self.solvers[self.current_solver_idx][0].solve_step(self.grid, self.player_cell, self.grid.get_cell(*self.end_pos))
            return
        elif key == arcade.key.R: self.show_trace = not self.show_trace; return
        if self.show_map: return
        if key in [arcade.key.EQUAL, arcade.key.PLUS]: self.maze_camera.zoom = min(self.maze_camera.zoom + 0.1, 3.0); self.update_hud()
        elif key == arcade.key.MINUS: self.maze_camera.zoom = max(self.maze_camera.zoom - 0.1, 0.1); self.update_hud()
        elif key in [arcade.key.KEY_0, arcade.key.NUM_0]: self.maze_camera.zoom = 1.0; self.update_hud()
        dir_map = {arcade.key.UP:(0,1), arcade.key.DOWN:(0,-1), arcade.key.LEFT:(-1,0), arcade.key.RIGHT:(1,0), arcade.key.W:(0,1), arcade.key.S:(0,-1), arcade.key.A:(-1,0), arcade.key.D:(1,0)}
        if key in dir_map:
            dx_key, dy_key = dir_map[key]; best_n, best_score = None, -1.0
            if self.player_cell:
                px, py = self.renderer.get_pixel(self.player_cell.row, self.player_cell.column)
                for n in self.player_cell.get_links():
                    if n.level != self.player_cell.level: continue
                    nx, ny = self.renderer.get_pixel(n.row, n.column); dx_n, dy_n = nx-px, ny-py; mag = math.sqrt(dx_n*dx_n+dy_n*dy_n)
                    if mag == 0: continue
                    score = (dx_n/mag * dx_key) + (dy_n/mag * dy_key)
                    if score > 0.4 and score > best_score: best_score, best_n = score, n
                if best_n: self.player_cell, self.target_pos = best_n, self.renderer.get_pixel(best_n.row, best_n.column); self.step_count += 1
        elif key in [arcade.key.U, arcade.key.D]:
            td = "U" if key == arcade.key.U else "D"
            for lv, ds in self.current_stair_options:
                if ds == td and self.player_cell:
                    self.current_level = lv; target = self.grid.get_cell(self.player_cell.row, self.player_cell.column, lv) if self.grid else None
                    if target and self.player_cell.is_linked(target): self.player_cell = target; px, py = self.renderer.get_pixel(target.row, target.column); self.player_sprite.center_x, self.player_sprite.center_y = px, py; self.target_pos = (px, py); self.step_count += 1; self.update_hud(); break
        elif key == arcade.key.TAB:
            self.current_solver_idx = (self.current_solver_idx + 1) % len(self.solvers); self.update_hud()
            if self.show_solution and self.grid: self.solving, self.sol_iterator = True, self.solvers[self.current_solver_idx][0].solve_step(self.grid, self.player_cell, self.grid.get_cell(*self.end_pos))
        elif key == arcade.key.P: arcade.get_image().save("maze_export.png")
<<<<<<< Updated upstream
        elif key == arcade.key.ESCAPE: self.window.show_view(MenuView())
=======
        elif key == arcade.key.ESCAPE: self.window.show_view(ProfileSelectView() if self.mode == "ADVENTURE" else CreativeMenuView())
>>>>>>> Stashed changes
