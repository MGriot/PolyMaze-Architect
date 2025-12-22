# maze_algorithms.py
import random
import heapq
from collections import deque
from maze_topology import Grid, Cell
from typing import List, Tuple, Dict

# --- GENERATORS ---

class MazeGenerator:
    def generate(self, grid: Grid):
        for _ in self.generate_step(grid): pass
    def generate_step(self, grid: Grid):
        raise NotImplementedError

class RecursiveBacktracker(MazeGenerator):
    def generate_step(self, grid: Grid):
        start = grid.random_cell()
        stack = [start]
        visited = {start}
        while stack:
            current = stack[-1]
            unvisited_neighbors = [n for n in current.active_neighbors if not n.get_links()]
            if not unvisited_neighbors: stack.pop()
            else:
                neighbor = random.choice(unvisited_neighbors)
                current.link(neighbor)
                visited.add(neighbor)
                stack.append(neighbor)
                yield current, neighbor

class RandomizedPrims(MazeGenerator):
    def generate_step(self, grid: Grid):
        visited = {grid.random_cell()}
        frontier = []
        for v in visited:
            for n in v.active_neighbors: frontier.append((v, n))
        while frontier:
            prev, cell = frontier.pop(random.randrange(len(frontier)))
            if cell in visited: continue
            prev.link(cell)
            visited.add(cell)
            for n in cell.active_neighbors:
                if n not in visited: frontier.append((cell, n))
            yield prev, cell

class AldousBroder(MazeGenerator):
    def generate_step(self, grid: Grid):
        cell = grid.random_cell()
        unvisited = grid.size() - 1
        while unvisited > 0:
            neighbor = random.choice(cell.active_neighbors)
            if not neighbor.get_links():
                cell.link(neighbor)
                unvisited -= 1
                yield cell, neighbor
            cell = neighbor

class BinaryTree(MazeGenerator):
    def generate_step(self, grid: Grid):
        for cell in grid.each_cell():
            neighbors = [n for n in cell.active_neighbors if (n.level == cell.level and (n.row < cell.row or (n.row == cell.row and n.column > cell.column)))]
            if neighbors:
                cell.link(random.choice(neighbors))
                yield cell, None
            elif grid.levels > 1:
                # Vertical bias if no 2D neighbors
                above = grid.get_cell(cell.row, cell.column, cell.level + 1)
                if above: cell.link(above); yield cell, above

class Wilsons(MazeGenerator):
    def generate_step(self, grid: Grid):
        unvisited = list(grid.each_cell())
        visited = {unvisited.pop(random.randrange(len(unvisited)))}
        while unvisited:
            cell = random.choice(unvisited)
            path = [cell]
            while cell not in visited:
                cell = random.choice(cell.active_neighbors)
                if cell in path: path = path[:path.index(cell)+1]
                else: path.append(cell)
            for i in range(len(path)-1):
                path[i].link(path[i+1])
                if path[i] in unvisited: unvisited.remove(path[i])
                visited.add(path[i]); yield path[i], path[i+1]

class Kruskals(MazeGenerator):
    def generate_step(self, grid: Grid):
        parent = {cell: cell for cell in grid.each_cell()}
        def find(i):
            if parent[i] == i: return i
            parent[i] = find(parent[i]); return parent[i]
        edges = []
        for cell in grid.each_cell():
            for n in cell.active_neighbors:
                if id(cell) < id(n): edges.append((cell, n))
        random.shuffle(edges)
        for u, v in edges:
            root_u, root_v = find(u), find(v)
            if root_u != root_v:
                parent[root_u] = root_v
                u.link(v); yield u, v

class Sidewinder(MazeGenerator):
    def generate_step(self, grid: Grid):
        for l in range(grid.levels):
            for r in range(grid.rows):
                run = []
                for c in range(grid.columns):
                    cell = grid.get_cell(r, c, l)
                    run.append(cell)
                    if c == grid.columns - 1 or (r < grid.rows - 1 and random.randint(0, 1) == 0):
                        member = random.choice(run)
                        north = grid.get_cell(member.row + 1, member.column, l)
                        if north: member.link(north); yield member, north
                        elif l < grid.levels - 1:
                            above = grid.get_cell(member.row, member.column, l+1)
                            if above: member.link(above); yield member, above
                        run = []
                    else:
                        east = grid.get_cell(r, c + 1, l)
                        if east: cell.link(east); yield cell, east

class HuntAndKill(MazeGenerator):
    def generate_step(self, grid: Grid):
        current = grid.random_cell()
        while current:
            unvisited_neighbors = [n for n in current.active_neighbors if not n.get_links()]
            if unvisited_neighbors:
                neighbor = random.choice(unvisited_neighbors)
                current.link(neighbor)
                yield current, neighbor
                current = neighbor
            else:
                current = None
                for cell in grid.each_cell():
                    visited_neighbors = [n for n in cell.active_neighbors if n.get_links()]
                    if not cell.get_links() and visited_neighbors:
                        current = cell
                        neighbor = random.choice(visited_neighbors)
                        current.link(neighbor)
                        yield current, neighbor
                        break

