# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2025-12-26

### Added
- **Multi-Slot Profiles**: Support for 3 independent adventure profiles.
- **Pre-Menu System**: New `MainMenuView` for branching between Adventure and Creative modes.
- **Profile Management**: New `ProfileSelectView` to view stats and reset adventure progress.
- **Expanded Creative Mode**: Added "Epic" and "Colossal" maze sizes.
- **Dynamic FOV Difficulty**: In Adventure mode, FOV visibility radius now scales inversely with player level.

### Changed
- **HUD Optimization**: Removed FPS counter from the main HUD for a cleaner look.
- **Difficulty Balance**: Increased complexity ramp-up for large-scale grids.

### Fixed
- **Navigation Logic**: Improved ESC key behavior to return to appropriate sub-menus.
- **Git Hygiene**: Added player profiles and exports to `.gitignore`.
