# Software Architecture

## 1. Design Philosophy
The project is split into a **Brain** and **Eyes**:

- `polymaze.core` (the Brain) is pure Python with **no UI imports**. `tests/test_core_is_ui_free.py` enforces this. The same code runs on desktop, Android and in the test suite.
- `polymaze.ui` (the Eyes) is the Kivy frontend: rendering, input and screen flow.

## 2. Core Layer (`src/polymaze/core/`)

### Topology (`topology.py`)
- **Cell**: Core unit with link/neighbor state and masking support.
- **Grid**: Abstract base for different geometries; **Square**, **Hexagonal**, **Triangular** and **Polar** implementations.
- **Masking System**: `mask_shape` applies geometric forms (Rectangle, Circle, Donut, N-gons…) to any topology.

### Algorithms (`algorithms.py`)
- **Strategy Pattern** generators that `yield` progress for non-blocking animation.
- **Solvers**: BFS, DFS and A* (`solve_step`), plus a greedy multi-target route through stars (`solve_multi`).

### Geometry (`geometry.py`)
- **MazeGeometry**: all spatial math, in world units, centred on the origin. The UI camera handles screen placement, so nothing depends on the window size.
- `get_occlusion_polygons`: Post-and-Beam wall model (convex polygons; shared walls emitted once; cached per floor).
- `fov_polygon`: raycast FOV. Nearby wall segments come from a spatial hash, then each segment is binned into the rays inside its angular span, so a ray tests only the walls in its direction.
- Helpers for stair arrows, cell outlines, star shapes, floor offsets for the exploded map, and coordinate labels.

### Game Rules (`game_state.py`)
- **GameState**: one maze run. It covers generation stepping, start/end/star placement, movement (`move(vector)` picks the linked neighbor best aligned with any direction vector, so keys, swipes and taps share one path), stairs, star collection, win detection, tiered solver, timers, and adventure scoring/penalties.

### Adaptive Profiles (`adventure.py`)
- **AdventureEngine**: multidimensional skill profile (Spatial, Perception, Structural, Efficiency, Collection) and the adaptive feedback loop. See [Adaptive Difficulty](adaptive_difficulty.md).
- Profiles are JSON files in a `data_dir` supplied by the UI (the OS per-user data folder). Writes are atomic, and profiles saved in CWD by the old Arcade build are migrated on first run.

### Settings & Catalog (`settings.py`, `catalog.py`, `themes.json`)
- Theme palette (`settings.theme`, Dark/Light), fixed accent colors, cell radius, FOV ray count.
- Option lists for the Creative menu (cell types, shapes, sizes, generators).

## 3. UI Layer (`src/polymaze/ui/`)

| Module | Role |
| --- | --- |
| `app.py` | `PolyMazeApp`: window config, `ScreenManager`, global key dispatch, theme switching |
| `screens/` | Main menu, profile select, creative setup, game screen |
| `maze_widget.py` | `MazeView`: draws the current floor (batched wall meshes, markers, trace/solution), follow camera, stencil-masked FOV |
| `map_overlay.py` | `MapView`: exploded multi-floor view with coordinate labels, legend and explored-cell stencil mask |
| `hud.py` | Status bar, floor minimap, touch tool buttons, stair buttons, victory panel |
| `controls.py` | Key codes and the `Gestures` helper (tap/hold-to-walk, swipe, drag, pinch, wheel) |
| `gfx.py` | Color conversion, mesh batching (split under Kivy's 65k-vertex limit), world-space text, `Camera` |
| `widgets.py` | Themed buttons/labels and a keyboard-navigable `MenuScreen` base |

### Rendering notes
- Walls for a floor are fan-triangulated into a few large `Mesh(mode="triangles")` instructions and rebuilt only when the floor or theme changes.
- FOV uses `StencilPush → FOV mesh → StencilUse → world → StencilUnUse → FOV mesh → StencilPop`. Goal, stars and player are drawn after the stencil, so they stay visible in the dark.
- The camera is `PushMatrix / Translate / Scale / Translate / PopMatrix`; `Camera.screen_to_world` converts touch positions.

## 4. Data Flow
1. `MainMenuScreen` → `ProfileSelectScreen` (Adventure) or `CreativeMenuScreen`.
2. Adventure: `AdventureEngine.get_next_maze_params()` produces the maze settings from the skill profile.
3. `PolyMazeApp.start_game(**params)` → `GameScreen.start` builds a `GameState` (grid, mask, generator) after drawing a loading label.
4. Each frame `GameScreen._tick` advances generation/solver, animates the player, and asks `MazeView` or `MapView` plus the `Hud` to redraw.
5. Input (keys, taps, buttons) calls `GameState` methods; the state is the single source of truth.
6. On victory in Adventure, `GameState` records the result with `AdventureEngine` right away, and the victory panel shows the updated profile.

## 5. Entry Points
- **`src/main.py`**: used for development (`python src/main.py`), by PyInstaller and by Buildozer.
- **`python -m polymaze`**: equivalent, when `src` is on `PYTHONPATH` or the package is installed (`pip install -e .`).

## 6. Further Reading
- [**User Guide & Controls**](usage.md)
- [**Packaging**](packaging.md)
- [**Adaptive Difficulty Logic**](adaptive_difficulty.md)
- [**Maze Theory**](theory.md)
- [**Algorithm Trade-offs**](algorithms.md)
