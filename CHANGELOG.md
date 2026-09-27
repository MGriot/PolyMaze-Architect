# Changelog

All notable changes to this project will be documented in this file.

## [v2.0.0] - 2026-09-27

### Added
- **Android support**: `buildozer.spec` builds an APK/AAB from the same codebase.
- **Desktop installers**: PyInstaller spec for Windows/macOS/Linux and an Inno Setup installer for Windows.
- **CI**: GitHub Actions runs the tests on every push and builds all platforms on `v*` tags, attaching them to a Release.
- **Touch controls**: tap/hold/swipe to walk, pinch or mouse-wheel zoom, drag to pan the map, on-screen tool and stair buttons.
- **Clickable menus**: every menu option is a button; keyboard navigation still works.
- **App icon and splash screen** (`tools/make_assets.py`).
- **Tests** for the FOV polygon, game rules, profiles, and a check that the core has no UI imports.

### Changed
- **Arcade → Kivy**: the UI was rewritten on Kivy; game logic moved to the UI-free `polymaze.core` package.
- **Save location**: profiles and screenshots now live in the per-user data folder. Existing profiles are migrated automatically.
- **Adventure results** are recorded as soon as you reach the exit, so leaving from the victory screen no longer discards the run.
- **FOV performance**: rays only test walls in their direction; shared walls are generated once. Colossal grids went from hundreds of milliseconds per move to about 10–25 ms.
- Entry point is now `python src/main.py` (`run_app.py` removed).

### Fixed
- Adventure mode crashed on completion or reset (`AdventureEngine.save_profile` was missing).
- Victory screen read a `skill_level` field that newer profiles don't have.
- FOV hit distance no longer depends on the order in which walls are tested.

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
