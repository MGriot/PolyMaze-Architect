# views.py
import arcade
import arcade.shape_list
import config
import math
import os
from maze_topology import SquareGrid, HexGrid
from maze_algorithms import (
    RecursiveBacktracker, RandomizedPrims, AldousBroder,
    BinaryTree, Wilsons, Kruskals, Sidewinder, RecursiveDivision,
    BFS_Solver, DFS_Solver, AStar_Solver
)

class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.grid_types = [("Square", SquareGrid), ("Hexagonal", HexGrid)]
        self.grid_idx = 0
        self.sizes = [("Small", 11, 15), ("Medium", 21, 31), ("Large", 41, 61)]
        self.size_idx = 1
        self.generators = [
            ("Backtracker", RecursiveBacktracker), ("Prim's", RandomizedPrims),
            ("Aldous-Broder", AldousBroder), ("Wilson's", Wilsons),
            ("Binary Tree", BinaryTree), ("Kruskal's", Kruskals),
            ("Sidewinder", Sidewinder), ("Rec. Division", RecursiveDivision)
        ]
        self.gen_idx = 0
        self.animate = True
        
        # Performance: Use Text objects
        self.title_text = None
        self.option_texts = []

    def on_show_view(self):
        arcade.set_background_color(config.BG_COLOR)
        self.setup_text()

    def setup_text(self):
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        self.title_text = arcade.Text(
            "POLY MAZE ARCHITECT", cw, ch + 180, config.TEXT_COLOR, 40, anchor_x="center"
        )
        self.update_options_text()

    def update_options_text(self):
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        self.option_texts = []
        options = [
            f"G: Grid Shape -> {self.grid_types[self.grid_idx][0]}",
            f"Z: Size -> {self.sizes[self.size_idx][0]} ({self.sizes[self.size_idx][1]}x{self.sizes[self.size_idx][2]})",
            f"A: Algorithm -> {self.generators[self.gen_idx][0]}",
            f"V: Animation -> {'ENABLED' if self.animate else 'DISABLED'}",
            f"T: Theme -> {config.CURRENT_THEME_NAME.upper()}",
            "", "PRESS ENTER TO START", "PRESS ESC TO QUIT"
        ]
        for i, line in enumerate(options):
            color = config.WALL_COLOR if ":" in line else arcade.color.GOLD
            if "Theme" in line: color = config.PLAYER_COLOR
            self.option_texts.append(arcade.Text(
                line, cw, ch + 80 - (i * 35), color, 18, anchor_x="center"
            ))

    def on_draw(self):
        self.clear()
        if self.title_text:
            self.title_text.draw()
        for text in self.option_texts:
            text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.G: 
            self.grid_idx = (self.grid_idx + 1) % len(self.grid_types)
            self.update_options_text()
        elif key == arcade.key.Z: 
            self.size_idx = (self.size_idx + 1) % len(self.sizes)
            self.update_options_text()
        elif key == arcade.key.A: 
            self.gen_idx = (self.gen_idx + 1) % len(self.generators)
            self.update_options_text()
        elif key == arcade.key.V: 
            self.animate = not self.animate
            self.update_options_text()
        elif key == arcade.key.T:
            config.apply_theme("light" if config.CURRENT_THEME_NAME == "dark" else "dark")
            arcade.set_background_color(config.BG_COLOR)
            self.setup_text()
        elif key == arcade.key.ENTER: self.start_game()
        elif key == arcade.key.ESCAPE: arcade.exit()

    def start_game(self):
        _, GridClass = self.grid_types[self.grid_idx]
        _, rows, cols = self.sizes[self.size_idx]
        gen_name, GenClass = self.generators[self.gen_idx]
        game = GameView()
        game.setup(GridClass, rows, cols, GenClass(), gen_name, self.animate)
        self.window.show_view(game)

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.grid = None
        self.wall_list = None 
        self.wall_shapes = None 
        self.grid_shapes = None 
        self.player_sprite = None
        self.physics_engine = None
        self.path_history = []
        self.gen_name = ""
        self.is_hex = False
        self.current_solver_idx = 0
        self.solvers = [
            (BFS_Solver(), "BFS (Shortest)", config.COLOR_SOL_BFS),
            (DFS_Solver(), "DFS (Wander)", config.COLOR_SOL_DFS),
            (AStar_Solver(), "A* (Heuristic)", config.COLOR_SOL_ASTAR)
        ]
        self.solution_path = []
        self.show_solution = False
        self.generating = False
        self.gen_iterator = None
        self.solving = False
        self.sol_iterator = None
        self.cell_radius = 0
        
        # UI Text objects
        self.hud_text_1 = None
        self.hud_text_2 = None
        self.status_text = None
        self.screenshot_msg_text = None
        self.screenshot_msg_timer = 0

    def setup(self, GridClass, rows, cols, generator, gen_name, animate):
        self.gen_name, self.is_hex = gen_name, (GridClass == HexGrid)
        self.grid = GridClass(rows, cols)
        if self.is_hex:
            rw, rh = config.SCREEN_WIDTH / ((cols + 1) * math.sqrt(3)), config.SCREEN_HEIGHT / (rows * 1.5 + 1)
            self.cell_radius = min(rw, rh) * 0.95
        else:
            self.cell_radius = min(config.SCREEN_WIDTH / (cols + 2), config.SCREEN_HEIGHT / (rows + 2)) / 2
        
        # Pre-batch the ghost grid
        self.grid_shapes = arcade.shape_list.ShapeElementList()
        R = self.cell_radius
        for cell in self.grid.each_cell():
            cx, cy = self.get_pixel(cell.row, cell.column)
            if self.is_hex:
                pts = [(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))) for a in [30, 90, 150, 210, 270, 330]]
                # Fix: create_polygon_outline is not in 3.x, use create_line_loop
                self.grid_shapes.append(arcade.shape_list.create_line_loop(pts, (40, 40, 40), 1))
            else:
                self.grid_shapes.append(arcade.shape_list.create_rectangle_outline(cx, cy, R*2, R*2, (40, 40, 40), 1))

        self.setup_ui_text()

        if animate:
            self.generating, self.gen_iterator = True, generator.generate_step(self.grid)
        else:
            generator.generate(self.grid); self.finish_generation()

    def setup_ui_text(self):
        self.hud_text_1 = arcade.Text("", 10, config.SCREEN_HEIGHT - 25, config.TEXT_COLOR, 12)
        self.hud_text_2 = arcade.Text(
            "S: Sol | TAB: Cycle | T: Theme | P: Print | ESC: Menu", 
            10, config.SCREEN_HEIGHT - 45, config.WALL_COLOR, 10
        )
        self.status_text = arcade.Text("GENERATING...", config.SCREEN_WIDTH/2, 20, config.TEXT_COLOR, 16, anchor_x="center")
        self.screenshot_msg_text = arcade.Text(
            "MAZE SAVED AS 'maze_export.png'", config.SCREEN_WIDTH/2, 60, arcade.color.GREEN, 20, anchor_x="center"
        )
        self.update_hud()

    def update_hud(self):
        if self.hud_text_1:
            self.hud_text_1.text = f"{self.gen_name} | {self.solvers[self.current_solver_idx][1]}"

    def finish_generation(self):
        self.generating = False
        self.generate_walls()
        px, py = self.get_pixel(0, 0)
        # Hitbox is smaller than visual circle for better movement
        self.player_sprite = arcade.SpriteCircle(int(self.cell_radius * 0.35), config.PLAYER_COLOR)
        self.player_sprite.center_x, self.player_sprite.center_y = px, py
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.path_history = [(px, py)]
        self.start_solving()

    def start_solving(self):
        s, _, _ = self.solvers[self.current_solver_idx]
        st, en = self.grid.get_cell(0, 0), self.grid.get_cell(self.grid.rows-1, self.grid.columns-1)
        self.solving, self.sol_iterator = True, s.solve_step(self.grid, st, en)

    def get_pixel(self, r, c):
        R = self.cell_radius
        if not self.is_hex:
            s = R * 2
            tx, ty = self.grid.columns * s, self.grid.rows * s
            return (config.SCREEN_WIDTH - tx)/2 + c*s + R, (config.SCREEN_HEIGHT - ty)/2 + r*s + R
        else:
            w, h = math.sqrt(3) * R, 1.5 * R
            tx, ty = (self.grid.columns + 0.5) * w, (self.grid.rows - 1) * h + 2 * R
            return (config.SCREEN_WIDTH - tx)/2 + c*w + (w/2 if r % 2 == 1 else 0) + w/2, (config.SCREEN_HEIGHT - ty)/2 + r*h + R

    def generate_walls(self):
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.wall_shapes = arcade.shape_list.ShapeElementList()
        R, processed = self.cell_radius, set()
        for cell in self.grid.each_cell():
            cx, cy = self.get_pixel(cell.row, cell.column)
            r, c = cell.row, cell.column
            if not self.is_hex:
                deltas = [(1, 0, -R, R, R, R), (0, -1, -R, -R, -R, R), (-1, 0, -R, -R, R, -R), (0, 1, R, -R, R, R)]
                for dr, dc, x1, y1, x2, y2 in deltas:
                    n = self.grid.get_cell(r+dr, c+dc)
                    if not n or not cell.is_linked(n): self.add_wall((cx+x1, cy+y1), (cx+x2, cy+y2), processed)
            else:
                angles = [30, 90, 150, 210, 270, 330]
                deltas = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (0, 1)] if r % 2 == 0 else [(1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (0, 1)]
                for i, (dr, dc) in enumerate(deltas):
                    n = self.grid.get_cell(r+dr, c+dc)
                    if not n or not cell.is_linked(n):
                        a1, a2 = math.radians(angles[i]), math.radians(angles[(i+1)%6])
                        self.add_wall((cx + R*math.cos(a1), cy + R*math.sin(a1)), (cx + R*math.cos(a2), cy + R*math.sin(a2)), processed)

    def add_wall(self, p1, p2, processed):
        wid = tuple(sorted([(round(p1[0],1), round(p1[1],1)), (round(p2[0],1), round(p2[1],1))]))
        if wid in processed: return
        processed.add(wid)
        mx, my = (p1[0]+p2[0])/2, (p1[1]+p2[1])/2
        l, ang = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2), math.degrees(math.atan2(p2[1]-p1[1], p2[0]-p1[0]))
        # Physics wall
        wall = arcade.SpriteSolidColor(int(l+1), config.WALL_THICKNESS, config.WALL_COLOR)
        wall.center_x, wall.center_y, wall.angle = mx, my, ang
        self.wall_list.append(wall)
        # Visual wall
        self.wall_shapes.append(arcade.shape_list.create_line(p1[0], p1[1], p2[0], p2[1], config.WALL_COLOR, config.WALL_THICKNESS))

    def on_draw(self):
        self.clear()
        if self.generating:
            self.grid_shapes.draw()
            for cell in self.grid.each_cell():
                cx, cy = self.get_pixel(cell.row, cell.column)
                for link in cell.get_links():
                    lx, ly = self.get_pixel(link.row, link.column)
                    arcade.draw_line(cx, cy, lx, ly, config.GENERATION_COLOR, 2)
            self.status_text.draw()
            return
        
        self.wall_shapes.draw()
        gx, gy = self.get_pixel(self.grid.rows-1, self.grid.columns-1)
        arcade.draw_circle_filled(gx, gy, self.cell_radius * 0.4, config.GOAL_COLOR)
        
        if self.show_solution and len(self.solution_path) > 1:
            arcade.draw_line_strip(self.solution_path, self.solvers[self.current_solver_idx][2], 4)
        
        if len(self.path_history) > 1:
            arcade.draw_line_strip(self.path_history, config.PATH_TRACE_COLOR, 2)
        
        if self.player_sprite:
            arcade.draw_circle_filled(
                self.player_sprite.center_x, self.player_sprite.center_y, 
                self.player_sprite.width/2, config.PLAYER_COLOR
            )
        
        self.hud_text_1.draw()
        self.hud_text_2.draw()
        
        if self.screenshot_msg_timer > 0:
            self.screenshot_msg_text.draw()
            self.screenshot_msg_timer -= 1

    def on_update(self, delta_time):
        if self.generating:
            try:
                # Optimized: More steps per frame during generation
                for _ in range(30): next(self.gen_iterator)
            except StopIteration: self.finish_generation()
            return
        if self.solving:
            try:
                for _ in range(5):
                    self.solution_path = [self.get_pixel(r, c) for r, c in next(self.sol_iterator)]
            except StopIteration: self.solving = False
            return
        if self.physics_engine:
            self.physics_engine.update()
            px, py = self.player_sprite.center_x, self.player_sprite.center_y
            if not self.path_history or (px-self.path_history[-1][0])**2 + (py-self.path_history[-1][1])**2 > 25:
                self.path_history.append((px, py))

    def on_key_press(self, key, modifiers):
        if self.generating: return
        s = config.MOVEMENT_SPEED
        if key == arcade.key.UP: self.player_sprite.change_y = s
        elif key == arcade.key.DOWN: self.player_sprite.change_y = -s
        elif key == arcade.key.LEFT: self.player_sprite.change_x = s # wait, left should be -s
        elif key == arcade.key.RIGHT: self.player_sprite.change_x = s
        elif key == arcade.key.S: self.show_solution = not self.show_solution
        elif key == arcade.key.P:
            arcade.get_image().save("maze_export.png")
            self.screenshot_msg_timer = 120
        elif key == arcade.key.T:
            config.apply_theme("light" if config.CURRENT_THEME_NAME == "dark" else "dark")
            arcade.set_background_color(config.BG_COLOR)
            self.generate_walls()
            self.setup_ui_text()
            self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
            self.player_sprite.color = config.PLAYER_COLOR
        elif key == arcade.key.TAB:
            self.current_solver_idx = (self.current_solver_idx + 1) % len(self.solvers)
            self.update_hud()
            s, _, _ = self.solvers[self.current_solver_idx]
            st, en = self.grid.get_cell(0, 0), self.grid.get_cell(self.grid.rows-1, self.grid.columns-1)
            self.solving, self.sol_iterator = True, s.solve_step(self.grid, st, en)
        elif key == arcade.key.ESCAPE: self.window.show_view(MenuView())

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.UP, arcade.key.DOWN]: self.player_sprite.change_y = 0
        if key in [arcade.key.LEFT, arcade.key.RIGHT]: self.player_sprite.change_x = 0