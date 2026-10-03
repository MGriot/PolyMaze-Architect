# Packaging: Desktop Installers & Android APK

PolyMaze Architect ships from a single Kivy codebase. All builds use `src/main.py` as the entry point.

| Target | Tool | Config | Output |
| --- | --- | --- | --- |
| Windows / macOS / Linux bundle | PyInstaller | `packaging/pyinstaller/polymaze.spec` | `dist/PolyMazeArchitect/` (`.app` on macOS) |
| Windows installer + portable zip | Inno Setup 6, `tools/build_windows.ps1` | `packaging/windows/polymaze.iss` | `dist/installer/PolyMazeArchitect-Setup-<ver>.exe`, `…-<ver>-windows-x64-portable.zip` |
| Android | Buildozer (python-for-android) | `buildozer.spec` | `bin/*-release.apk` (signed) / `bin/*-debug.apk` |

**Version**: `__version__` in `src/polymaze/__init__.py` is the only place to change it. The PyInstaller spec (exe version info, macOS plist), Buildozer, the Windows build script and CI all read it from there. CI refuses a tag that doesn't match it.

## 1. App icon & splash

`src/polymaze/assets/` holds `icon.png`, `icon.ico` and `presplash.png`. They are rendered from a seeded maze by:

```bash
python tools/make_assets.py
```

The README and docs screenshots in `docs/img/` are captured from the running app by:

```bash
python tools/capture_screenshots.py
```

It seeds demo profiles in a temporary folder, so your own saves are never touched.

## 2. Desktop (PyInstaller)

Build on the OS you are targeting; PyInstaller does not cross-compile.

### Windows

```powershell
pip install -r requirements-dev.txt
winget install JRSoftware.InnoSetup   # once, for the installer
.\tools\build_windows.ps1
```

The script runs PyInstaller, then Inno Setup, then zips the bundle. Both files land in `dist\installer\`. Without Inno Setup it still builds the portable zip and prints a warning.

- `dist\PolyMazeArchitect\PolyMazeArchitect.exe` runs without Python installed. Its **Properties → Details** tab shows the product name and version.
- The SDL2/GLEW/ANGLE DLLs from `kivy_deps` are bundled automatically by the spec.
- The bundle is a folder (onedir), not a single file. It starts faster and is what the installer packages. The portable zip extracts into a `PolyMazeArchitect\` folder.
- The installer defaults to a per-user install (no admin prompt), adds Start-menu and optional desktop shortcuts, and registers an uninstaller with links to the GitHub page. It closes a running copy before upgrading and replaces the old bundle cleanly. Saves in `%APPDATA%\polymaze` are kept on uninstall.
- Keep `AppId` in `polymaze.iss` unchanged forever: upgrades find the previous install through it.
- The exe and installer are not code-signed, so SmartScreen shows "Windows protected your PC" until the file builds reputation. Users click **More info → Run anyway**.

### macOS / Linux

```bash
pyinstaller packaging/pyinstaller/polymaze.spec --noconfirm
```

- macOS: `hdiutil create -volname "PolyMaze Architect" -srcfolder dist/PolyMazeArchitect.app -ov -format UDZO PolyMazeArchitect.dmg`. The app is unsigned; users right-click → Open the first time. Signing and notarization need an Apple Developer account. CI builds on Apple Silicon (`arm64`).
- Linux: ship `dist/PolyMazeArchitect/` as a `.tar.gz`.

## 3. Android (Buildozer)

Buildozer only runs on Linux. On Windows use **WSL2 (Ubuntu)**:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev cmake libffi-dev libssl-dev
pip install --user buildozer==1.6.0 cython==0.29.37
```

Keep these pins: Buildozer 1.6.0 requires Cython older than 3.0, and Kivy 2.3.1 accepts 0.29.1 to 3.0.11.

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

The app id is `io.github.mgriot.polymazearchitect` (`package.domain` + `package.name`). Don't change it: Android treats a new id as a different app, so it can't update existing installs.

