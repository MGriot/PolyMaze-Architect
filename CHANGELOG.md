# Changelog

All notable changes to this project will be documented in this file.

## [v1.1.0] - 2025-12-25

### Added
- **Dynamic Field of View**: Implemented a new Raycasting-based lighting system.
- **Stepped Attenuation**: Light now fades in distinct bands ("posterized" effect) as requested.
- **Dark Mode Optimization**: Significant performance improvements for visibility calculations.

### Changed
- **Refactored Renderer**: Moved visibility calculation logic from `views.py` to `renderer.py`.
- **Lighting Algorithm**: Switched from per-frame brute-force segment checking to a sorted angle sweep algorithm ($O(N \log N)$).

### Fixed
- **Frame Drops**: Resolved severe lag when using Dark Mode on large maps.
- **Light Bleeding**: Fixed issues where light would pass through wall corners in specific topologies.
