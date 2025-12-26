# PolyMaze Architect: Multi-Algo, Multi-Topology, 3D Builder

**PolyMaze Architect** is an advanced maze generation and exploration suite. Unlike standard maze games, it allows you to architect complex structures using multiple mathematical algorithms across different grid shapes and vertical levels.

## 🚀 Key Features
- **Hybrid Topologies**: Architect mazes in classic **Square**, **Triangular**, **Polar**, or organic **Hexagonal** grids.
- **Adventure Mode**: Experience an **Adaptive Difficulty** system that learns from your performance and scales complexity accordingly.
- **3D Verticality**: Generate multi-level mazes (up to 6 floors) connected by functional stairs.
- **Algorithm Sandbox**: Choose from 10 generation algorithms (Wilson's, Prim's, Kruskal's, etc.) and 3 solvers (A*, BFS, DFS).
- **Dynamic Lighting**: Real-time raycasted Field of View with stepped attenuation. In Adventure mode, FOV becomes a critical difficulty factor.
- **Architectural Overview**: Toggle an "exploded" view (`M` key) to see the entire 3D structure and its connections.
- **High Performance**: Powered by the **Arcade** library with GPU-batched rendering.
- **Themed UI**: Built-in **Dark** and **Light** modes with custom color palettes.

## 🛠️ Quick Start

### 1. Requirements
Ensure you have Python 3.10+ installed.
```bash
pip install arcade
```

### 2. Run the App
```bash
python src/main.py
```

## 📖 Documentation
For deeper insights, check out the following guides in the `/docs` folder:
- [**Maze Theory & Algorithms**](docs/theory.md): The math behind the mazes.
- [**Software Architecture**](docs/architecture.md): How the modular layers work.
- [**User Guide & Controls**](docs/usage.md): Comprehensive keybindings.

## 📂 Project Structure
- `src/`: Source code.
- `docs/`: Technical documentation and guides.
- `themes.json`: JSON-based color palette definitions.
