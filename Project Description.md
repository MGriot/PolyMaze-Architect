## Project Description: `PyMazeRunner v2.0`

### 1. Project Goal
To create a highly modular and extensible 2D maze game where users can select from various generation and solving algorithms at runtime. The project prioritizes a clean separation of concerns between the maze data structure (topology), the algorithms that operate on it, and the graphical representation (rendering).

### 2. Architecture: Strategy Pattern + Model-View
*   **Model:**
    *   **`maze_topology.py`:** Contains the fundamental graph-based data structures (`Cell`, `Grid`). This layer is agnostic to both shape and algorithms. It represents the "canvas."
    *   **`algorithms.py`:** Implements the **Strategy Pattern**. It defines `MazeGenerator` and `MazeSolver` abstract classes and provides multiple concrete implementations (e.g., `RecursiveBacktracker`, `AldousBroder`, `BFS`, `A*`). These are the "paintbrushes."
*   **View (`views.py`):**
    *   **`MenuView`:** Now acts as a configuration hub. The user selects which generator and solver "strategy" to use before starting the game.
    *   **`GameView`:** Is constructed with the chosen strategies. It is responsible for rendering the maze state provided by the Model and handling player input. It is completely decoupled from the specific algorithm implementations.
*   **Controller (`main.py` & `config.py`):** The entry point and settings configuration.

### 3. Key Algorithms Implemented
*   **Maze Generators:**
    1.  **Recursive Backtracker (DFS):** Creates mazes with long, winding corridors and low branching. (Already implemented, will be refactored).
    2.  **Aldous-Broder:** A "random walk" algorithm that produces a uniform spanning tree. Its mazes are unbiased but it is very slow to generate.
    3.  **Prim's Algorithm:** Tends to create mazes with many short dead-ends, giving it a very different feel from Recursive Backtracker.

*   **Pathfinding Solvers:**
    1.  **Breadth-First Search (BFS):** Guarantees finding the absolute shortest path in an unweighted grid. (Already implemented, will be refactored).
    2.  **A\* (A-Star):** A classic, efficient pathfinding algorithm that uses a heuristic (Manhattan distance) to intelligently search towards the goal, making it much faster than BFS on large mazes.

---

## The Refactored Codebase

Your directory structure will be updated to include the new `algorithms.py` file.

```
src/
   |-- main.py
   |-- config.py
   |-- maze_topology.py  (Updated)
   |-- maze_algorithms.py
   |-- views.py          (Heavily Updated)
```

### 1. `maze_topology.py` (Updated)
The `Cell` and `Grid` classes remain largely the same as the previous "Graph" version. We are only adding minor utility methods if needed. The core structure is already perfect for this task.

```python
# maze_topology.py
import random
from typing import List, Tuple, Dict, Optional

class Cell:
    """A generic node in the maze graph."""
    def __init__(self, row: int, column: int):
        self.row = row
        self.column = column
        self.links: Dict['Cell', bool] = {}
        self.neighbors: List['Cell'] = []

    def link(self, cell: 'Cell', bidi=True):
        self.links[cell] = True
        if bidi:
            cell.link(self, bidi=False)

    def is_linked(self, cell: 'Cell') -> bool:
        return cell in self.links

    def get_links(self) -> List['Cell']:
        return list(self.links.keys())

class Grid:
    """Abstract Base Class for any grid shape."""
    def __init__(self, rows: int, columns: int):
        self.rows = rows
        self.columns = columns
        self.grid = self._prepare_grid()
        self._configure_cells()
        self.start_cell = self.grid[0][0]
        self.end_cell = self.grid[self.rows - 1][self.columns - 1]

    def _prepare_grid(self) -> List[List[Cell]]:
        return [[Cell(r, c) for c in range(self.columns)] for r in range(self.rows)]

    def _configure_cells(self):
        raise NotImplementedError("Subclasses must implement this")

    def get_cell(self, row, col) -> Optional[Cell]:
        if 0 <= row < self.rows and 0 <= col < self.columns:
            return self.grid[row][col]
        return None
    
    def random_cell(self) -> Cell:
        r = random.randint(0, self.rows - 1)
        c = random.randint(0, self.columns - 1)
        return self.grid[r][c]

    def size(self) -> int:
        return self.rows * self.columns

    def each_cell(self):
        for row in self.grid:
            for cell in row:
                if cell: yield cell

class SquareGrid(Grid):
    """Concrete implementation for Square geometry."""
    def _configure_cells(self):
        for cell in self.each_cell():
            row, col = cell.row, cell.column
            north = self.get_cell(row - 1, col)
            south = self.get_cell(row + 1, col)
            east  = self.get_cell(row, col + 1)
            west  = self.get_cell(row, col - 1)
            
            # Filter out None values
            cell.neighbors = [n for n in [north, south, east, west] if n]

```