class Ellers(MazeGenerator):
    def generate_step(self, grid: Grid):
        # Works best on 2D, but we'll iterate levels too
        for l in range(grid.levels):
            row_sets = {} # cell -> set_id
            next_set_id = 0
            
            for r in range(grid.rows):
                row_cells = [grid.get_cell(r, c, l) for c in range(grid.columns)]
                # 1. Initialize
                for cell in row_cells:
                    if cell not in row_sets:
                        row_sets[cell] = next_set_id
                        next_set_id += 1
                
                # 2. Merge Right
                for c in range(grid.columns - 1):
                    cell = row_cells[c]
                    next_cell = row_cells[c+1]
                    if row_sets[cell] != row_sets[next_cell]:
                        if r == grid.rows - 1 or random.choice([True, False]):
                            cell.link(next_cell)
                            old_set, new_set = row_sets[next_cell], row_sets[cell]
                            # Merge sets - naive linear scan is fine for these sizes
                            for k, v in list(row_sets.items()):
                                if v == old_set: row_sets[k] = new_set
                            yield cell, next_cell
                
                # 3. Vertical (Down)
                if r < grid.rows - 1:
                    sets = {}
                    for cell in row_cells:
                        sid = row_sets[cell]
                        if sid not in sets: sets[sid] = []
                        sets[sid].append(cell)
                    
                    for sid, cells in sets.items():
                        random.shuffle(cells)
                        count = 0
                        for cell in cells:
                            # At least one per set, then random
                            if count == 0 or random.choice([True, False]):
                                bottom = grid.get_cell(r+1, cell.column, l)
                                if bottom:
                                    cell.link(bottom)
                                    row_sets[bottom] = sid
                                    yield cell, bottom
                                    count += 1
            
            # Link levels (basic vertical shaft)
            if l < grid.levels - 1:
                u = grid.get_cell(random.randint(0, grid.rows-1), random.randint(0, grid.columns-1), l)
                v = grid.get_cell(u.row, u.column, l+1)
                if u and v:
                    u.link(v); yield u, v

class RecursiveDivision(MazeGenerator):
    def generate_step(self, grid: Grid):
        for cell in grid.each_cell():
            for n in cell.active_neighbors: cell.link(n)
        def divide(r, c, h, w, l):
            if h <= 1 or w <= 1: return
            if random.choice([True, False]) if h != w else h > w:
                wall_r, pass_c = random.randint(r, r+h-2), random.randint(c, c+w-1)
                for col in range(c, c+w):
                    if col != pass_c:
                        u, v = grid.get_cell(wall_r, col, l), grid.get_cell(wall_r+1, col, l)
                        if u and v: u.unlink(v)
                yield None, None
                yield from divide(r, c, wall_r-r+1, w, l)
                yield from divide(wall_r+1, c, r+h-wall_r-1, w, l)
            else:
                wall_c, pass_r = random.randint(c, c+w-2), random.randint(r, r+h-1)
                for row in range(r, r+h):
                    if row != pass_r:
                        u, v = grid.get_cell(row, wall_c, l), grid.get_cell(row, wall_c+1, l)
                        if u and v: u.unlink(v)
                yield None, None
                yield from divide(r, c, h, wall_c-c+1, l)
                yield from divide(r, wall_c+1, h, c+w-wall_c-1, l)
        for l in range(grid.levels):
            yield from divide(0, 0, grid.rows, grid.columns, l)
            if l < grid.levels - 1:
                # One guaranteed vertical passage per division level
                u, v = grid.get_cell(random.randint(0, grid.rows-1), random.randint(0, grid.columns-1), l), grid.get_cell(0, 0, l+1)
                # Just random link to next level
                target = grid.get_cell(random.randint(0, grid.rows-1), random.randint(0, grid.columns-1), l+1)
                u.link(target); yield u, target

# --- SOLVERS ---

class MazeSolver:
    def solve(self, grid: Grid, start: Cell, goal: Cell):
        for path in self.solve_step(grid, start, goal): pass
        return path
    def reconstruct(self, came_from, start, goal):
        path, curr = [], goal
        while curr:
            path.append((curr.row, curr.column, curr.level))
            if curr == start: break
            curr = came_from.get(curr)
        return path[::-1]

class BFS_Solver(MazeSolver):
    def solve_step(self, grid, start, goal):
        q, came_from = deque([start]), {start: None}
        while q:
            curr = q.popleft()
            if curr == goal: break
            for n in curr.get_links():
                if n not in came_from:
                    came_from[n] = curr; q.append(n)
                    yield self.reconstruct(came_from, start, n)
        yield self.reconstruct(came_from, start, goal)

class DFS_Solver(MazeSolver):
    def solve_step(self, grid, start, goal):
        stack, came_from = [start], {start: None}
        while stack:
            curr = stack.pop()
            if curr == goal: break
            for n in curr.get_links():
                if n not in came_from:
                    came_from[n] = curr; stack.append(n)
                    yield self.reconstruct(came_from, start, n)
        yield self.reconstruct(came_from, start, goal)

class AStar_Solver(MazeSolver):
    def solve_step(self, grid, start, goal):
        pq, came_from, g = [(0, start)], {start: None}, {start: 0}
        while pq:
            _, curr = heapq.heappop(pq)
            if curr == goal: break
            for n in curr.get_links():
                score = g[curr] + 1
                if n not in g or score < g[n]:
                    g[n] = score
                    f = score + abs(n.row-goal.row) + abs(n.column-goal.column) + abs(n.level-goal.level)*5
                    heapq.heappush(pq, (f, n)); came_from[n] = curr
                    yield self.reconstruct(came_from, start, n)
        yield self.reconstruct(came_from, start, goal)