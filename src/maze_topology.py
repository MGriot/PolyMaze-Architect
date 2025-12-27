import random
import math
from typing import List, Dict, Optional, Iterator

class Cell:
    """A node in the maze graph."""
    def __init__(self, row: int, column: int, level: int = 0):
        self.row = row
        self.column = column
        self.level = level
        self.links: Dict['Cell', bool] = {} # Connected neighbors (Paths)
        self.neighbors: List['Cell'] = []   # All adjacent cells
        self.active: bool = True # For masking shapes

    def link(self, cell: 'Cell', bidi=True):
        if not self.active or not cell.active: return
        if cell in self.links: return
        self.links[cell] = True
        if bidi: cell.link(self, bidi=False)

    @property
    def active_neighbors(self) -> List['Cell']:
        return [n for n in self.neighbors if n.active]

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
        self.topology = "rect"
        self.grid = [[[Cell(r, c, l) for c in range(columns)] for r in range(rows)] for l in range(levels)]
        self._configure_cells()
        
    def _configure_cells(self):
        pass

    def get_cell(self, row, col, level=0) -> Optional[Cell]:
        if 0 <= level < self.levels and 0 <= row < self.rows and 0 <= col < self.columns:
            cell = self.grid[level][row][col]
            if cell.active: return cell
        return None

    def random_cell(self) -> Optional[Cell]:
        active_cells = list(self.each_cell())
        if not active_cells: return None
        return random.choice(active_cells)

    def size(self) -> int:
        return len(list(self.each_cell()))

    def each_cell(self) -> Iterator[Cell]:
        for level in self.grid:
            for row in level:
                for cell in row:
                    if cell.active: yield cell

    def mask_shape(self, shape: str):
        """Disables cells outside the desired shape."""
        shape = shape.lower()
        # Pre-calculate aspect ratio for true geometric shapes (Square, Circle)
        ar_cols = self.columns / max(1, self.rows)
        ar_rows = self.rows / max(1, self.columns)
        
        # Generic N-gon helper
        def is_ngon(nx, ny, n, rotate=False):
            angle = math.atan2(ny, nx)
            if rotate: angle += math.pi / n
            r = math.sqrt(nx**2 + ny**2)
            # Map angle to the sector of the polygon
            segment = 2 * math.pi / n
            # The distance from center to the edge at this angle
            # d = r * cos( (theta % segment) - segment/2 )
            # We want d <= apothem (distance from center to midpoint of edge)
            # For a unit polygon (radius 1 at vertices), apothem is cos(pi/n)
            # Actually, standard formula for "is inside unit polygon":
            # r * cos( (angle % (2pi/n)) - pi/n ) <= cos(pi/n)
            # This makes the vertices touch the unit circle.
            return (r * math.cos((angle % segment) - segment / 2)) <= math.cos(math.pi / n)

        for level in self.grid:
            for row in level:
                for cell in row:
                    nx, ny = self._get_normalized_coords(cell.row, cell.column)
                    keep = True
                    
                    if shape == "rectangle":
                        keep = True
                    elif shape == "square":
                        # Force 1:1 aspect ratio mask
                        if self.columns > self.rows: keep = abs(nx) <= (1.0 / ar_cols)
                        else: keep = abs(ny) <= (1.0 / ar_rows)
                    elif shape == "circle":
                        # Force 1:1 aspect ratio circle
                        dx, dy = nx, ny
                        if self.columns > self.rows: dx *= ar_cols
                        else: dy *= ar_rows
                        keep = (dx**2 + dy**2) <= 1.0
                    elif shape == "oval":
                        keep = (nx**2 + ny**2) <= 1.0
                    elif shape == "semicircle":
                        # Bottom half (ny > 0) is cut off? Or top? 
                        # ny goes -1 (top) to 1 (bottom). Let's keep top half.
                        keep = (nx**2 + ny**2) <= 1.0 and ny <= 0.2
                    elif shape == "donut":
                        dist = nx**2 + ny**2
                        keep = 0.25 <= dist <= 1.1
                    elif shape == "triangle":
                        # Equilateral-ish triangle pointing up
                        keep = (ny > -0.7) and (ny < 1.732 * nx + 1.2) and (ny < -1.732 * nx + 1.2)
                    elif shape == "diamond" or shape == "rhombus":
                        keep = abs(nx) + abs(ny) <= 1.2
                    elif shape == "parallelogram":
                        # Skewed rectangle: x + 0.5y bounded
                        keep = abs(nx - ny * 0.5) <= 0.7 and abs(ny) <= 0.8
                    elif shape == "trapezoid":
                        # Narrower at top (ny < 0)
                        width = 0.8 if ny > 0 else (0.8 + ny * 0.4) 
                        keep = abs(nx) <= width and abs(ny) <= 0.9
                    elif shape == "kite":
                        # Rhombus but lower part is elongated
                        # Top half (ny < 0): like diamond
                        # Bottom half (ny > 0): narrower
                        if ny < 0: keep = abs(nx) + abs(ny) <= 1.2
                        else: keep = abs(nx) + (ny * 0.5) <= 0.6 # Slower taper
                        # Clean up bounds
                        keep = keep and abs(ny) <= 1.0
                    elif shape == "cross":
                        keep = (abs(nx) <= 0.33) or (abs(ny) <= 0.33)
                    elif shape == "pentagon": keep = is_ngon(nx, ny, 5, rotate=True)
                    elif shape == "hexagon": keep = is_ngon(nx, ny, 6)
                    elif shape == "heptagon": keep = is_ngon(nx, ny, 7, rotate=True)
                    elif shape == "octagon": keep = is_ngon(nx, ny, 8)
                    elif shape == "nonagon": keep = is_ngon(nx, ny, 9, rotate=True)
                    elif shape == "decagon": keep = is_ngon(nx, ny, 10)

                    if not keep:
                        cell.active = False
                        for n in cell.neighbors:
                            cell.unlink(n)
                            n.unlink(cell)

    def _get_normalized_coords(self, r, c):
        ny = (r / max(1, self.rows-1)) * 2 - 1
        nx = (c / max(1, self.columns-1)) * 2 - 1
        return nx, ny

    def braid(self, p=0.5):
        """Removes dead ends to create multiple paths."""
        dead_ends = [c for c in self.each_cell() if len(c.get_links()) == 1]
        random.shuffle(dead_ends)
        for cell in dead_ends:
            if len(cell.get_links()) != 1 or random.random() > p:
                continue
            unlinked = [n for n in cell.active_neighbors if not cell.is_linked(n)]
            if unlinked:
                best = [n for n in unlinked if len(n.get_links()) == 1]
                target = random.choice(best if best else unlinked)
                cell.link(target)

