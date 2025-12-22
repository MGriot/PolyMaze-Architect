# views.py
import arcade
import arcade.shape_list
import config
import math
import os
import random
import time
import traceback
from maze_topology import SquareCellGrid, HexCellGrid, TriCellGrid, PolarCellGrid
from maze_algorithms import (
    RecursiveBacktracker, RandomizedPrims, AldousBroder,
    BinaryTree, Wilsons, Kruskals, Sidewinder, RecursiveDivision,
    HuntAndKill, Ellers,
    BFS_Solver, DFS_Solver, AStar_Solver
)

class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.cell_types = [("Square", SquareCellGrid), ("Hexagonal", HexCellGrid), ("Triangular", TriCellGrid), ("Polar", PolarCellGrid)]
        self.cell_idx = 0
        self.shapes = ["rectangle", "circle", "triangle", "hexagon"]
        self.shape_idx = 0
        self.sizes = [("Small", 11, 15), ("Medium", 21, 31), ("Large", 31, 41)]
        self.size_idx = 1
        self.generators = [
            ("Backtracker", RecursiveBacktracker), ("Prim's", RandomizedPrims),
            ("Aldous-Broder", AldousBroder), ("Wilson's", Wilsons),
            ("Binary Tree", BinaryTree), ("Kruskal's", Kruskals),
            ("Sidewinder", Sidewinder), ("Rec. Division", RecursiveDivision),
            ("Hunt & Kill", HuntAndKill), ("Eller's", Ellers)
        ]
        self.gen_idx = 0
        self.animate = True
        self.multi_path = False
        self.levels = 1
        self.show_trace = True
        self.random_endpoints = False
        
        self.title_text = None
        self.option_texts = []
        self.footer_texts = []

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
        try:
            self.clear()
            if self.title_text: self.title_text.draw()
            for text in self.option_texts: text.draw()
        except Exception:
            traceback.print_exc()

    def on_key_press(self, key, modifiers):
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
            arcade.set_background_color(config.BG_COLOR)
            self.setup_ui()
        elif key == arcade.key.ENTER: self.start_game(); changed = False
        elif key == arcade.key.ESCAPE: arcade.exit(); changed = False
        else: changed = False
        
        if changed: self.update_options()

    def start_game(self):
        _, GridClass = self.cell_types[self.cell_idx]
        shape = self.shapes[self.shape_idx]
        _, rows, cols = self.sizes[self.size_idx]
        gen_name, GenClass = self.generators[self.gen_idx]
        game = GameView()
        braid = 0.5 if self.multi_path else 0.0
        game.setup(GridClass, shape, rows, cols, self.levels, GenClass(), gen_name, self.animate, braid, self.show_trace, self.random_endpoints)
        self.window.show_view(game)

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.grid = None
        self.wall_list_layers = [] 
        self.wall_shapes_layers = [] 
        self.stair_shapes_layers = [] 
        self.grid_shapes = None 
        self.player_sprite = None
        self.player_cell = None # Track cell instead of physics
        self.target_pos = None # For smooth animation
        self.current_level = 0
        self.grid_type = "rect"
        self.braid_pct = 0.0
        self.path_history = [] 
        self.show_trace = True
        self.current_solver_idx = 0
        self.solvers = [(BFS_Solver(), "BFS", config.COLOR_SOL_BFS), (DFS_Solver(), "DFS", config.COLOR_SOL_DFS), (AStar_Solver(), "A*", config.COLOR_SOL_ASTAR)]
        self.solution_path = [] 
        self.show_solution, self.solving = False, False
        self.sol_iterator, self.gen_iterator = None, None
        self.generating = False
        self.cell_radius = 0
        self.hud_text_1, self.hud_text_2, self.status_text = None, None, None
        self.stair_prompt = None
        self.current_stair_options = []
        self.top_margin, self.bottom_margin = 80, 60
        self.show_map = False
        self.map_wall_shapes = [] 
        self.map_stair_shapes = []
        self.start_time, self.solve_duration, self.game_won = 0, 0, False
        self.cells_visited = set()

    def setup(self, GridClass, shape, rows, cols, levels, generator, gen_name, animate, braid_pct, show_trace, random_endpoints):
        self.gen_name, self.braid_pct = gen_name, braid_pct
        self.grid = GridClass(rows, cols, levels)
        self.grid.mask_shape(shape)
        
        if GridClass == HexCellGrid: self.grid_type = "hex"
        elif GridClass == TriCellGrid: self.grid_type = "tri"
        elif GridClass == PolarCellGrid: self.grid_type = "polar"
        else: self.grid_type = "rect"
        
        self.show_trace, self.current_level, self.path_history, self.solution_path, self.show_map, self.game_won = show_trace, 0, [], [], False, False
        self.cells_visited = set()
        
        avail_h = config.SCREEN_HEIGHT - self.top_margin - self.bottom_margin
        if self.grid_type == "hex":
            self.cell_radius = min((config.SCREEN_WIDTH-150)/((cols+1)*math.sqrt(3)), avail_h/(rows*1.5+1)) * 0.95
        elif self.grid_type == "tri":
            self.cell_radius = min((config.SCREEN_WIDTH-150)/(cols*math.sqrt(3)/2 + 1), avail_h/(rows*1.5 + 1)) * 0.9
        elif self.grid_type == "polar":
             self.cell_radius = min((config.SCREEN_WIDTH-100)/2, (avail_h)/2) / (rows + 3) / 1.5
        else:
            self.cell_radius = min((config.SCREEN_WIDTH-150)/(cols+2), avail_h/(rows+2)) / 2
        
        self.grid_shapes = arcade.shape_list.ShapeElementList()
        R = self.cell_radius
        for cell in self.grid.each_cell():
            if cell.level == 0:
                cx, cy = self.get_pixel(cell.row, cell.column)
                if self.grid_type == "hex":
                    pts = [(cx + R*math.cos(math.radians(a)), cy + R*math.sin(math.radians(a))) for a in [30, 90, 150, 210, 270, 330]]
                    self.grid_shapes.append(arcade.shape_list.create_line_loop(pts, (40, 40, 40), 1))
                elif self.grid_type == "tri":
                    pts = self._get_tri_verts(cell.row, cell.column, cx, cy, R)
                    self.grid_shapes.append(arcade.shape_list.create_line_loop(pts, (40, 40, 40), 1))
                elif self.grid_type == "rect":
                    self.grid_shapes.append(arcade.shape_list.create_rectangle_outline(cx, cy, R*2, R*2, (40, 40, 40), 1))

        self.setup_ui_text()
        
        valid_cells = list(self.grid.each_cell())
        if valid_cells:
            if random_endpoints:
                s_cell, e_cell = random.sample(valid_cells, 2) if len(valid_cells) > 1 else (valid_cells[0], valid_cells[0])
                self.start_pos = (s_cell.row, s_cell.column, s_cell.level)
                self.end_pos = (e_cell.row, e_cell.column, e_cell.level)
            else:
                valid_cells.sort(key=lambda c: (c.level, c.row, c.column))
                s_cell, e_cell = valid_cells[0], valid_cells[-1]
                self.start_pos = (s_cell.row, s_cell.column, s_cell.level)
                self.end_pos = (e_cell.row, e_cell.column, e_cell.level)
        else:
            self.start_pos, self.end_pos = (0,0,0), (0,0,0)

        if animate:
            self.generating, self.gen_iterator = True, generator.generate_step(self.grid)
        else:
            generator.generate(self.grid)
            if self.braid_pct > 0: self.grid.braid(self.braid_pct)
            self.finish_generation()

    def setup_ui_text(self):
        self.hud_text_1 = arcade.Text("", 20, config.SCREEN_HEIGHT - 35, config.TEXT_COLOR, font_size=14, bold=True)
        self.hud_text_2 = arcade.Text("S: Sol | TAB: AI | M: Architectural Map | P: Print | ESC: Menu", 20, config.SCREEN_HEIGHT - 60, config.WALL_COLOR, font_size=11)
        self.status_text = arcade.Text("GENERATING...", config.SCREEN_WIDTH/2, 30, config.TEXT_COLOR, font_size=16, anchor_x="center")
        self.stair_prompt = arcade.Text("", config.SCREEN_WIDTH/2, 30, arcade.color.CYAN, font_size=18, anchor_x="center", bold=True)
        self.update_hud()

    def update_hud(self):
        l_str = f"Floor {self.current_level+1}/{self.grid.levels}" if self.grid.levels > 1 else ""
        self.hud_text_1.text = f"{self.gen_name.upper()} ARCHITECT | {l_str}"

    def get_pixel(self, r, c, scale=1.0, offset=(0,0)):
        R = self.cell_radius * scale
        ox, oy = config.SCREEN_WIDTH / 2 + offset[0], (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2 + offset[1]

        if self.grid_type == "hex":
            w, h = math.sqrt(3) * R, 1.5 * R
            start_x, start_y = ox - (self.grid.columns + 0.5) * w / 2, oy - ((self.grid.rows - 1) * h + 2 * R) / 2
            return start_x + c*w + (w/2 if r % 2 == 1 else 0) + w/2, start_y + r*h + R
            
        elif self.grid_type == "tri":
            s, h = R * math.sqrt(3), 1.5 * R
            start_x, start_y = ox - self.grid.columns * (s/4) - s/4, oy - (self.grid.rows * h) / 2
            cx, cy = start_x + c * (s/2) + s/2, start_y + r * h + R
            if (r + c) % 2 != 0: cy += R/2 # Inverted center shift
            return cx, cy

        elif self.grid_type == "polar":
            rw = R * 1.5
            radius = (rw * 2) + r * rw + rw/2
            angle = (c * (2 * math.pi / self.grid.columns)) - math.pi / 2
            return ox + radius * math.cos(angle), oy + radius * math.sin(angle)

        else: # rect
            s = R * 2
            start_x, start_y = ox - (self.grid.columns * s)/2, oy - (self.grid.rows * s)/2
            return start_x + c*s + R, start_y + r*s + R

    def _get_tri_verts(self, r, c, cx, cy, R):
        s = R * math.sqrt(3)
        if (r + c) % 2 == 0: # Upright
            return (cx, cy + R), (cx + s/2, cy - R/2), (cx - s/2, cy - R/2)
        else: # Inverted
            return (cx, cy - R), (cx + s/2, cy + R/2), (cx - s/2, cy + R/2)

    def generate_walls(self):
        self.wall_shapes_layers = [arcade.shape_list.ShapeElementList() for _ in range(self.grid.levels)]
        R = self.cell_radius
        for l in range(self.grid.levels):
            processed = set()
            for cell in self.grid.each_cell():
                if cell.level != l: continue
                r, c = cell.row, cell.column
                cx, cy = self.get_pixel(r, c)
                if self.grid_type == "rect":
                    deltas = [(1, 0, -R, R, R, R), (0, -1, -R, -R, -R, R), (-1, 0, -R, -R, R, -R), (0, 1, R, -R, R, R)]
                    for dr, dc, x1, y1, x2, y2 in deltas:
                        n = self.grid.get_cell(r+dr, c+dc, l)
                        if not n or not cell.is_linked(n): self.add_wall((cx+x1, cy+y1), (cx+x2, cy+y2), processed, l)
                elif self.grid_type == "hex":
                    angles, deltas = [30, 90, 150, 210, 270, 330], ([(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (0, 1)] if r % 2 == 0 else [(1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (0, 1)])
                    for i, (dr, dc) in enumerate(deltas):
                        n = self.grid.get_cell(r+dr, c+dc, l)
                        if not n or not cell.is_linked(n):
                            a1, a2 = math.radians(angles[i]), math.radians(angles[(i+1)%6])
                            self.add_wall((cx+R*math.cos(a1), cy+R*math.sin(a1)), (cx+R*math.cos(a2), cy+R*math.sin(a2)), processed, l)
                elif self.grid_type == "tri":
                    p1, p2, p3 = self._get_tri_verts(r, c, cx, cy, R)
                    if (r + c) % 2 == 0:
                        edges = [(p2, p3, (1, 0)), (p1, p2, (0, 1)), (p1, p3, (0, -1))]
                    else:
                        edges = [(p2, p3, (-1, 0)), (p1, p2, (0, 1)), (p1, p3, (0, -1))]
                    for v1, v2, (dr, dc) in edges:
                        n = self.grid.get_cell(r+dr, c+dc, l)
                        if not n or not cell.is_linked(n): self.add_wall(v1, v2, processed, l)
                elif self.grid_type == "polar":
                    rw = R * 1.5
                    ir, or_ = (rw * 2) + r * rw, (rw * 2) + (r + 1) * rw
                    step = 2 * math.pi / self.grid.columns
                    ts, te = c * step - math.pi/2, (c + 1) * step - math.pi/2
                    ox, oy = config.SCREEN_WIDTH / 2, (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2
                    n = self.grid.get_cell(r-1, c, l)
                    if r == 0 or (not n or not cell.is_linked(n)):
                         self.add_wall((ox + ir*math.cos(ts), oy + ir*math.sin(ts)), (ox + ir*math.cos(te), oy + ir*math.sin(te)), processed, l)
                    n = self.grid.get_cell(r+1, c, l)
                    if not n or not cell.is_linked(n):
                         self.add_wall((ox + or_*math.cos(ts), oy + or_*math.sin(ts)), (ox + or_*math.cos(te), oy + or_*math.sin(te)), processed, l)
                    n = self.grid.get_cell(r, (c-1)%self.grid.columns, l)
                    if not n or not cell.is_linked(n):
                         self.add_wall((ox + ir*math.cos(ts), oy + ir*math.sin(ts)), (ox + or_*math.cos(ts), oy + or_*math.sin(ts)), processed, l)

    def finish_generation(self):
        try:
            if self.braid_pct > 0: self.grid.braid(self.braid_pct)
            self.generating = False
            self.generate_walls()
            self.generate_stairs_visuals()
            self.generate_map_shapes()
            sr, sc, sl = self.start_pos
            self.player_cell = self.grid.get_cell(sr, sc, sl)
            px, py = self.get_pixel(sr, sc)
            self.player_sprite = arcade.SpriteCircle(int(self.cell_radius * 0.3), config.PLAYER_COLOR)
            self.player_sprite.center_x, self.player_sprite.center_y = px, py
            self.target_pos = (px, py)
            self.path_history = [((px, py), sl)]
            self.start_time = time.time()
            self.cells_visited.add((sr, sc, sl))
            self.update_hud()
        except Exception: traceback.print_exc()

    def add_wall(self, p1, p2, processed, level):
        wid = tuple(sorted([(round(p1[0],2), round(p1[1],2)), (round(p2[0],2), round(p2[1],2))]))
        if wid in processed: return
        processed.add(wid)
        self.wall_shapes_layers[level].append(arcade.shape_list.create_line(p1[0], p1[1], p2[0], p2[1], config.WALL_COLOR, config.WALL_THICKNESS))

    def generate_stairs_visuals(self):
        self.stair_shapes_layers = [arcade.shape_list.ShapeElementList() for _ in range(self.grid.levels)]
        for l in range(self.grid.levels):
            for r in range(self.grid.rows):
                for c in range(self.grid.columns):
                    cell = self.grid.get_cell(r, c, l)
                    if not cell: continue
                    cx, cy = self.get_pixel(r, c)
                    for link in cell.get_links():
                        if link.level > cell.level:
                            self.stair_shapes_layers[l].append(arcade.shape_list.create_polygon([(cx, cy+8), (cx-8, cy-6), (cx+8, cy-6)], arcade.color.AZURE))
                        elif link.level < cell.level:
                            self.stair_shapes_layers[l].append(arcade.shape_list.create_polygon([(cx, cy-8), (cx-8, cy+6), (cx+8, cy+6)], arcade.color.BROWN))

    def generate_map_shapes(self):
        self.map_wall_shapes = [arcade.shape_list.ShapeElementList() for _ in range(self.grid.levels)]
        self.map_stair_shapes = [arcade.shape_list.ShapeElementList() for _ in range(self.grid.levels)]
        m_scale, v_gap = 0.35, config.SCREEN_HEIGHT * 0.22
        
        # Adjust scale for large polar/tri grids if needed
        if self.grid_type == "polar": m_scale = 0.25

        for l in range(self.grid.levels):
            off = (0, (l - (self.grid.levels-1)/2) * v_gap)
            for cell in self.grid.each_cell():
                if cell.level != l: continue
                r, c = cell.row, cell.column
                cx, cy = self.get_pixel(r, c, m_scale, off)
                R = self.cell_radius * m_scale
                
                if self.grid_type == "rect":
                    deltas = [(1, 0, -R, R, R, R), (0, -1, -R, -R, -R, R), (-1, 0, -R, -R, R, -R), (0, 1, R, -R, R, R)]
                    for dr, dc, x1, y1, x2, y2 in deltas:
                        neighbor = self.grid.get_cell(r+dr, c+dc, l)
                        if not neighbor or not cell.is_linked(neighbor):
                            self.map_wall_shapes[l].append(arcade.shape_list.create_line(cx+x1, cy+y1, cx+x2, cy+y2, config.WALL_COLOR, 1))
                            
                elif self.grid_type == "hex":
                    angles, deltas = [30, 90, 150, 210, 270, 330], ([(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (0, 1)] if r % 2 == 0 else [(1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (0, 1)])
                    for i, (dr, dc) in enumerate(deltas):
                        neighbor = self.grid.get_cell(r+dr, c+dc, l)
                        if not neighbor or not cell.is_linked(neighbor):
                            a1, a2 = math.radians(angles[i]), math.radians(angles[(i+1)%6])
                            self.map_wall_shapes[l].append(arcade.shape_list.create_line(cx+R*math.cos(a1), cy+R*math.sin(a1), cx+R*math.cos(a2), cy+R*math.sin(a2), config.WALL_COLOR, 1))

                elif self.grid_type == "tri":
                    p1, p2, p3 = self._get_tri_verts(r, c, cx, cy, R)
                    if (r + c) % 2 == 0: # Upright
                        edges = [(p2, p3, (1, 0)), (p1, p2, (0, 1)), (p1, p3, (0, -1))]
                    else: # Inverted
                        edges = [(p2, p3, (-1, 0)), (p1, p2, (0, 1)), (p1, p3, (0, -1))]
                    for v1, v2, (dr, dc) in edges:
                        n = self.grid.get_cell(r+dr, c+dc, l)
                        if not n or not cell.is_linked(n):
                            self.map_wall_shapes[l].append(arcade.shape_list.create_line(v1[0], v1[1], v2[0], v2[1], config.WALL_COLOR, 1))

                elif self.grid_type == "polar":
                    rw = R * 1.5
                    # Note: R here is already scaled by m_scale because get_pixel uses it.
                    # Wait, self.cell_radius is NOT scaled in generate_map_shapes local variables usually.
                    # R = self.cell_radius * m_scale. This is correct.
                    # But ir, or_ logic needs to match the polar radius logic.
                    # Hole is 2 rings wide.
                    ir, or_ = (rw * 2) + r * rw, (rw * 2) + (r + 1) * rw
                    step = 2 * math.pi / self.grid.columns
                    ts, te = c * step - math.pi/2, (c + 1) * step - math.pi/2
                    # ox, oy for map
                    ox, oy = config.SCREEN_WIDTH / 2 + off[0], (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2 + off[1]
                    
                    n = self.grid.get_cell(r-1, c, l)
                    if r == 0 or (not n or not cell.is_linked(n)):
                         self.map_wall_shapes[l].append(arcade.shape_list.create_line(ox + ir*math.cos(ts), oy + ir*math.sin(ts), ox + ir*math.cos(te), oy + ir*math.sin(te), config.WALL_COLOR, 1))
                    n = self.grid.get_cell(r+1, c, l)
                    if not n or not cell.is_linked(n):
                         self.map_wall_shapes[l].append(arcade.shape_list.create_line(ox + or_*math.cos(ts), oy + or_*math.sin(ts), ox + or_*math.cos(te), oy + or_*math.sin(te), config.WALL_COLOR, 1))
                    n = self.grid.get_cell(r, (c-1)%self.grid.columns, l)
                    if not n or not cell.is_linked(n):
                         self.map_wall_shapes[l].append(arcade.shape_list.create_line(ox + ir*math.cos(ts), oy + ir*math.sin(ts), ox + or_*math.cos(ts), oy + or_*math.sin(ts), config.WALL_COLOR, 1))

                for link in cell.get_links():
                        if link.level != cell.level:
                            col = arcade.color.AZURE if link.level > cell.level else arcade.color.BROWN
                            self.map_stair_shapes[l].append(arcade.shape_list.create_rectangle_filled(cx, cy, 4, 4, col))

    def draw_map_overlay(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT, (0,0,0,235))
        arcade.draw_text("EXPLODED ARCHITECTURAL VIEW", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT-40, arcade.color.CYAN, font_size=20, anchor_x="center", bold=True)
        m_scale, v_gap = 0.35, config.SCREEN_HEIGHT * 0.22
        for l in range(self.grid.levels):
            off = (0, (l - (self.grid.levels-1)/2) * v_gap)
            p_center = self.get_pixel(self.grid.rows//2, self.grid.columns//2, m_scale, off)
            fw, fh = (self.grid.columns+1)*self.cell_radius*2*m_scale, (self.grid.rows+1)*self.cell_radius*2*m_scale
            arcade.draw_lbwh_rectangle_filled(p_center[0]-fw/2, p_center[1]-fh/2, fw, fh, (50, 50, 50, 100))
            self.map_wall_shapes[l].draw(); self.map_stair_shapes[l].draw()
            p_lab = self.get_pixel(self.grid.rows-1, 0, m_scale, off)
            arcade.draw_text(f"FLOOR {l+1}", p_lab[0], p_lab[1]+10, arcade.color.CYAN if l == self.current_level else arcade.color.GRAY, font_size=12)
            if l == self.current_level:
                px, py = self.get_pixel(self.get_grid_pos(self.player_sprite.center_x, self.player_sprite.center_y)[0], self.get_grid_pos(self.player_sprite.center_x, self.player_sprite.center_y)[1], m_scale, off)
                arcade.draw_circle_filled(px, py, 5, config.PLAYER_COLOR)

    def draw_minimap(self):
        if self.grid.levels <= 1: return
        x, y = config.SCREEN_WIDTH - 40, config.SCREEN_HEIGHT - 100
        arcade.draw_lbwh_rectangle_filled(x-30, y-60, 60, 120, (0, 0, 0, 120))
        start_y = y - (self.grid.levels * 25) / 2 + 10
        for i in range(self.grid.levels):
            color = arcade.color.CYAN if i == self.current_level else (100, 100, 100, 150)
            arcade.draw_lbwh_rectangle_filled(x-20, start_y + i*25 - 10, 40, 20, color)
            arcade.draw_text(f"F{i+1}", x, start_y + i*25, arcade.color.WHITE, font_size=10, anchor_x="center", anchor_y="center")
            if i == self.grid.levels - 1: arcade.draw_circle_filled(x + 12, start_y + i*25 + 5, 3, config.GOAL_COLOR)

    def draw_victory(self):
        arcade.draw_lbwh_rectangle_filled(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT, (0,0,0,200))
        cw, ch = config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2
        arcade.draw_text("CONGRATULATIONS!", cw, ch + 80, arcade.color.GOLD, font_size=36, anchor_x="center", bold=True)
        stats = [f"Time: {int(self.solve_duration)}s", f"Cells: {len(self.cells_visited)}", f"Complexity: {self.grid.size()}", "", "PRESS ENTER TO RESTART"]
        for i, line in enumerate(stats):
            arcade.draw_text(line, cw, ch - 20 - (i*30), config.HIGHLIGHT_COLOR if "ENTER" in line else config.TEXT_COLOR, font_size=16, anchor_x="center")

    def on_draw(self):
        try:
            self.clear()
            if self.generating:
                self.grid_shapes.draw()
                for cell in self.grid.each_cell():
                    cx, cy = self.get_pixel(cell.row, cell.column)
                    for link in cell.get_links():
                        if link.level == cell.level:
                            lx, ly = self.get_pixel(link.row, link.column)
                            arcade.draw_line(cx, cy, lx, ly, config.GENERATION_COLOR, 2)
                self.status_text.draw(); return
            if self.show_map: self.draw_map_overlay(); return
            self.wall_shapes_layers[self.current_level].draw()
            self.stair_shapes_layers[self.current_level].draw()
            if self.show_solution and self.solution_path:
                pts = []
                for r, c, l in self.solution_path:
                    if l == self.current_level: pts.append(self.get_pixel(r, c))
                    else:
                        if len(pts) > 1: arcade.draw_line_strip(pts, self.solvers[self.current_solver_idx][2], 4)
                        pts = []
                if len(pts) > 1: arcade.draw_line_strip(pts, self.solvers[self.current_solver_idx][2], 4)
            if self.show_trace and len(self.path_history) > 1:
                pts = [p for p, l in self.path_history if l == self.current_level]
                if len(pts) > 1: arcade.draw_line_strip(pts, config.PATH_TRACE_COLOR, 2)
            if self.current_level == self.end_pos[2]:
                gx, gy = self.get_pixel(self.end_pos[0], self.end_pos[1])
                arcade.draw_circle_filled(gx, gy, self.cell_radius * 0.4, config.GOAL_COLOR)
            if self.player_sprite: arcade.draw_circle_filled(self.player_sprite.center_x, self.player_sprite.center_y, self.player_sprite.width/2, config.PLAYER_COLOR)
            self.hud_text_1.draw(); self.hud_text_2.draw(); self.draw_minimap()
            if self.current_stair_options: self.stair_prompt.draw()
            if self.game_won: self.draw_victory()
        except Exception: traceback.print_exc()

    def on_update(self, delta_time):
        try:
            if self.generating:
                try:
                    for _ in range(50): next(self.gen_iterator)
                except StopIteration: self.finish_generation()
                return
            if self.game_won: return
            if self.solving and self.sol_iterator:
                try:
                    for _ in range(5): self.solution_path = next(self.sol_iterator)
                except StopIteration: self.solving = False
            
            # Smooth movement interpolation
            if self.player_sprite and self.target_pos:
                dx, dy = self.target_pos[0] - self.player_sprite.center_x, self.target_pos[1] - self.player_sprite.center_y
                self.player_sprite.center_x += dx * 0.3
                self.player_sprite.center_y += dy * 0.3
                
            if self.player_cell:
                r, c, l = self.player_cell.row, self.player_cell.column, self.player_cell.level
                self.cells_visited.add((r, c, l))
                if (r, c, l) == self.end_pos:
                    self.game_won, self.solve_duration = True, time.time() - self.start_time; return
                
                if self.show_trace and (not self.path_history or (self.player_sprite.center_x-self.path_history[-1][0][0])**2 + (self.player_sprite.center_y-self.path_history[-1][0][1])**2 > 25):
                    self.path_history.append(((self.player_sprite.center_x, self.player_sprite.center_y), self.current_level))
                
                self.current_stair_options = []
                for link in self.player_cell.get_links():
                    if link.level > l: self.current_stair_options.append((link.level, "U"))
                    elif link.level < l: self.current_stair_options.append((link.level, "D"))
                self.stair_prompt.text = f"STAIRS: Press {' / '.join(['['+o[1]+']' for o in self.current_stair_options])} to move" if self.current_stair_options else ""
        except Exception: traceback.print_exc()

    def get_grid_pos(self, x, y):
        R = self.cell_radius
        ox = config.SCREEN_WIDTH / 2
        oy = (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2
        
        if self.grid_type == "hex":
            w, h = math.sqrt(3) * R, 1.5 * R
            grid_w = (self.grid.columns + 0.5) * w
            grid_h = (self.grid.rows-1) * h + 2*R
            start_x, start_y = ox - grid_w/2, oy - grid_h/2
            r = int((y - start_y - R) / h + 0.5)
            c = int((x - start_x - (w/2 if r % 2 == 1 else 0) - w/2) / w + 0.5)
            return max(0, min(r, self.grid.rows-1)), max(0, min(c, self.grid.columns-1))
            
        elif self.grid_type == "tri":
            h = R * math.sqrt(3)
            w = R
            grid_w = (self.grid.columns + 1) * w / 2
            grid_h = self.grid.rows * h
            start_x, start_y = ox - grid_w/2, oy - grid_h/2
            r = int((y - start_y) / h)
            c = int((x - start_x) / (w/2))
            return max(0, min(r, self.grid.rows-1)), max(0, min(c, self.grid.columns-1))
            
        elif self.grid_type == "polar":
             dx, dy = x - ox, y - oy
             dist = math.sqrt(dx*dx + dy*dy)
             ring_width = R * 1.5
             r = int(dist / ring_width)
             if r >= self.grid.rows: r = self.grid.rows - 1
             
             angle = math.atan2(dy, dx) + math.pi/2
             if angle < 0: angle += 2*math.pi
             angle_step = 2 * math.pi / self.grid.columns
             c = int(angle / angle_step) % self.grid.columns
             return r, c

        else: # rect
            s = R * 2
            grid_w, grid_h = self.grid.columns * s, self.grid.rows * s
            start_x, start_y = ox - grid_w/2, oy - grid_h/2
            r = int((y - start_y) // s)
            c = int((x - start_x) // s)
            return max(0, min(r, self.grid.rows-1)), max(0, min(c, self.grid.columns-1))

    def on_key_press(self, key, modifiers):
        if self.generating or self.game_won:
            if self.game_won and key == arcade.key.ENTER: self.window.show_view(MenuView())
            return
        if key == arcade.key.M: self.show_map = not self.show_map; return
        if self.show_map: return
        
        # Logical direction mapping for any topology
        dir_map = {arcade.key.UP: (0, 1), arcade.key.DOWN: (0, -1), arcade.key.LEFT: (-1, 0), arcade.key.RIGHT: (1, 0)}
        if key in dir_map:
            dx_key, dy_key = dir_map[key]
            best_n, best_score = None, -1.0
            px, py = self.get_pixel(self.player_cell.row, self.player_cell.column)
            for n in self.player_cell.get_links():
                if n.level != self.player_cell.level: continue
                nx, ny = self.get_pixel(n.row, n.column)
                dx_n, dy_n = nx - px, ny - py
                mag = math.sqrt(dx_n*dx_n + dy_n*dy_n)
                if mag == 0: continue
                # Dot product score for alignment with key direction
                score = (dx_n/mag * dx_key) + (dy_n/mag * dy_key)
                if score > 0.5 and score > best_score:
                    best_score, best_n = score, n
            if best_n:
                self.player_cell = best_n
                self.target_pos = self.get_pixel(best_n.row, best_n.column)

        elif key in [arcade.key.U, arcade.key.D]:
            td = "U" if key == arcade.key.U else "D"
            for lv, ds in self.current_stair_options:
                if ds == td:
                    self.current_level = lv
                    target = self.grid.get_cell(self.player_cell.row, self.player_cell.column, lv)
                    if target and self.player_cell.is_linked(target):
                        self.player_cell = target
                        px, py = self.get_pixel(target.row, target.column)
                        self.player_sprite.center_x, self.player_sprite.center_y = px, py
                        self.target_pos = (px, py)
                        self.update_hud(); break
        elif key == arcade.key.S:
            self.show_solution = not self.show_solution
            if self.show_solution:
                self.solving, self.sol_iterator = True, self.solvers[self.current_solver_idx][0].solve_step(self.grid, self.grid.get_cell(*self.start_pos), self.grid.get_cell(*self.end_pos))
        elif key == arcade.key.TAB:
            self.current_solver_idx = (self.current_solver_idx + 1) % len(self.solvers); self.update_hud()
            if self.show_solution: self.solving, self.sol_iterator = True, self.solvers[self.current_solver_idx][0].solve_step(self.grid, self.grid.get_cell(*self.start_pos), self.grid.get_cell(*self.end_pos))
        elif key == arcade.key.P: arcade.get_image().save("maze_export.png")
        elif key == arcade.key.ESCAPE: self.window.show_view(MenuView())

    def on_key_release(self, key, modifiers):
        pass
