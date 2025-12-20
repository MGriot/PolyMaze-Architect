# maze_algorithms.py
import random
import heapq
from collections import deque
from maze_topology import Grid, Cell
from typing import List, Tuple, Dict

# --- GENERATORS ---

class MazeGenerator:
    """Base interface for generators."""
    def generate(self, grid: Grid):
        """Run the full generation (blocking)."""
        for _ in self.generate_step(grid):
            pass

    def generate_step(self, grid: Grid):
        """Generator that yields progress for animation."""
        raise NotImplementedError

class RecursiveBacktracker(MazeGenerator):
    def generate_step(self, grid: Grid):
        start = grid.random_cell()
        stack = [start]
        visited = {start}

        while stack:
            current = stack[-1]
            unvisited_neighbors = [n for n in current.neighbors if not n.get_links()]
            
            if not unvisited_neighbors:
                stack.pop()
            else:
                neighbor = random.choice(unvisited_neighbors)
                current.link(neighbor)
                visited.add(neighbor)
                stack.append(neighbor)
                yield current, neighbor # Yield for animation

class RandomizedPrims(MazeGenerator):
    def generate_step(self, grid: Grid):
        visited = set()
        start = grid.random_cell()
        visited.add(start)
        frontier = list(start.neighbors)
        
        while frontier:
            cell = random.choice(frontier)
            frontier.remove(cell)
            if cell in visited: continue
            
            in_maze_neighbors = [n for n in cell.neighbors if n in visited]
            if in_maze_neighbors:
                neighbor = random.choice(in_maze_neighbors)
                cell.link(neighbor)
                visited.add(cell)
                for n in cell.neighbors:
                    if n not in visited and n not in frontier:
                        frontier.append(n)
                yield neighbor, cell

class AldousBroder(MazeGenerator):
    def generate_step(self, grid: Grid):
        cell = grid.random_cell()
        visited = {cell}
        unvisited_count = grid.size() - 1

        while unvisited_count > 0:
            neighbor = random.choice(cell.neighbors)
            if not neighbor.get_links():
                cell.link(neighbor)
                unvisited_count -= 1
                visited.add(neighbor)
                yield cell, neighbor
            cell = neighbor

class BinaryTree(MazeGenerator):
    """
    Very simple. For each cell, link either North or East.
    Creates a distinct diagonal bias.
    """
    def generate_step(self, grid: Grid):
        # We process cell by cell
        for cell in grid.each_cell():
            # Potential links (North or East for Square, similar for Hex)
            # To keep it generic, we pick the first two neighbors if they exist
            # but for Binary Tree it usually needs a consistent direction.
            # We'll use North (-1, 0) and East (0, 1) or equivalents.
            neighbors = []
            for n in cell.neighbors:
                if n.row < cell.row or (n.row == cell.row and n.column > cell.column):
                    neighbors.append(n)
            
            if neighbors:
                neighbor = random.choice(neighbors)
                cell.link(neighbor)
                yield cell, neighbor

class Wilsons(MazeGenerator):
    """
    Loop-erased random walks.
    Produces unbiased mazes.
    """
    def generate_step(self, grid: Grid):
        unvisited = list(grid.each_cell())
        start = random.choice(unvisited)
        unvisited.remove(start)
        visited = {start}

        while unvisited:
            cell = random.choice(unvisited)
            path = [cell]
            
            while cell not in visited:
                cell = random.choice(cell.neighbors)
                if cell in path:
                    # Loop detected, erase it
                    index = path.index(cell)
                    path = path[:index+1]
                else:
                    path.append(cell)
            
            # Add path to maze
            for i in range(len(path)-1):
                path[i].link(path[i+1])
                if path[i] in unvisited:
                    unvisited.remove(path[i])
                visited.add(path[i])
                yield path[i], path[i+1]

class Kruskals(MazeGenerator):
    """
    Randomized Kruskal's.
    Characteristic: Lots of short dead-ends, very "bony" look.
    """
    def generate_step(self, grid: Grid):
        # 1. Create sets for each cell
        parent = {cell: cell for cell in grid.each_cell()}
        
        def find(i):
            if parent[i] == i: return i
            parent[i] = find(parent[i])
            return parent[i]

        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j
                return True
            return False

        # 2. List of all possible unique edges (walls)
        edges = []
        for cell in grid.each_cell():
            for neighbor in cell.neighbors:
                if (neighbor, cell) not in edges:
                    edges.append((cell, neighbor))
        
        random.shuffle(edges)

        # 3. Process edges
        for u, v in edges:
            if union(u, v):
                u.link(v)
                yield u, v

