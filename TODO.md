# PolyMaze Architect - Development Tasks

## Feature Addition (Priority: High)
*   [DONE] [src/maze_algorithms.py] Implement **Hunt and Kill** algorithm.
*   [DONE] [src/maze_algorithms.py] Implement **Eller's Algorithm**.
*   [DONE] [src/maze_topology.py] Implement **TriGrid** class for triangular cell tessellation.
*   [DONE] [src/maze_topology.py] Implement **PolarGrid** (Circular Maze) logic.
*   [DONE] [src/views.py] Update `GameView` setup to allow **Random Start and End Points**.
*   [DONE] [src/maze_topology.py] Refactor architecture to support **Independent Cell Shapes and Maze Forms** (Masking).

## Testing (Priority: High)
*   [DONE] [tests/] **Initialize Test Suite**. Created `tests/` directory.
*   [DONE] [tests/test_topology.py] Added unit tests for `Cell` linking/unlinking and neighbor calculations.
*   [DONE] [tests/test_algorithms.py] Added verification tests for new algorithms.

## Refactoring (Priority: Medium)
*   [MEDIUM] [src/views.py] **Decompose GameView**. Extract rendering logic into a `MazeRenderer` class and solving orchestration into a `SolverManager`.
*   [DONE] [src/views.py] **Fix Performance Warning**. Refactored `MenuView` to use `arcade.Text` objects.
*   [MEDIUM] [src/views.py] Remove generic `except Exception` blocks. Handle specific errors or let the app crash with a useful log to allow for debugging.
*   [MEDIUM] [src/config.py] Implement schema validation for `themes.json` loading to prevent crashes on bad config.

## Documentation (Priority: Low)
*   [LOW] [docs/algorithms.md] Add specific documentation explaining the trade-offs of the new algorithms (Eller's/Hunt & Kill).
*   [LOW] [src/views.py] Add type hints (mypy) to all UI classes.