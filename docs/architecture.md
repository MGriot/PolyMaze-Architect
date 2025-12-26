# Software Architecture

## 1. Design Philosophy
The project follows a **Strict Decoupling** strategy to ensure that logic, data, and presentation never overlap.

## 2. Layers

### Topology (`maze_topology.py`)
- **Cell**: Core unit with link/neighbor state and masking support.
- **Grid**: Abstract base for different geometries.
- **Topologies**: Square, Hexagonal, Triangular, and Polar (Circular) implementations.
- **Masking System**: Built into the base `Grid` class, allowing geometric forms (Rectangle, Circle, etc.) to be applied to any topology.

### Logic (`maze_algorithms.py`)
- Implements the **Strategy Pattern**.
- Algorithms yield progress for non-blocking UI animations.
- **Solvers**: AI pathfinding using BFS, DFS, and A* strategies.

### Rendering (`renderer.py`)
- **MazeRenderer**: Encapsulates all spatial and vertex calculations.
- Centralizes geometry generation for different cell shapes.
- **Dynamic FOV Engine**: 
    - Implements a raycasting-based visibility system using sorted angle sweeps.
    - Utilizes OpenGL Stencil Buffers for watertight masking of walls and entities.
    - Supports stepped radial attenuation for a low-poly aesthetic.
- Manages dual-view consistency (Game View vs. Architectural Map).

### Presentation (`views.py`)
- **Menu Layer**: State management for generation parameters.
- **Dual-Camera System**:
    - `maze_camera` (`Camera2D`): Smoothly tracks the player and handles dynamic zooming.
    - `gui_camera` (`Camera2D`): Renders fixed UI elements (HUD bar, prompts) at a constant 1:1 scale.
- **Discrete Movement Engine**: State-based navigation using spatial alignment (dot-product) instead of physics collisions.

## 3. Data Flow
1. `MenuView` gathers parameters.
2. `GameView` instantiates the `Grid` and `MazeRenderer`.
3. `mask_shape` deactivates cells outside the target form.
4. `MazeGenerator` yields steps until the spanning tree is complete.
5. `GameView` switches cameras per-frame to render both the centered maze and the fixed HUD overlay.