class Sidewinder(MazeGenerator):
    """
    Row-based algorithm.
    Characteristic: No upward dead-ends.
    """
    def generate_step(self, grid: Grid):
        for row in range(grid.rows):
            run = []
            for col in range(grid.columns):
                cell = grid.get_cell(row, col)
                run.append(cell)

                at_eastern_boundary = (col == grid.columns - 1)
                at_northern_boundary = (row == grid.rows - 1)

                should_close_run = at_eastern_boundary or (not at_northern_boundary and random.randint(0, 1) == 0)

                if should_close_run:
                    member = random.choice(run)
                    north = grid.get_cell(member.row + 1, member.column)
                    if north:
                        member.link(north)
                        yield member, north
                    run = []
                else:
                    east = grid.get_cell(cell.row, cell.column + 1)
                    if east:
                        cell.link(east)
                        yield cell, east

class RecursiveDivision(MazeGenerator):
    """
    Chamber-based. Starts with empty space and adds walls.
    """
    def generate_step(self, grid: Grid):
        # First, link everything (remove all walls)
        for cell in grid.each_cell():
            for neighbor in cell.neighbors:
                cell.link(neighbor)

        def divide(r, c, h, w):
            if h <= 1 or w <= 1: return
            
            horizontal = random.choice([True, False]) if h != w else h > w
            
            if horizontal:
                # Horizontal wall
                wall_row = random.randint(r, r + h - 2)
                passage_col = random.randint(c, c + w - 1)
                
                for col in range(c, c + w):
                    if col != passage_col:
                        cell = grid.get_cell(wall_row, col)
                        south = grid.get_cell(wall_row + 1, col)
                        if cell and south: 
                            cell.unlink(south)
                            # yield cell, south # We yield unlinking (visually different)
                
                yield None, None # Signal a division happened
                yield from divide(r, c, wall_row - r + 1, w)
                yield from divide(wall_row + 1, c, r + h - wall_row - 1, w)
            else:
                # Vertical wall
                wall_col = random.randint(c, c + w - 2)
                passage_row = random.randint(r, r + h - 1)
                
                for row in range(r, r + h):
                    if row != passage_row:
                        cell = grid.get_cell(row, wall_col)
                        east = grid.get_cell(row, wall_col + 1)
                        if cell and east: 
                            cell.unlink(east)
                
                yield None, None
                yield from divide(r, c, h, wall_col - c + 1)
                yield from divide(r, wall_col + 1, h, c + w - wall_col - 1)

        yield from divide(0, 0, grid.rows, grid.columns)

# --- SOLVERS ---

class MazeSolver:
    """Base interface for solvers."""
    def solve(self, grid: Grid, start: Cell, goal: Cell) -> List[Tuple[int, int]]:
        for path in self.solve_step(grid, start, goal):
            pass
        return path

    def solve_step(self, grid: Grid, start: Cell, goal: Cell):
        """Yields the current exploration path or partial solution."""
        raise NotImplementedError
    
    def reconstruct_path(self, came_from: Dict[Cell, Cell], start: Cell, goal: Cell):
        path = []
        curr = goal
        while curr != start and curr is not None:
            path.append((curr.row, curr.column))
            curr = came_from.get(curr)
        path.append((start.row, start.column))
        path.reverse()
        return path

class BFS_Solver(MazeSolver):
    def solve_step(self, grid: Grid, start: Cell, goal: Cell):
        queue = deque([start])
        came_from = {start: None}
        
        while queue:
            current = queue.popleft()
            if current == goal: break
            
            for neighbor in current.get_links():
                if neighbor not in came_from:
                    came_from[neighbor] = current
                    queue.append(neighbor)
                    yield self.reconstruct_path(came_from, start, neighbor)
        yield self.reconstruct_path(came_from, start, goal)

class DFS_Solver(MazeSolver):
    def solve_step(self, grid: Grid, start: Cell, goal: Cell):
        stack = [start]
        came_from = {start: None}
        
        while stack:
            current = stack.pop()
            if current == goal: break
            
            for neighbor in current.get_links():
                if neighbor not in came_from:
                    came_from[neighbor] = current
                    stack.append(neighbor)
                    yield self.reconstruct_path(came_from, start, neighbor)
        yield self.reconstruct_path(came_from, start, goal)

class AStar_Solver(MazeSolver):
    def heuristic(self, a: Cell, b: Cell):
        return abs(a.row - b.row) + abs(a.column - b.column)

    def solve_step(self, grid: Grid, start: Cell, goal: Cell):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {start: None}
        g_score = {start: 0}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal: break
                
            for neighbor in current.get_links():
                new_g = g_score[current] + 1
                if neighbor not in g_score or new_g < g_score[neighbor]:
                    g_score[neighbor] = new_g
                    f_score = new_g + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))
                    came_from[neighbor] = current
                    yield self.reconstruct_path(came_from, start, neighbor)
        yield self.reconstruct_path(came_from, start, goal)