# maze_topology.py
import random
from typing import List, Dict, Optional, Iterator

class Cell:
    """A node in the maze graph."""
    def __init__(self, row: int, column: int):
        self.row = row
        self.column = column
        self.links: Dict['Cell', bool] = {} # Connected neighbors (Paths)
        self.neighbors: List['Cell'] = []   # All adjacent cells (Walls or Paths)

    def link(self, cell: 'Cell', bidi=True):
        """Open a path (remove wall) between this cell and another."""
        self.links[cell] = True
        if bidi: cell.link(self, bidi=False)

    def unlink(self, cell: 'Cell', bidi=True):
        """Place a wall between this cell and another."""
        if cell in self.links:
            del self.links[cell]
        if bidi: cell.unlink(self, bidi=False)

    def is_linked(self, cell: 'Cell') -> bool:
        return cell in self.links

    def get_links(self) -> List['Cell']:
        return list(self.links.keys())
    
    def __lt__(self, other):
        # needed for PriorityQueue comparisons
        return (self.row, self.column) < (other.row, other.column)

class Grid:
    """Abstract Grid container."""
    def __init__(self, rows: int, columns: int):
        self.rows = rows
        self.columns = columns
        self.grid = [[Cell(r, c) for c in range(columns)] for r in range(rows)]
        self._configure_cells()
        
    def _configure_cells(self):
        """Defined in subclasses to set neighbors (Square, Hex, etc)"""
        pass

    def get_cell(self, row, col) -> Optional[Cell]:
        if 0 <= row < self.rows and 0 <= col < self.columns:
            return self.grid[row][col]
        return None

    def random_cell(self) -> Cell:
        return self.grid[random.randint(0, self.rows-1)][random.randint(0, self.columns-1)]

    def size(self) -> int:
        return self.rows * self.columns

    def each_cell(self) -> Iterator[Cell]:
        for row in self.grid:
            for cell in row:
                yield cell

class SquareGrid(Grid):
    """Concrete grid with 4 neighbors (NSEW)."""
    def _configure_cells(self):
        for cell in self.each_cell():
            r, c = cell.row, cell.column
            # Add neighbors (North, South, East, West)
            for dr, dc in [(-1,0), (1,0), (0,1), (0,-1)]:
                neighbor = self.get_cell(r + dr, c + dc)
                if neighbor:
                    cell.neighbors.append(neighbor)

class HexGrid(Grid):
    """Concrete grid with 6 neighbors (Hexagonal).
    Using 'odd-r' horizontal layout (shoves odd rows right).
    """
    def _configure_cells(self):
        for cell in self.each_cell():
            row, col = cell.row, cell.column
            north_diagonal = -1 if (row % 2 == 0) else 0
            south_diagonal = -1 if (row % 2 == 0) else 0
            
            # Neighbors for odd-r layout
            # North-West, North-East, East, South-East, South-West, West
            # Note: The logic for diagonals depends on row parity
            
            # Shared deltas
            # West, East
            deltas = [(0, -1), (0, 1)]
            
            if row % 2 == 0:
                # Even rows
                # NW, NE, SW, SE
                deltas.extend([(-1, -1), (-1, 0), (1, -1), (1, 0)])
            else:
                # Odd rows
                # NW, NE, SW, SE
                deltas.extend([(-1, 0), (-1, 1), (1, 0), (1, 1)])

            for dr, dc in deltas:
                neighbor = self.get_cell(row + dr, col + dc)
                if neighbor:
                    cell.neighbors.append(neighbor)