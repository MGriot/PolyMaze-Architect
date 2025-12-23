# PolyMaze Architect - Development Tasks

## Feature Addition (Priority: High)
*   [DONE] [src/maze_algorithms.py] Implement **Hunt and Kill** algorithm.
*   [DONE] [src/maze_algorithms.py] Implement **Eller's Algorithm**.
*   [DONE] [src/maze_topology.py] Implement **TriCellGrid** class for triangular cell tessellation.
*   [DONE] [src/maze_topology.py] Implement **PolarCellGrid** (Circular Maze) logic.
*   [DONE] [src/views.py] Update `GameView` setup to allow **Random Start and End Points**.
*   [DONE] [src/maze_topology.py] Refactor architecture to support **Independent Cell Shapes and Maze Forms** (Masking).
*   [DONE] [src/maze_algorithms.py] Update all generators to be **Mask-Aware** using `active_neighbors`.

## Camera & UI (Priority: High)
*   [DONE] [src/views.py] Implement **Following Camera** (`Camera2D`) for Arcade 3.3.3.
*   [DONE] [src/views.py] Implement **Dynamic Zoom** system (+/- keys).
*   [DONE] [src/views.py] Implement **Professional HUD Bar** with live metrics (FPS, Steps, Time).
*   [DONE] [src/views.py] Separate **GUI Camera** from Game Camera.

## Testing (Priority: High)
*   [DONE] [tests/] **Initialize Test Suite**.
*   [DONE] [tests/test_topology.py] Added unit tests for `Cell` linking/unlinking and neighbor calculations.
*   [DONE] [tests/test_algorithms.py] Added verification tests for new algorithms.

## Refactoring (Priority: Medium)
*   [DONE] [src/views.py] **Robust Triangular Rendering**. Implemented equilateral tiling and vertex-based edge detection.
*   [DONE] [src/renderer.py] **Decompose GameView**. Extracted all rendering and coordinate logic into a dedicated class.
*   [DONE] [src/config.py] Implement **Schema Validation** for `themes.json` loading.

## Documentation (Priority: Low)
*   [DONE] [docs/algorithms.md] Add specific documentation explaining the trade-offs of the new algorithms.
*   [DONE] [src/views.py] Add type hints (mypy) to all UI classes.