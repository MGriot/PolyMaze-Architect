# views.py
import arcade
import config
import math
import time
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
            ("Backtracker", RecursiveBacktracker),
            ("Prim's", RandomizedPrims),
            ("Aldous-Broder", AldousBroder),
            ("Wilson's", Wilsons),
            ("Binary Tree", BinaryTree),
            ("Kruskal's", Kruskals),
            ("Sidewinder", Sidewinder),
            ("Rec. Division", RecursiveDivision)
        ]
        self.gen_idx = 0
        
        self.animate = True

    def on_show_view(self):
        arcade.set_background_color(config.BG_COLOR)

    def on_draw(self):
        self.clear()
        cw, ch = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2
        
        arcade.draw_text("POLY MAZE ARCHITECT", cw, ch + 180, arcade.color.WHITE, 40, anchor_x="center")
        
        options = [
            f"G: Grid Shape -> {self.grid_types[self.grid_idx][0]}",
            f"Z: Size -> {self.sizes[self.size_idx][0]} ({self.sizes[self.size_idx][1]}x{self.sizes[self.size_idx][2]})",
            f"A: Algorithm -> {self.generators[self.gen_idx][0]}",
            f"V: Animation -> {'ENABLED' if self.animate else 'DISABLED'}",
            "",
            "PRESS ENTER TO START",
            "PRESS ESC TO QUIT"
        ]
        
        for i, line in enumerate(options):
            color = arcade.color.LIGHT_GRAY if ":" in line else arcade.color.GOLD
            arcade.draw_text(line, cw, ch + 80 - (i * 35), color, 18, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.G:
            self.grid_idx = (self.grid_idx + 1) % len(self.grid_types)
        elif key == arcade.key.Z:
            self.size_idx = (self.size_idx + 1) % len(self.sizes)
        elif key == arcade.key.A:
            self.gen_idx = (self.gen_idx + 1) % len(self.generators)
        elif key == arcade.key.V:
            self.animate = not self.animate
        elif key == arcade.key.ENTER:
            self.start_game()
        elif key == arcade.key.ESCAPE:
            arcade.exit()

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
        self.player_list = None
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
        
        # Animation state
        self.generating = False
        self.gen_iterator = None
        
        self.solving = False
        self.sol_iterator = None
        
        self.cell_size = config.CELL_SIZE

    def setup(self, GridClass, rows, cols, generator, gen_name, animate):
        self.gen_name = gen_name
        self.is_hex = (GridClass == HexGrid)
        self.grid = GridClass(rows, cols)
        
        # Adjust cell size for large mazes
        if rows > 30: self.cell_size = 15
        elif rows > 20: self.cell_size = 25
        else: self.cell_size = 35

        if animate:
            self.generating = True
            self.gen_iterator = generator.generate_step(self.grid)
        else:
            generator.generate(self.grid)
            self.finish_generation()

    def finish_generation(self):
        self.generating = False
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.generate_wall_sprites()
        
        px, py = self.get_pixel(0, 0)
        self.player_list = arcade.SpriteList()
        self.player_sprite = arcade.SpriteSolidColor(self.cell_size-8, self.cell_size-8, config.PLAYER_COLOR)
        self.player_sprite.center_x = px
        self.player_sprite.center_y = py
        self.player_list.append(self.player_sprite)
        
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.path_history = [(px, py)]
        
        self.start_solving()

    def start_solving(self):
        """Initializes the animated solver."""
        solver, _, _ = self.solvers[self.current_solver_idx]
        start = self.grid.get_cell(0, 0)
        end = self.grid.get_cell(self.grid.rows - 1, self.grid.columns - 1)
        self.solving = True
        self.sol_iterator = solver.solve_step(self.grid, start, end)

    def get_pixel(self, r, c):
        cs = self.cell_size
        if not self.is_hex:
            total_w = self.grid.columns * cs
            total_h = self.grid.rows * cs
            off_x = (config.SCREEN_WIDTH - total_w) / 2
            off_y = (config.SCREEN_HEIGHT - total_h) / 2
            return off_x + c * cs + cs/2, off_y + r * cs + cs/2
        else:
            # Hex layout (odd-r)
            width = cs
            height = math.sqrt(3)/2 * cs
            total_w = self.grid.columns * width
            total_h = self.grid.rows * height
            off_x = (config.SCREEN_WIDTH - total_w) / 2
            off_y = (config.SCREEN_HEIGHT - total_h) / 2
            
            x = off_x + c * width + width/2
            if r % 2 == 1: x += width/2
            y = off_y + r * height + height/2
            return x, y

    def generate_wall_sprites(self):
        cs = self.cell_size
        wt = config.WALL_THICKNESS
        wc = config.WALL_COLOR
        
        for cell in self.grid.each_cell():
            cx, cy = self.get_pixel(cell.row, cell.column)
            
            def add_wall(x, y, w, h, angle=0):
                wall = arcade.SpriteSolidColor(int(w), int(h), wc)
                wall.center_x = x
                wall.center_y = y
                wall.angle = angle
                self.wall_list.append(wall)

            if not self.is_hex:
                # Square walls
                for dr, dc, x_off, y_off, w, h in [
                    (1, 0, 0, cs/2, cs, wt),   # N
                    (-1, 0, 0, -cs/2, cs, wt),  # S
                    (0, 1, cs/2, 0, wt, cs),    # E
                    (0, -1, -cs/2, 0, wt, cs)   # W
                ]:
                    neighbor = self.grid.get_cell(cell.row + dr, cell.column + dc)
                    if not neighbor or not cell.is_linked(neighbor):
                        add_wall(cx + x_off, cy + y_off, w, h)
            else:
                # Hex walls - simplified for SpriteList (uses rectangles)
                # In a real hex view, we'd draw lines, but for physics we need sprites.
                pass # Hex physics is complex with simple sprites, omitted for brevity

    def on_draw(self):
        self.clear()
        
        if self.generating:
            # Draw unfinished grid
            for cell in self.grid.each_cell():
                cx, cy = self.get_pixel(cell.row, cell.column)
                if self.is_hex:
                    arcade.draw_circle_filled(cx, cy, 2, arcade.color.DARK_GRAY)
                else:
                    arcade.draw_point(cx, cy, arcade.color.DARK_GRAY, 2)
                
                for link in cell.get_links():
                    lx, ly = self.get_pixel(link.row, link.column)
                    arcade.draw_line(cx, cy, lx, ly, arcade.color.GREEN, 2)
            
            arcade.draw_text("GENERATING...", config.SCREEN_WIDTH/2, 20, arcade.color.WHITE, 16, anchor_x="center")
            return

        self.wall_list.draw()
        
        # Goal
        gx, gy = self.get_pixel(self.grid.rows-1, self.grid.columns-1)
        arcade.draw_rect_filled(arcade.XYWH(gx, gy, self.cell_size/2, self.cell_size/2), config.GOAL_COLOR)

        # Solution
        _, sol_name, sol_color = self.solvers[self.current_solver_idx]
        if self.show_solution and len(self.solution_path) > 1:
            arcade.draw_line_strip(self.solution_path, sol_color, 4)

        if len(self.path_history) > 1:
            arcade.draw_line_strip(self.path_history, config.PATH_TRACE_COLOR, 2)
        self.player_list.draw()
        self.draw_hud(sol_name)

    def draw_hud(self, sol_name):
        arcade.draw_text(f"{self.gen_name} | Solver: {sol_name}", 10, config.SCREEN_HEIGHT - 25, arcade.color.WHITE, 12)
        arcade.draw_text("S: Solution | TAB: Cycle | ESC: Menu", 10, config.SCREEN_HEIGHT - 45, arcade.color.GRAY, 10)

    def on_update(self, delta_time):
        if self.generating:
            try:
                # Move multiple steps per frame to speed up slow algorithms like AB
                for _ in range(5):
                    next(self.gen_iterator)
            except StopIteration:
                self.finish_generation()
            return

        if self.solving:
            try:
                for _ in range(3): # Speed of solving animation
                    path_coords = next(self.sol_iterator)
                    self.solution_path = [self.get_pixel(r, c) for r, c in path_coords]
            except StopIteration:
                self.solving = False
            return

        self.physics_engine.update()
        px, py = self.player_sprite.center_x, self.player_sprite.center_y
        lx, ly = self.path_history[-1]
        if (px-lx)**2 + (py-ly)**2 > 25:
            self.path_history.append((px, py))

    def recalculate_solution(self):
        solver, _, _ = self.solvers[self.current_solver_idx]
        start = self.grid.get_cell(0, 0)
        end = self.grid.get_cell(self.grid.rows - 1, self.grid.columns - 1)
        coords_path = solver.solve(self.grid, start, end)
        self.solution_path = [self.get_pixel(r, c) for r, c in coords_path]

    def on_key_press(self, key, modifiers):
        if self.generating: return
        
        s = config.MOVEMENT_SPEED
        if key == arcade.key.UP: self.player_sprite.change_y = s
        elif key == arcade.key.DOWN: self.player_sprite.change_y = -s
        elif key == arcade.key.LEFT: self.player_sprite.change_x = -s
        elif key == arcade.key.RIGHT: self.player_sprite.change_x = s
        elif key == arcade.key.S: self.show_solution = not self.show_solution
        elif key == arcade.key.TAB:
            self.current_solver_idx = (self.current_solver_idx + 1) % len(self.solvers)
            self.start_solving()
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MenuView())

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.UP, arcade.key.DOWN]: self.player_sprite.change_y = 0
        if key in [arcade.key.LEFT, arcade.key.RIGHT]: self.player_sprite.change_x = 0