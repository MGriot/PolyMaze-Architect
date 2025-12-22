# maze_topology.py
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
        if not cell.active: return # Safety check
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
        active_cells = [c for c in self.each_cell()]
        if not active_cells: return None
        return random.choice(active_cells)

    def size(self) -> int:
        return len([c for c in self.each_cell()])

    def each_cell(self) -> Iterator[Cell]:
        for level in self.grid:
            for row in level:
                for cell in row:
                    if cell.active: yield cell

    def mask_shape(self, shape: str):
        """Disables cells outside the desired shape."""
        # Center of the grid in logical coordinates
        cr, cc = self.rows / 2, self.columns / 2
        
        for level in self.grid:
            for row in level:
                for cell in row:
                    # Normalized coordinates (-1.0 to 1.0)
                    nx, ny = self._get_normalized_coords(cell.row, cell.column)
                    
                    keep = True
                    if shape == "circle":
                        keep = (nx**2 + ny**2) <= 1.0
                    elif shape == "triangle":
                        # Point up triangle: y > -0.5, y < -2x + 1, y < 2x + 1 (approx)
                        # Map ny to point up: Top at +1, Base at -1?
                        # Standard equi-tri: 
                        #  dist to center? 
                        # Simple barycentric or linear planes:
                        # Bottom: ny > -0.5
                        # Sides: abs(nx) < (1 - ny) * 0.577 (approx 1/sqrt(3)) ?
                        # Let's use a simple upright triangle logic
                        # Vertices: (0, 1), (-0.866, -0.5), (0.866, -0.5)
                        # We'll allow a bit larger: Top(0, 1), Bot(-1), Width varies
                        # Check 3 half-planes
                        # 1. Bottom: ny > -0.6
                        # 2. Left: ny < 1.732*nx + 1
                        # 3. Right: ny < -1.732*nx + 1
                        keep = (ny > -0.6) and (ny < 1.732 * nx + 1.1) and (ny < -1.732 * nx + 1.1)
                    elif shape == "hexagon":
                        # abs(x) < 0.866 and abs(y) < 1.0 and abs(y) < -abs(x) + ...
                        # Standard flat top: abs(dx) + abs(dy) < ...?
                        # Let's use max(abs(nx), abs(nx)*0.5 + abs(ny)*0.866) <= 1.0 (approx)
                        keep = max(abs(nx), abs(nx)*0.5 + abs(ny)*0.866) <= 0.95
                    
                    if not keep:
                        cell.active = False
                        # Unlink neighbors for graph integrity
                        for n in cell.neighbors:
                            cell.unlink(n)
                            n.unlink(cell)

    def _get_normalized_coords(self, r, c):
        """Returns x, y in range roughly -1 to 1 based on cell type geometry."""
        # Default rectangular mapping
        ny = (r / self.rows) * 2 - 1
        nx = (c / self.columns) * 2 - 1
        return nx, ny

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

class SquareCellGrid(Grid):
    def _configure_cells(self):
        for level in self.grid:
            for row in level:
                for cell in row:
                    r, c, l = cell.row, cell.column, cell.level
                    # 2D neighbors
                    # Check grid boundaries manually since get_cell filters active which isn't set yet
                    for dr, dc in [(-1,0), (1,0), (0,1), (0,-1)]:
                        if 0 <= r+dr < self.rows and 0 <= c+dc < self.columns:
                            cell.neighbors.append(self.grid[l][r+dr][c+dc])
                    # 3D neighbors
                    for dl in [-1, 1]:
                        if 0 <= l+dl < self.levels:
                            cell.neighbors.append(self.grid[l+dl][r][c])

    def _get_normalized_coords(self, r, c):
        # Y grows down in indices, but up in geometry? Let's stick to indices directions
        # -1 at top (r=0), 1 at bottom. -1 at left, 1 at right.
        return (c / max(1, self.columns-1)) * 2 - 1, (r / max(1, self.rows-1)) * 2 - 1

class HexCellGrid(Grid):
    def _configure_cells(self):
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
        # Hex conversion (pointy top)
        # x = sqrt(3) * (col + 0.5 * (row&1))
        # y = 3/2 * row
        import math
        x = math.sqrt(3) * (c + 0.5 * (r % 2))
        y = 1.5 * r
        
        # Normalize
        max_y = 1.5 * self.rows
        max_x = math.sqrt(3) * (self.columns + 0.5)
        
        return (x / max_x) * 2 - 1, (y / max_y) * 2 - 1

class TriCellGrid(Grid):
    def _configure_cells(self):
        for level in self.grid:
            for row in level:
                for cell in row:
                    r, c, l = cell.row, cell.column, cell.level
                    # Parity (r+c)%2 determines orientation
                    # even: Upright (^), odd: Inverted (v)
                    if (r + c) % 2 == 0:
                        deltas = [(0, -1), (0, 1), (1, 0)] # L, R, B
                    else:
                        deltas = [(0, -1), (0, 1), (-1, 0)] # L, R, T
                    
                    for dr, dc in deltas:
                        if 0 <= r+dr < self.rows and 0 <= c+dc < self.columns:
                            cell.neighbors.append(self.grid[l][r+dr][c+dc])
                    for dl in [-1, 1]:
                        if 0 <= l+dl < self.levels:
                            cell.neighbors.append(self.grid[l+dl][r][c])

    def _get_normalized_coords(self, r, c):
        # Precise scaling for equilateral triangles
        # h = sqrt(3)/2 * s. We treat s=1.
        nx = (c / max(1, self.columns - 1)) * 2 - 1
        ny = (r / max(1, self.rows - 1)) * 2 - 1
        return nx, ny
        # Tri coordinates
        # Width = 1, Height = sqrt(3).
        # x = c * 0.5, y = r * sqrt(3) roughly
        import math
        x = (c * 0.5) + 0.5
        y = r * math.sqrt(3)
        
        max_x = self.columns * 0.5 + 0.5
        max_y = self.rows * math.sqrt(3)
        return (x / max_x) * 2 - 1, (y / max_y) * 2 - 1

class PolarCellGrid(Grid):
    def _configure_cells(self):
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
        # Polar to Cartesian
        import math
        # r is radius, c is angle
        radius_norm = r / max(1, self.rows)
        angle = (c / max(1, self.columns)) * 2 * math.pi
        
        return radius_norm * math.cos(angle), radius_norm * math.sin(angle)