### 2. `algorithms.py` (New File)
This is the core of our new strategy pattern. It's pure logic, with no Arcade code.

```python
# algorithms.py
import abc
import random
import heapq
from maze_topology import Grid, Cell

# --- GENERATOR STRATEGIES ---

class MazeGenerator(abc.ABC):
    """Abstract interface for maze generation algorithms."""
    @abc.abstractmethod
    def generate(self, grid: Grid):
        pass

class RecursiveBacktracker(MazeGenerator):
    """Long, winding paths. Low "branchiness"."""
    def generate(self, grid: Grid):
        start_at = grid.random_cell()
        stack = [start_at]
        visited = {start_at}

        while stack:
            current = stack[-1]
            neighbors = [n for n in current.neighbors if n not in visited]
            
            if not neighbors:
                stack.pop()
            else:
                neighbor = random.choice(neighbors)
                current.link(neighbor)
                visited.add(neighbor)
                stack.append(neighbor)

class PrimsAlgorithm(MazeGenerator):
    """Many short dead-ends. High "branchiness"."""
    def generate(self, grid: Grid):
        start_at = grid.random_cell()
        active = [start_at]
        visited = {start_at}

        while active:
            current = random.choice(active)
            
            # Find neighbors that have been visited
            available_neighbors = [n for n in current.neighbors if n in visited]
            
            # Find neighbors that haven't been visited
            unvisited_neighbors = [n for n in current.neighbors if n not in visited]

            if unvisited_neighbors:
                neighbor_to_link = random.choice(available_neighbors)
                current.link(neighbor_to_link)

                new_neighbor = random.choice(unvisited_neighbors)
                current.link(new_neighbor)
                visited.add(new_neighbor)
                active.append(new_neighbor)
            else:
                active.remove(current)

class AldousBroder(MazeGenerator):
    """Unbiased, but very slow. A 'random walk'."""
    def generate(self, grid: Grid):
        cell = grid.random_cell()
        unvisited = grid.size() - 1

        while unvisited > 0:
            neighbor = random.choice(cell.neighbors)
            if not neighbor.get_links():
                cell.link(neighbor)
                unvisited -= 1
            cell = neighbor

# --- SOLVER STRATEGIES ---

class MazeSolver(abc.ABC):
    @abc.abstractmethod
    def solve(self, grid: Grid, start: Cell, end: Cell):
        pass

class BFSSolver(MazeSolver):
    """Guarantees the shortest path."""
    def solve(self, grid: Grid, start: Cell, end: Cell):
        came_from = {start: None}
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            if current == end: break
            for neighbor in current.get_links():
                if neighbor not in came_from:
                    came_from[neighbor] = current
                    queue.append(neighbor)
        return self._reconstruct_path(came_from, start, end)

    def _reconstruct_path(self, came_from, start, end):
        path = []
        curr = end
        while curr != start and curr is not None:
            path.append((curr.row, curr.column))
            curr = came_from.get(curr)
        path.append((start.row, start.column))
        return path[::-1]

class AStarSolver(MazeSolver):
    """Efficient heuristic search. Finds the shortest path."""
    def solve(self, grid: Grid, start: Cell, end: Cell):
        
        def heuristic(cell1: Cell, cell2: Cell):
            # Manhattan distance
            return abs(cell1.row - cell2.row) + abs(cell1.column - cell2.column)

        open_set = [(0, start)] # (f_score, cell)
        heapq.heapify(open_set)
        
        came_from = {start: None}
        g_score = {cell: float('inf') for cell in grid.each_cell()}
        g_score[start] = 0

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end:
                return self._reconstruct_path(came_from, start, end)

            for neighbor in current.get_links():
                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score, neighbor))
        return [] # No path found

    def _reconstruct_path(self, came_from, start, end):
        # Same helper as BFS
        path = []
        curr = end
        while curr != start and curr is not None:
            path.append((curr.row, curr.column))
            curr = came_from.get(curr)
        path.append((start.row, start.column))
        return path[::-1]
```

