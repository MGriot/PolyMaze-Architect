# Packaging: Desktop Installers & Android APK

PolyMaze Architect ships from a single Kivy codebase. All builds use `src/main.py` as the entry point.

| Target | Tool | Config | Output |
| --- | --- | --- | --- |
| Windows / macOS / Linux bundle | PyInstaller | `packaging/pyinstaller/polymaze.spec` | `dist/PolyMazeArchitect/` (`.app` on macOS) |
| Windows installer | Inno Setup 6 | `packaging/windows/polymaze.iss` | `dist/installer/PolyMazeArchitect-Setup-<ver>.exe` |
| Android | Buildozer (python-for-android) | `buildozer.spec` | `bin/*.apk` (debug) / `bin/*.aab` (release) |

The version number comes from `src/polymaze/__init__.py` (`__version__`).

## 1. App icon & splash

`src/polymaze/assets/` holds `icon.png`, `icon.ico` and `presplash.png`. They are rendered from a seeded maze by:

```bash
python tools/make_assets.py
```

## 2. Desktop (PyInstaller)

Build on the OS you are targeting; PyInstaller does not cross-compile.

```bash
pip install -r requirements-dev.txt
pyinstaller packaging/pyinstaller/polymaze.spec --noconfirm
```

- `dist/PolyMazeArchitect/PolyMazeArchitect.exe` (or the macOS `.app`) runs without Python installed.
- On Windows the SDL2/GLEW/ANGLE DLLs from `kivy_deps` are bundled automatically by the spec.
- The bundle is a folder (onedir), not a single file. It starts faster and is what the installer packages.

### Windows installer

Install Inno Setup 6 once:

```bash
winget install JRSoftware.InnoSetup
```

Then wrap the PyInstaller output:

```bash
iscc /DAppVersion=2.0.0 packaging\windows\polymaze.iss
```

The installer defaults to a per-user install (no admin prompt), adds Start-menu and optional desktop shortcuts, and registers an uninstaller. Saves in `%APPDATA%\polymaze` are kept on uninstall.

### macOS / Linux

- macOS: `hdiutil create -volname "PolyMaze Architect" -srcfolder dist/PolyMazeArchitect.app -ov -format UDZO PolyMazeArchitect.dmg`. The app is unsigned; users right-click → Open the first time. Signing and notarization need an Apple Developer account.
- Linux: ship `dist/PolyMazeArchitect/` as a `.tar.gz`.

## 3. Android (Buildozer)

Buildozer only runs on Linux. On Windows use **WSL2 (Ubuntu)**:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev
pip install --user buildozer cython
```

From the repo root (inside WSL, e.g. `/mnt/c/Users/<you>/Documents/Coding/PolyMaze Architect`):

```bash
buildozer android debug
```

The first build downloads the Android SDK/NDK (several GB) and takes 20–40 minutes; later builds are incremental. The APK lands in `bin/`.

Install it on a phone with USB debugging enabled:

```bash
buildozer android deploy run logcat
```

Or copy the APK to the phone and allow "Install unknown apps".

### Release build (Google Play)

1. Set `package.domain` in `buildozer.spec` to a domain you own. It becomes the permanent app id.
2. Bump `android.api` to the target level Google Play currently requires.
3. Create a signing key once and keep it safe; never commit it:
   ```bash
   keytool -genkey -v -keystore polymaze-release.keystore -alias polymaze -keyalg RSA -keysize 2048 -validity 10000
   ```
4. Build the bundle with the key exposed through the environment:
   ```bash
   export P4A_RELEASE_KEYSTORE=$PWD/polymaze-release.keystore
   export P4A_RELEASE_KEYSTORE_PASSWD=... P4A_RELEASE_KEYALIAS=polymaze P4A_RELEASE_KEYALIAS_PASSWD=...
   buildozer android release
   ```

## 4. Continuous integration

`.github/workflows/build.yml`:

- Every push / PR: runs the core test suite.
- Tag `v*` (or a manual run): builds the Windows installer + portable zip, the macOS `.dmg`, the Linux `.tar.gz` and the Android debug APK. On tags it attaches them all to a GitHub Release.

```bash
git tag v2.0.0
git push origin v2.0.0
```

## 5. Troubleshooting

- **Black window / no GL on a VM**: Kivy needs OpenGL 2.0+. On Windows VMs set `KIVY_GL_BACKEND=angle_sdl2`.
- **Kivy log**: `~/.kivy/logs/` (desktop). On Android use `adb logcat -s python`.
- **Python version**: Kivy 2.3 supports Python 3.8–3.13; build with 3.11 to match the Android toolchain.

See also: [Architecture](architecture.md) · [Cross-Platform Roadmap](cross_platform_roadmap.md) · [User Guide](usage.md)
