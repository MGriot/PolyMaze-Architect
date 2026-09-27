# catalog.py
"""Option lists shown in the Creative menu."""
from typing import List, Tuple, Type
from .topology import Grid, SquareCellGrid, HexCellGrid, TriCellGrid, PolarCellGrid
from .algorithms import (
    MazeGenerator, RecursiveBacktracker, RandomizedPrims, AldousBroder,
    BinaryTree, Wilsons, Kruskals, Sidewinder, RecursiveDivision,
    HuntAndKill, Ellers
)

CELL_TYPES: List[Tuple[str, Type[Grid]]] = [
    ("Square", SquareCellGrid), ("Hexagonal", HexCellGrid),
    ("Triangular", TriCellGrid), ("Polar", PolarCellGrid)
]

SHAPES: List[str] = [
    "rectangle", "square", "circle", "oval", "semicircle", "triangle",
    "diamond", "rhombus", "cross", "parallelogram", "trapezoid", "kite",
    "pentagon", "hexagon", "heptagon", "octagon", "nonagon", "decagon", "donut"
]

SIZES: List[Tuple[str, int, int]] = [
    ("Small", 11, 15), ("Medium", 21, 31), ("Large", 31, 41),
    ("X-Large", 51, 71), ("Epic", 81, 101), ("Colossal", 121, 161)
]

GENERATORS: List[Tuple[str, Type[MazeGenerator]]] = [
    ("Backtracker", RecursiveBacktracker), ("Prim's", RandomizedPrims),
    ("Aldous-Broder", AldousBroder), ("Wilson's", Wilsons),
    ("Binary Tree", BinaryTree), ("Kruskal's", Kruskals),
    ("Sidewinder", Sidewinder), ("Rec. Division", RecursiveDivision),
    ("Hunt & Kill", HuntAndKill), ("Eller's", Ellers)
]

MAX_LEVELS = 6

def grid_type_for(grid_class: Type[Grid]) -> str:
    if issubclass(grid_class, HexCellGrid): return "hex"
    if issubclass(grid_class, TriCellGrid): return "tri"
    if issubclass(grid_class, PolarCellGrid): return "polar"
    return "rect"
