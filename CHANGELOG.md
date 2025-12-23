# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.0.0] - 2025-12-22

### Added
- **New Maze Algorithms:**
    - Added **Hunt and Kill** algorithm.
    - Added **Eller's Algorithm** (row-by-row generation).
- **New Grid Topologies:**
    - **Triangular Grid**: Perfect equilateral tessellation.
    - **Polar (Circular) Grid**: Concentric circles with center-hole padding for navigability.
- **Features:**
    - **Independent Shapes**: Decoupled "Cell Shape" from "Maze Form".
    - **Masking System**: Apply any form (Circle, triangle, etc.) to any cell type.
    - **Discrete Movement**: Snappy cell-based navigation using Arrow keys or **WASD**.
    - **Solution Path**: Re-implemented solution toggle using the **'X'** key.

### Changed
- **Architecture**:
    - Extracted `MazeRenderer` class to handle all coordinate and wall-detection logic.
    - Refactored `GameView` to use discrete state-based movement instead of velocity physics.
- **Rendering**:
    - Implemented high-precision coordinate rounding to eliminate duplicate lines.
    - Updated generation phase to show accurate equilateral triangle/hex outlines.

### Fixed
- Fixed critical crash when drawing player sprites (`AttributeError`).
- Fixed `TypeError` in Sprite initialization across different library versions.
- Fixed logic gap where generation and solvers would ignore shape boundaries.
- Fixed starting and ending points sometimes spawning outside the maze shape.
