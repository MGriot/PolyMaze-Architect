# PolyMaze Architect - Development Tasks

## Feature Addition (Priority: High)
*   [DONE] [src/maze_algorithms.py] Implement **Hunt and Kill** algorithm.
*   [DONE] [src/maze_algorithms.py] Implement **Eller's Algorithm**.
*   [DONE] [src/maze_topology.py] Implement **TriCellGrid** class for triangular cell tessellation.
*   [DONE] [src/maze_topology.py] Implement **PolarCellGrid** (Circular Maze) logic.
*   [DONE] [src/views.py] Update `GameView` setup to allow **Random Start and End Points**.
*   [DONE] [src/maze_topology.py] Refactor architecture to support **Independent Cell Shapes and Maze Forms** (Masking).
*   [DONE] [src/maze_algorithms.py] Update all generators to be **Mask-Aware** using `active_neighbors`.

## Testing (Priority: High)
*   [DONE] [tests/] **Initialize Test Suite**. Created `tests/` directory.
*   [DONE] [tests/test_topology.py] Added unit tests for `Cell` linking/unlinking and neighbor calculations.
*   [DONE] [tests/test_algorithms.py] Added verification tests for new algorithms.

## Refactoring (Priority: Medium)
*   [DONE] [src/views.py] **Robust Triangular Rendering**. Implemented equilateral tiling and vertex-based edge detection.
*   [DONE] [src/views.py] **Enhanced Polar Layout**. Added center hole padding for improved navigability.
*   [DONE] [src/views.py] **Fix Performance Warning**. Refactored `MenuView` to use `arcade.Text` objects.
*   [MEDIUM] [src/views.py] **Decompose GameView**. Extract rendering logic into a `MazeRenderer` class.
*   [MEDIUM] [src/config.py] Implement schema validation for `themes.json` loading.

## Documentation (Priority: Low)
*   [LOW] [docs/algorithms.md] Add specific documentation explaining the trade-offs of the new algorithms.
*   [LOW] [src/views.py] Add type hints (mypy) to all UI classes.