### 3. `views.py` (Heavily Updated)
The `MenuView` is now a selector, and `GameView` accepts the chosen algorithms in its constructor.

```python
# views.py
import arcade
import config
from maze_topology import SquareGrid
import algorithms

class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.generators = [
            ("Recursive Backtracker", algorithms.RecursiveBacktracker),
            ("Prim's Algorithm", algorithms.PrimsAlgorithm),
            ("Aldous-Broder", algorithms.AldousBroder),
        ]
        self.solvers = [
            ("Breadth-First Search (BFS)", algorithms.BFSSolver),
            ("A* Search", algorithms.AStarSolver)
        ]
        self.gen_index = 0
        self.sol_index = 0

    def on_show_view(self):
        arcade.set_background_color(config.COLOR_WALL)

    def on_draw(self):
        self.clear()
        cy = config.SCREEN_HEIGHT / 2
        
        arcade.draw_text("MAZE ALGORITHM SELECTOR", config.SCREEN_WIDTH / 2, cy + 150,
                         arcade.color.WHITE, font_size=40, anchor_x="center")

        # Generator selection
        arcade.draw_text("Generator: (G to cycle)", config.SCREEN_WIDTH / 2, cy + 50,
                         arcade.color.GRAY, font_size=18, anchor_x="center")
        arcade.draw_text(self.generators[self.gen_index][0], config.SCREEN_WIDTH / 2, cy + 20,
                         arcade.color.WHITE, font_size=24, anchor_x="center")

        # Solver selection
        arcade.draw_text("Solver: (S to cycle)", config.SCREEN_WIDTH / 2, cy - 50,
                         arcade.color.GRAY, font_size=18, anchor_x="center")
        arcade.draw_text(self.solvers[self.sol_index][0], config.SCREEN_WIDTH / 2, cy - 80,
                         arcade.color.WHITE, font_size=24, anchor_x="center")
        
        arcade.draw_text("Press ENTER to Generate", config.SCREEN_WIDTH / 2, cy - 180,
                         arcade.color.GREEN, font_size=20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.G:
            self.gen_index = (self.gen_index + 1) % len(self.generators)
        elif key == arcade.key.S:
            self.sol_index = (self.sol_index + 1) % len(self.solvers)
        elif key == arcade.key.ENTER:
            # Instantiate the chosen strategies
            selected_generator = self.generators[self.gen_index][1]()
            selected_solver = self.solvers[self.sol_index][1]()
            
            # Pass them to the GameView
            game_view = GameView(selected_generator, selected_solver)
            game_view.setup()
            self.window.show_view(game_view)

class GameView(arcade.View):
    # This class remains identical to the "Graph-based" version, with one key change:
    def __init__(self, generator: algorithms.MazeGenerator, solver: algorithms.MazeSolver):
        super().__init__()
        # Store the passed-in strategy objects
        self.generator = generator
        self.solver = solver
        
        # ... (rest of __init__ is the same: self.grid=None, etc.)
        self.grid = None
        self.player_pos = [0, 0]
        self.wall_list = None
        self.player_sprite = None
        self.path_history = []
        self.solution_path = []
        self.show_solution = False
        self.physics_engine = None

    def setup(self):
        arcade.set_background_color(config.BG_COLOR)
        self.grid = SquareGrid(config.ROWS, config.COLS)
        
        # --- DECOUPLED ALGORITHM EXECUTION ---
        # Use the strategy object to generate the maze
        self.generator.generate(self.grid)
        
        # Use the strategy object to solve it
        start_cell = self.grid.start_cell
        end_cell = self.grid.end_cell
        self.solution_path_coords = self.solver.solve(self.grid, start_cell, end_cell)
        # ------------------------------------
        
        # The rest of setup is purely for rendering and physics, it does not change.
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.create_walls_from_graph()
        
        start_x, start_y = self.get_pixel_coords(0, 0)
        self.player_sprite = arcade.SpriteSolidColor(config.CELL_SIZE - 10, config.CELL_SIZE - 10, config.PLAYER_COLOR)
        self.player_sprite.center_x = start_x
        self.player_sprite.center_y = start_y
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.path_history = [(start_x, start_y)]

    # ... The rest of GameView (on_draw, on_update, get_pixel_coords, etc.) is
    # ... completely identical to the previous version. It does not need to be changed.
    # ... This proves the power of the architecture.
    def get_pixel_coords(self, row, col):
        x = col * config.CELL_SIZE + config.CELL_SIZE / 2 + 50
        y = row * config.CELL_SIZE + config.CELL_SIZE / 2 + 50
        return x, y

    def create_walls_from_graph(self):
        cs = config.CELL_SIZE
        wt = config.WALL_THICKNESS
        for cell in self.grid.each_cell():
            cx, cy = self.get_pixel_coords(cell.row, cell.column)
            if not cell.is_linked(self.grid.get_cell(cell.row - 1, cell.column)): # North wall
                wall = arcade.SpriteSolidColor(cs + wt, wt, config.WALL_COLOR)
                wall.center_x = cx
                wall.center_y = cy - cs / 2
                self.wall_list.append(wall)
            if not cell.is_linked(self.grid.get_cell(cell.row, cell.column - 1)): # West wall
                wall = arcade.SpriteSolidColor(wt, cs + wt, config.WALL_COLOR)
                wall.center_x = cx - cs / 2
                wall.center_y = cy
                self.wall_list.append(wall)
        
        # Draw bounding box
        top_y = (self.grid.rows - 1) * cs + cs / 2 + 50
        right_x = (self.grid.columns - 1) * cs + cs / 2 + 50
        arcade.draw_line(50 - cs/2, 50 - cs/2, right_x + cs/2, 50 - cs/2, config.WALL_COLOR, wt) # Bottom
        arcade.draw_line(right_x + cs/2, 50 - cs/2, right_x + cs/2, top_y + cs/2, config.WALL_COLOR, wt) # Right

    def on_draw(self):
        self.clear()
        self.wall_list.draw()
        if self.show_solution:
            pixel_sol = [self.get_pixel_coords(r, c) for r, c in self.solution_path_coords]
            if len(pixel_sol) > 1:
                arcade.draw_line_strip(pixel_sol, config.SOLUTION_COLOR, 3)
        if len(self.path_history) > 1:
            arcade.draw_line_strip(self.path_history, config.PATH_TRACE_COLOR, 2)
        self.player_sprite.draw()
        ex, ey = self.get_pixel_coords(config.ROWS - 1, config.COLS - 1)
        arcade.draw_rectangle_filled(ex, ey, config.CELL_SIZE/2, config.CELL_SIZE/2, config.GOAL_COLOR)
        arcade.draw_text(f"Path Length: {len(self.path_history)}", 10, config.SCREEN_HEIGHT - 30, arcade.color.WHITE, 14)
        arcade.draw_text("S: Solution | Arrows: Move | ESC: Menu", 10, config.SCREEN_HEIGHT - 50, arcade.color.WHITE, 14)
    
    def on_update(self, delta_time):
        self.physics_engine.update()
        cx, cy = self.player_sprite.center_x, self.player_sprite.center_y
        if len(self.path_history) == 0 or ((cx - self.path_history[-1][0])**2 + (cy - self.path_history[-1][1])**2) > 25:
             self.path_history.append((cx, cy))
    
    def on_key_press(self, key, modifiers):
        s = config.MOVEMENT_SPEED
        if key == arcade.key.UP: self.player_sprite.change_y = s
        elif key == arcade.key.DOWN: self.player_sprite.change_y = -s
        elif key == arcade.key.LEFT: self.player_sprite.change_x = -s
        elif key == arcade.key.RIGHT: self.player_sprite.change_x = s
        elif key == arcade.key.S: self.show_solution = not self.show_solution
        elif key == arcade.key.ESCAPE:
            menu = MenuView()
            self.window.show_view(menu)

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.UP, arcade.key.DOWN]: self.player_sprite.change_y = 0
        if key in [arcade.key.LEFT, arcade.key.RIGHT]: self.player_sprite.change_x = 0
```

### 4. `config.py` and `main.py`
These files remain unchanged from the previous "Graph-based" version.

