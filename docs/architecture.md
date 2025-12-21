# Software Architecture

## 1. Design Philosophy
The project follows a **Strict Decoupling** strategy to ensure that logic, data, and presentation never overlap.

## 2. Layers

### Topology (`maze_topology.py`)
- **Cell**: Core unit with link/neighbor state.
- **Grid**: Abstract base for different geometries.
- **SquareGrid / HexGrid**: Geometry-specific neighbor configuration and 3D level stacking.

### Logic (`maze_algorithms.py`)
- Implements the **Strategy Pattern**.
- Every algorithm is a generator that `yield`s progress, allowing for non-blocking UI animations.

### Presentation (`views.py`)
- **MenuView**: Configuration state.
- **GameView**: High-performance rendering engine.
- **Batched Rendering**: Uses `ShapeElementList` to send geometry to the GPU in bulk rather than line-by-line.

## 3. Data Flow
1. `MenuView` gathers parameters (Size, Topology, Levels).
2. `GameView` instantiates the correct `Grid` subclass.
3. The selected `Generator` strategy is executed (optionally via `yield` steps).
4. `ShapeElementList` is compiled once generation is finished.
5. `PhysicsEngineSimple` handles sprite collisions against the compiled walls.
