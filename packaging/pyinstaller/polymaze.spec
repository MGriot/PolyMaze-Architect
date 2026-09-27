# -*- mode: python ; coding: utf-8 -*-
# Desktop build (Windows / macOS / Linux). From the repo root:
#     pyinstaller packaging/pyinstaller/polymaze.spec --noconfirm
# Output: dist/PolyMazeArchitect/ (and dist/PolyMazeArchitect.app on macOS)
import os
import sys

from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, hookspath, runtime_hooks

APP_NAME = "PolyMazeArchitect"
ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(SRC, "polymaze", "assets")

deps = get_deps_minimal(video=None, audio=None, camera=None, spelling=None)

a = Analysis(
    [os.path.join(SRC, "main.py")],
    pathex=[SRC],
    datas=[
        (os.path.join(SRC, "polymaze", "core", "themes.json"), "polymaze/core"),
        (ASSETS, "polymaze/assets"),
    ],
    hookspath=hookspath(),
    runtime_hooks=runtime_hooks(),
    hiddenimports=deps["hiddenimports"],
    excludes=deps["excludes"] + ["tkinter", "arcade", "pyglet"],
    noarchive=False,
)
pyz = PYZ(a.pure)

# PNG icons would need Pillow to convert on macOS; the Windows .ico is used as-is.
icon = os.path.join(ASSETS, "icon.ico") if sys.platform == "win32" else None
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    console=False,
    icon=icon,
)

extra_bins = []
if sys.platform == "win32":
    from kivy_deps import angle, glew, sdl2
    extra_bins = [Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)]

coll = COLLECT(exe, a.binaries, a.datas, *extra_bins, strip=False, upx=False, name=APP_NAME)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="io.github.polymaze.architect",
        info_plist={"CFBundleShortVersionString": "2.0.0", "NSHighResolutionCapable": True},
    )
