# Changelog

All notable changes to this project will be documented in this file.

## [v1.5.0] - 2025-12-26

### Added
- **Star Collection Challenge**: Optional objective to collect 3 stars before the exit unlocks.
- **Tiered AI Solver**: `X` key now cycles between Path-to-Exit, Path-to-Stars+Exit, and Clear.
- **Run Reset Mechanics**: Pressing `BACKSPACE` now allows for an immediate exit from a maze.
- **Collection Skill Vector**: New adaptive difficulty parameter tracking star retrieval proficiency.
- **Greedy Multi-Target Solver**: New logic in `maze_algorithms.py` to calculate efficient routes through multiple waypoints.

### Changed
- **Adventure Balance**: Resetting a run now applies a significant XP penalty and skill decay.
- **Score Multipliers**: Stars provide a performance bonus, while AI tools now apply harsher penalties (up to 80%).
- **Map Legend**: Added "STAR" and "FOG" status indicators to the architectural view.

### Fixed
- **Victory Conditions**: Correctly enforced star collection requirement when active.
- **UI Feedback**: Star counts and collection status now display in the primary HUD.
