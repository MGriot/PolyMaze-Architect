# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.0.0] - 2025-12-22

### Added
- **New Maze Algorithms:**
    - Added **Hunt and Kill** algorithm.
    - Added **Eller's Algorithm**.
- **New Grid Topologies:**
    - **Triangular Grid**: Added support for triangular tessellation.
    - **Polar (Circular) Grid**: Added concentric circle topology with center padding (hole) for better driveability.
- **Features:**
    - **Independent Shapes**: Decoupled "Cell Shape" (Square, Hex, Tri, Polar) from "Maze Form" (Rectangle, Circle, Triangle, Hexagon).
    - **Masking System**: Added geometric masking to apply any maze form to any cell grid.
    - **Random Endpoints**: Added toggle for randomized start/end points within valid active boundaries.
    - **Shape-Aware Generation**: Generators now strictly respect the chosen maze form.
- **Testing:**
    - Initialized comprehensive Unit Test suite.

### Changed
- **Rendering Engine**:
    - **Precise Tri-Tiling**: Implemented equilateral triangle tiling with crisp vertex-based wall rendering.
    - **Duplicate Line Elimination**: Optimized wall detection to ensure shared edges are drawn only once.
- **UI**: Refactored `MenuView` to use efficient text rendering objects, resolving performance warnings.
- **Architecture**: Refactored `Grid` classes to `*CellGrid` to clarify the separation between cell topology and maze boundaries.

### Fixed
- Fixed critical crashes (`AttributeError`) in `GameView` setup.
- Fixed logic gap where generation and solvers would ignore shape boundaries.
- Fixed starting and ending points sometimes spawning outside the maze shape.