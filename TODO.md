# Project TODOs

## [HIGH] Priority
- [x] **Refactor FOV Logic**: Implement efficient Raycasting/Shadowcasting with stepped attenuation.
- [x] **Unit Tests for FOV**: Geometric tests for `fov_polygon` (ray count, radius bound, wall blocking, brute-force equivalence) in `tests/test_geometry.py`.
- [x] **Performance Profiling**: Profiled on Colossal Square/Hex/Polar grids; angular binning + wall dedupe cut per-move FOV cost ~40x.
- [x] **Cross-Platform Port**: Kivy frontend, desktop installers, Android build ([roadmap](docs/cross_platform_roadmap.md)).
- [ ] **Android Device Test**: Install the release APK on a real phone; check touch feel, FOV frame rate on large mazes, save persistence, and that the next version updates in place.

## [MEDIUM] Priority
- [ ] **Theme Editor**: Add a UI to customize colors in `themes.json`.
- [ ] **Save/Load Mazes**: Serialize the `Grid` object to file.
- [ ] **Sound Effects**: Add audio for walking, bumping walls, and level completion (`kivy.core.audio.SoundLoader`).
- [ ] **Portrait Layout**: Phone-friendly portrait mode (currently landscape only).
- [ ] **iOS Build**: kivy-ios toolchain (needs a Mac).

## [LOW] Priority
- [ ] **Gamepad Support**: Add controller input handling (Kivy joystick events).
- [ ] **Minimap Toggle**: Allow the minimap to be hidden entirely.
- [ ] **Achievements**: Expand the XP system with specific badges.
- [ ] **Code Signing**: Sign the Windows installer and notarize the macOS app (Android releases are already signed).