class SquareCellGrid(Grid):
    def _configure_cells(self):
        self.topology = "rect"
        for level in self.grid:
            for row in level:
                for cell in row:
                    r, c, l = cell.row, cell.column, cell.level
                    for dr, dc in [(-1,0), (1,0), (0,1), (0,-1)]:
                        if 0 <= r+dr < self.rows and 0 <= c+dc < self.columns:
                            cell.neighbors.append(self.grid[l][r+dr][c+dc])
                    for dl in [-1, 1]:
                        if 0 <= l+dl < self.levels:
                            cell.neighbors.append(self.grid[l+dl][r][c])

class HexCellGrid(Grid):
    def _configure_cells(self):
        self.topology = "hex"
        for level in self.grid:
            for row in level:
                for cell in row:
                    r, c, l = cell.row, cell.column, cell.level
                    if r % 2 == 0:
                        deltas = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (0, 1)]
                    else:
                        deltas = [(1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (0, 1)]
                    for dr, dc in deltas:
                        if 0 <= r+dr < self.rows and 0 <= c+dc < self.columns:
                            cell.neighbors.append(self.grid[l][r+dr][c+dc])
                    for dl in [-1, 1]:
                        if 0 <= l+dl < self.levels:
                            cell.neighbors.append(self.grid[l+dl][r][c])

    def _get_normalized_coords(self, r, c):
        nx = ((c + 0.5 * (r % 2)) / self.columns) * 2 - 1
        ny = (r / self.rows) * 2 - 1
        return nx, ny

class TriCellGrid(Grid):
    def _configure_cells(self):
        self.topology = "tri"
        for level in self.grid:
            for row in level:
                for cell in row:
                    r, c, l = cell.row, cell.column, cell.level
                    if (r + c) % 2 == 0:
                        deltas = [(0, -1), (0, 1), (-1, 0)]
                    else:
                        deltas = [(0, -1), (0, 1), (1, 0)]
                    for dr, dc in deltas:
                        if 0 <= r+dr < self.rows and 0 <= c+dc < self.columns:
                            cell.neighbors.append(self.grid[l][r+dr][c+dc])
                    for dl in [-1, 1]:
                        if 0 <= l+dl < self.levels:
                            cell.neighbors.append(self.grid[l+dl][r][c])

    def _get_normalized_coords(self, r, c):
        nx = (c / self.columns) * 2 - 1
        ny = (r / self.rows) * 2 - 1
        return nx, ny

class PolarCellGrid(Grid):
    def _configure_cells(self):
        self.topology = "polar"
        for level in self.grid:
            for row in level:
                for cell in row:
                    r, c, l = cell.row, cell.column, cell.level
                    cw = self.grid[l][r][(c + 1) % self.columns]
                    ccw = self.grid[l][r][(c - 1) % self.columns]
                    cell.neighbors.append(cw); cell.neighbors.append(ccw)
                    if r > 0: cell.neighbors.append(self.grid[l][r-1][c])
                    if r < self.rows - 1: cell.neighbors.append(self.grid[l][r+1][c])
                    for dl in [-1, 1]:
                        if 0 <= l+dl < self.levels:
                            cell.neighbors.append(self.grid[l+dl][r][c])
    
    def _get_normalized_coords(self, r, c):
        radius_norm = r / max(1, self.rows)
        angle = (c / max(1, self.columns)) * 2 * math.pi
        return radius_norm * math.cos(angle), radius_norm * math.sin(angle)