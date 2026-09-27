# PolyMaze Architect: Multi-Algo, Multi-Topology, 3D Builder

**PolyMaze Architect** is an advanced maze generation and exploration suite. Unlike standard maze games, it allows you to architect complex structures using multiple mathematical algorithms across different grid shapes and vertical levels.

## 🚀 Key Features
- **Hybrid Topologies**: Architect mazes in classic **Square**, **Triangular**, **Polar**, or organic **Hexagonal** grids.
- **Adventure Mode**: Experience an **Adaptive Difficulty** system that learns from your performance and scales complexity accordingly.
- **3D Verticality**: Generate multi-level mazes (up to 6 floors) connected by functional stairs.
- **Algorithm Sandbox**: Choose from 10 generation algorithms (Wilson's, Prim's, etc.) and 3 solvers (A*, BFS, DFS).
- **Star Collection**: Optional secondary objectives that must be cleared to unlock the exit, fully integrated into the adaptive challenge model.
- **Tiered AI Solver**: Intelligent pathfinding that can calculate routes directly to the exit or optimal paths through all required stars.
- **Dynamic Lighting**: Real-time raycasted Field of View with stepped attenuation. In Adventure mode, FOV becomes a critical difficulty factor.
- **Explorative Map**: Toggle a "Fog of War" on the Architectural view to show only areas you've physically explored.
- **Architectural Overview**: Toggle an "exploded" view (`M` key) with full panning and zooming support.
- **Cross-Platform**: Built on **Kivy**: runs on Windows, macOS, Linux and **Android**, with touch controls (tap/hold/swipe to walk, pinch to zoom) alongside the classic keyboard layout.
- **High Performance**: GPU-batched wall meshes and an angle-binned raycaster keep FOV fast even on Colossal grids.
- **Themed UI**: Built-in **Dark** and **Light** modes with custom color palettes.

## 📥 Install

Download the latest build from the project's **Releases** page:

| Platform | File |
| --- | --- |
| Windows | `PolyMazeArchitect-Setup-<version>.exe` (installer) or the portable `.zip` |
| macOS | `PolyMazeArchitect-<version>-macos.dmg` (unsigned: right-click → Open the first time) |
| Linux | `PolyMazeArchitect-<version>-linux-x86_64.tar.gz` |
| Android | `polymazearchitect-<version>-debug.apk` (enable "Install unknown apps" to sideload) |

Adventure profiles and screenshots are stored in your per-user data folder (`%APPDATA%\polymaze` on Windows, app-private storage on Android).

## 🛠️ Run from Source

Requires Python 3.10–3.13.

```bash
python -m venv .venv
.\.venv\Scripts\activate    # Windows
source .venv/bin/activate    # Linux/Mac
pip install -r requirements-dev.txt
python src/main.py
```

Run the test suite (core logic only; no display needed):
```bash
pytest
```

## 📦 Build Installers

See [Packaging](docs/packaging.md) for details. In short:

- **Desktop**: `pyinstaller packaging/pyinstaller/polymaze.spec --noconfirm` builds `dist/PolyMazeArchitect/`. On Windows, `iscc packaging\windows\polymaze.iss` then wraps it in an installer.
- **Android**: `buildozer android debug` (Linux or WSL2) builds an APK into `bin/`.
- **CI**: pushing a `v*` tag builds every platform and attaches the files to a GitHub Release.

## 📖 Documentation
For deeper insights, check out the following guides in the `/docs` folder:
- [**Adaptive Difficulty System**](docs/adaptive_difficulty.md): How Adventure mode learns from you.
- [**Maze Theory & Algorithms**](docs/theory.md): The math behind the mazes.
- [**Generation Algorithms - Trade-offs**](docs/algorithms.md): Comparative analysis of the 10 builders.
- [**Software Architecture**](docs/architecture.md): How the modular layers work.
- [**User Guide & Controls**](docs/usage.md): Comprehensive keybindings.
- [**Packaging**](docs/packaging.md): Building the desktop installers and the Android APK.
- [**Cross-Platform Roadmap**](docs/cross_platform_roadmap.md): The Kivy migration and what's next (iOS).

## 📂 Project Structure
- `src/polymaze/core/`: UI-free game logic (topology, algorithms, geometry, rules, profiles, `themes.json`).
- `src/polymaze/ui/`: Kivy frontend (screens, maze renderer, map overlay, HUD, input).
- `src/main.py`: Entry point for development, PyInstaller and Buildozer.
- `packaging/`: PyInstaller spec and Inno Setup script. `buildozer.spec` sits at the root.
- `tests/`: Unit tests for the core.
- `docs/`: Technical documentation and guides.
