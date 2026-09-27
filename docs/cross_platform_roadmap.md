# Cross-Platform Roadmap

PolyMaze Architect was ported from **Arcade** (desktop only) to **Kivy** so that one Python codebase runs on Windows, macOS, Linux and Android, and later iOS.

## Status

| Phase | Status |
| --- | --- |
| 1. Refactor core into `src/polymaze/core/` with zero UI imports | ✅ Done (enforced by `tests/test_core_is_ui_free.py`) |
| 2. Kivy renderer, menus and HUD | ✅ Done |
| 3. Unified input: keyboard + touch (tap/hold/swipe, pinch, on-screen buttons) | ✅ Done |
| 4. Desktop packaging: PyInstaller + Inno Setup, CI builds | ✅ Done |
| 5. Android packaging with Buildozer | ✅ Config + CI done; device testing pending |
| 6. iOS (kivy-ios, requires a Mac + Apple Developer account) | ⏳ Not started |

## How the original hurdles were solved
1. **Stencil management**: raw `pyglet.gl` stencil calls became Kivy `StencilPush / StencilUse / StencilUnUse / StencilPop` for both the FOV and the explorative map.
2. **Save paths**: profiles and screenshots go to `App.user_data_dir` (app-private storage on Android, `%APPDATA%` on Windows). The core receives it as `data_dir`.
3. **Responsive UI**: world geometry is centred on the origin and a camera fits it to any screen. UI sizes scale with window height and never shrink tap targets below ~40 dp.
4. **Performance on mobile**: FOV raycasting was reworked (angular binning, deduplicated walls, cached polygons). Per-move cost on Colossal grids dropped from hundreds of ms to under ~25 ms on a desktop CPU.

## Next steps
- Profile on a mid-range Android device. If FOV is still heavy on huge grids, lower `settings.FOV_RAYS` or cache FOV per cell.
- Consider `sensorLandscape` orientation and a portrait layout for phones.
- Sound effects via `kivy.core.audio.SoundLoader` and gamepad support via Kivy joystick events (see [TODO](../TODO.md)).

See also: [Packaging](packaging.md) · [Architecture](architecture.md)
