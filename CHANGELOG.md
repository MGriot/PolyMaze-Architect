# Changelog

All notable changes to this project will be documented in this file.

## [v1.4.0] - 2025-12-26

### Added
- **Multidimensional Adaptive Engine**: Replaced linear leveling with a 4-vector skill profile (Spatial, Perception, Structural, Efficiency).
- **Explorative Map (Fog of War)**: Architectural Map now hides unvisited areas when enabled or triggered by difficulty.
- **Dynamic Braid Scaling**: Mazes now transition from simple trees to complex multi-path networks based on player efficiency.
- **Performance Momentum**: System rewards rapid, tool-free successes with accelerated growth rates.

### Changed
- **Adaptive HUD**: Profile selection now displays calculated aggregate skill levels instead of simple integers.
- **Enhanced Scale**: Maximum maze dimensions increased to 120x155 for the "Colossal" setting and high-level Adventure mode.
- **Grace Periods**: Implemented logic to stabilize difficulty if the system detects a player is struggling.

### Fixed
- **API Synchronization**: Fully migrated to Arcade 3.x `draw_rect_filled` API across all views.
- **Profile Integrity**: Resolved slot-mixing bugs; each profile now correctly persists to its independent JSON file.
- **Camera Centering**: Fixed Architectural Map centering logic for high-verticality mazes.
