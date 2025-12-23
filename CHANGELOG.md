# Changelog

## [v2.1.0] - 2025-12-23

### Added
- **Dynamic Camera System**:
    - Implemented a smooth following camera using `arcade.camera.Camera2D`.
    - Added a separate `gui_camera` for fixed UI overlays.
    - **Zoom Controls**: Use `+` and `-` to scale the view (0.1x to 3.0x).
- **Professional HUD**:
    - Added a semi-transparent HUD bar at the top of the screen.
    - Added real-time **FPS** display.
    - Added **Step Counter** to track player movement.
    - Added **Time Tracking** to measure maze solve duration.
- **Enhanced Movement**:
    - Unified cell-based movement across all topologies using spatial dot-product alignment.

### Fixed
- Fixed critical `AttributeError` by updating camera implementation for Arcade 3.3.x.
- Fixed `IndentationError` in the main rendering loop.
- Fixed `NoneType` attribute errors during fast view transitions.

## [v2.0.0] - 2025-12-22

### Added
- **Topologies**: Triangular and Polar (Circular) grid support.
- **Geometric Masks**: Apply forms (Circle, Hexagon, etc.) to any grid.
- **Algorithms**: Added Hunt & Kill and Eller's algorithms.
- **Theme Engine**: JSON-based theme validation and light/dark mode support.

### Changed
- Refactored rendering logic into a standalone `MazeRenderer` class.
- Replaced velocity physics with snappy state-based discrete movement.
- Re-mapped solution toggle to the **'X'** key to avoid WASD conflicts.