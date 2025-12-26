# Changelog

All notable changes to this project will be documented in this file.

## [v1.3.0] - 2025-12-26

### Added
- **Explorative Map (Fog of War)**: New feature that hides unvisited areas in the Architectural Map view.
- **Map Navigation**: Added WASD and Arrow Key support for panning the map camera.
- **Enhanced Difficulty Scaling**: Increased maze size limits (up to 110x140) and added multi-path (braid) probability to the learning model.
- **Adaptive Generation**: Mazes now generate faster proportionally to their size.

### Changed
- **Optimization Engine**: Implemented vertex caching and spatial partitioning for FOV, resulting in a 5x speedup on Colossal maps.
- **Stencil Masking**: Replaced per-cell filtering with OpenGL stencil buffers for the Explorative Map feature.
- **Refined Map Visuals**: Replaced background rectangles with semi-transparent "Floor Plates".

### Fixed
- **Arcade 3.x Compatibility**: Fixed `AttributeError` by migrating to `draw_rect_filled` and `LBWH`/`XYWH` helper classes.
- **Map Centering**: Resolved issue where the map would render off-screen on certain resolutions.
- **Keyboard Logic**: Fixed missing parameters in Creative menu input handling.