### Release signing

Android only installs an update over an existing app if both are signed with the **same key**. Debug builds use a throwaway key that differs on every machine and CI run. Releases are therefore signed with a permanent release key.

**One-time setup** (Windows, needs a JDK for `keytool` and the GitHub CLI logged in):

```powershell
powershell -ExecutionPolicy Bypass -File tools\setup_android_signing.ps1
```

The script:
1. Creates `~\.polymaze-signing\polymaze-release.keystore` (PKCS12, RSA 4096, alias `polymaze`) with a random password. The alias and password go into `polymaze-release.txt` next to it. Nothing is written inside the repo.
2. Uploads these Actions secrets: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`.

Running it again reuses the existing keystore and re-uploads the secrets.

> **Back up `~\.polymaze-signing\`** (password manager, encrypted drive). If the key is lost, no future version can update existing installs; users would have to uninstall and lose their saves. Never commit the keystore.

**Signed build by hand** (WSL), with the keystore copied into WSL:

```bash
export P4A_RELEASE_KEYSTORE=~/polymaze-release.keystore
export P4A_RELEASE_KEYSTORE_PASSWD='<password>' P4A_RELEASE_KEYALIAS=polymaze P4A_RELEASE_KEYALIAS_PASSWD='<password>'
buildozer android release
```

### Google Play

1. Set `android.release_artifact = aab` in `buildozer.spec`; Play needs an app bundle, not an APK.
2. Bump `android.api` to the target level Google Play currently requires.
3. Build with the same release key as above (`buildozer android release`) and enrol it in Play App Signing as the upload key.

## 4. Continuous integration

`.github/workflows/build.yml`:

- **Every push to master / PR**: runs the core test suite.
- **Manual run** (`gh workflow run build.yml --ref master`): also builds every platform and uploads the files as workflow artifacts. Use it as a dry run before tagging.
- **Tag `v*`**: checks that the tag equals `v` + `__version__`, builds every platform, then publishes a GitHub Release with:
  - `PolyMazeArchitect-Setup-<ver>.exe` and `PolyMazeArchitect-<ver>-windows-x64-portable.zip`
  - `PolyMazeArchitect-<ver>-macos-arm64.dmg`
  - `PolyMazeArchitect-<ver>-linux-x86_64.tar.gz`
  - `PolyMazeArchitect-<ver>-android.apk`: signed with the release key and checked with `apksigner`. Without the signing secrets CI builds `…-android-debug.apk` and shows a warning.
  - `SHA256SUMS.txt`
  - Release notes taken from the matching `## [v<ver>]` section of `CHANGELOG.md`, plus a download table.

## 5. Release checklist

1. Bump `__version__` in `src/polymaze/__init__.py`.
2. Add a `## [v<ver>] - <date>` section to `CHANGELOG.md`. CI fails without it.
3. Commit and push to `master`. Optionally do a dry run with `gh workflow run build.yml --ref master`.
4. Tag and push:
   ```bash
   git tag -a v2.0.0 -m "PolyMaze Architect 2.0.0"
   git push origin v2.0.0
   ```
5. Check the Release page once the workflow finishes.

## 6. Troubleshooting

- **Black window / no GL on a VM**: Kivy needs OpenGL 2.0+. On Windows VMs set `KIVY_GL_BACKEND=angle_sdl2`.
- **Kivy log**: `~/.kivy/logs/` (desktop). On Android use `adb logcat -s python`.
- **Python version**: Kivy 2.3 supports Python 3.8–3.13; build with 3.11 to match the Android toolchain.
- **"App not installed" on Android when updating**: the new APK is signed with a different key than the installed one, e.g. a debug build over a release build. Uninstall first, or install an APK signed with the release key.

See also: [Architecture](architecture.md) · [Cross-Platform Roadmap](cross_platform_roadmap.md) · [User Guide](usage.md)
