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
    - **Polar (Circular) Grid**: Added concentric circle topology.
- **Features:**
    - **Independent Shapes**: Decoupled "Cell Shape" (Square, Hex, Tri, Polar) from "Maze Form" (Rectangle, Circle, Triangle, Hexagon).
    - **Masking System**: Added geometric masking to apply any maze form to any cell grid.
    - **Random Endpoints**: Added toggle for randomized start/end points.
- **Testing:**
    - Initialized comprehensive Unit Test suite.

### Changed
- **UI**: Refactored `MenuView` to use efficient text rendering objects, resolving performance warnings.
- **Architecture**: Refactored `Grid` classes to `*CellGrid` to clarify the separation between cell topology and maze boundaries.

### Fixed
- Fixed crash caused by missing methods in `GameView` after refactoring.
- Fixed `AttributeError` when starting the game.
- Fixed `PerformanceWarning` from `arcade.draw_text`.