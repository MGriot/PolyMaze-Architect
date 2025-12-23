# Software Architecture

## 1. Design Philosophy
The project follows a **Strict Decoupling** strategy to ensure that logic, data, and presentation never overlap.

## 2. Layers

### Topology (`maze_topology.py`)
- **Cell**: Core unit with link/neighbor state and masking support.
- **Grid**: Abstract base for different geometries.
- **SquareCellGrid / HexCellGrid / TriCellGrid / PolarCellGrid**: Geometry-specific neighbor configuration, coordinate normalization, and 3D level stacking.
- **Masking System**: Built into the base `Grid` class, allowing any geometric form (Rectangle, Circle, etc.) to be applied to any topology by deactivating specific cells.

### Logic (`maze_algorithms.py`)
- Implements the **Strategy Pattern**.
- Every algorithm is a generator that `yield`s progress, allowing for non-blocking UI animations.
- **Solvers**: Multi-algorithm AI pathfinding (BFS, DFS, A*).

### Rendering (`renderer.py`)
- **MazeRenderer**: Encapsulates all spatial calculations.
- Centralizes vertex generation for different cell shapes.
- Handles dual-view consistency (Game View vs. Exploded Architectural Map).

### Presentation (`views.py`)
- **MenuView**: Configuration state and theme management.
- **GameView**: UI interaction and camera management (`Camera2D`).
- **Batched Rendering**: Uses `ShapeElementList` to send geometry to the GPU in bulk.
- **Discrete Movement**: State-based navigation using spatial alignment scoring instead of floaty physics.

## 3. Data Flow
1. `MenuView` gathers parameters (Size, Topology, Levels).
2. `GameView` instantiates the correct `Grid` subclass.
3. The grid's `mask_shape` method is called to apply the desired maze form.
4. The selected `Generator` strategy is executed (optionally via `yield` steps).
5. `MazeRenderer` compiles `ShapeElementList` objects for walls and stairs.
6. User input maps logical directions to spatial neighbors for snappy movement.