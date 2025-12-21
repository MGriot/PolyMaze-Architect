# maze_topology.py
import random
from typing import List, Dict, Optional, Iterator

class Cell:
    """A node in the maze graph."""
    def __init__(self, row: int, column: int, level: int = 0):
        self.row = row
        self.column = column
        self.level = level
        self.links: Dict['Cell', bool] = {} # Connected neighbors (Paths)
        self.neighbors: List['Cell'] = []   # All adjacent cells

    def link(self, cell: 'Cell', bidi=True):
        self.links[cell] = True
        if bidi: cell.link(self, bidi=False)

    def unlink(self, cell: 'Cell', bidi=True):
        if cell in self.links:
            del self.links[cell]
        if bidi: cell.unlink(self, bidi=False)

    def is_linked(self, cell: 'Cell') -> bool:
        return cell in self.links

    def get_links(self) -> List['Cell']:
        return list(self.links.keys())
    
    def __lt__(self, other):
        return (self.level, self.row, self.column) < (other.level, other.row, other.column)

class Grid:
    """Abstract Grid container."""
    def __init__(self, rows: int, columns: int, levels: int = 1):
        self.rows = rows
        self.columns = columns
        self.levels = levels
        self.grid = [[[Cell(r, c, l) for c in range(columns)] for r in range(rows)] for l in range(levels)]
        self._configure_cells()
        
    def _configure_cells(self):
        pass

    def get_cell(self, row, col, level=0) -> Optional[Cell]:
        if 0 <= level < self.levels and 0 <= row < self.rows and 0 <= col < self.columns:
            return self.grid[level][row][col]
        return None

    def random_cell(self) -> Cell:
        return self.grid[random.randint(0, self.levels-1)][random.randint(0, self.rows-1)][random.randint(0, self.columns-1)]

    def size(self) -> int:
        return self.rows * self.columns * self.levels

    def each_cell(self) -> Iterator[Cell]:
        for level in self.grid:
            for row in level:
                for cell in row:
                    yield cell

    def braid(self, p=0.5):
        """Removes dead ends to create multiple paths."""
        dead_ends = [c for c in self.each_cell() if len(c.get_links()) == 1]
        random.shuffle(dead_ends)
        
        for cell in dead_ends:
            if len(cell.get_links()) != 1 or random.random() > p:
                continue
            
            # Find neighbors not already linked
            unlinked = [n for n in cell.neighbors if not cell.is_linked(n)]
            # Prefer linking to other dead ends
            best = [n for n in unlinked if len(n.get_links()) == 1]
            target = random.choice(best if best else unlinked)
            cell.link(target)

class SquareGrid(Grid):
    def _configure_cells(self):
        for cell in self.each_cell():
            r, c, l = cell.row, cell.column, cell.level
            # 2D neighbors
            for dr, dc in [(-1,0), (1,0), (0,1), (0,-1)]:
                neighbor = self.get_cell(r + dr, c + dc, l)
                if neighbor: cell.neighbors.append(neighbor)
            # 3D neighbors (Stairs)
            for dl in [-1, 1]:
                neighbor = self.get_cell(r, c, l + dl)
                if neighbor: cell.neighbors.append(neighbor)

class HexGrid(Grid):
    def _configure_cells(self):
        for cell in self.each_cell():
            row, col, l = cell.row, cell.column, cell.level
            # Hex neighbors (Pointy-top, odd-r)
            if row % 2 == 0:
                deltas = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (0, 1)]
            else:
                deltas = [(1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (0, 1)]
            
            for dr, dc in deltas:
                neighbor = self.get_cell(row + dr, col + dc, l)
                if neighbor: cell.neighbors.append(neighbor)
            # 3D neighbors
            for dl in [-1, 1]:
                neighbor = self.get_cell(row, col, l + dl)
                if neighbor: cell.neighbors.append(neighbor)
