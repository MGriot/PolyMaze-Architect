# -*- mode: python ; coding: utf-8 -*-
# Desktop build (Windows / macOS / Linux). From the repo root:
#     pyinstaller packaging/pyinstaller/polymaze.spec --noconfirm
# Output: dist/PolyMazeArchitect/ (and dist/PolyMazeArchitect.app on macOS)
import os
import re
import sys

from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, hookspath, runtime_hooks

APP_NAME = "PolyMazeArchitect"
ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(SRC, "polymaze", "assets")

# Single source of truth for the version: src/polymaze/__init__.py
with open(os.path.join(SRC, "polymaze", "__init__.py"), encoding="utf-8") as f:
    VERSION = re.search(r'__version__ = ["\']([^"\']+)["\']', f.read()).group(1)

# Name the window/clipboard providers instead of letting Kivy detect them: detection opens a real
# window, which fails on headless CI (no X server on Linux; a blocking "OpenGL 2.0 not found" dialog
# on Windows runners). Image and text are still auto-detected; that needs no window.
deps = get_deps_minimal(window="sdl2", clipboard=["sdl2", "dummy"], video=None, audio=None, camera=None, spelling=None)

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

def windows_version_info():
    """Details tab of the .exe Properties dialog."""
    from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct, StringTable,
                                                     VarFileInfo, VarStruct, VSVersionInfo)
    nums = tuple(int(n) for n in re.findall(r"\d+", VERSION)[:4])
    nums += (0,) * (4 - len(nums))
    strings = {
        "CompanyName": "MGriot",
        "FileDescription": "PolyMaze Architect",
        "FileVersion": VERSION,
        "InternalName": APP_NAME,
        "LegalCopyright": "MGriot",
        "OriginalFilename": f"{APP_NAME}.exe",
        "ProductName": "PolyMaze Architect",
        "ProductVersion": VERSION,
    }
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=nums, prodvers=nums),
        kids=[StringFileInfo([StringTable("040904B0", [StringStruct(k, v) for k, v in strings.items()])]),
              VarFileInfo([VarStruct("Translation", [0x0409, 1200])])],
    )

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
    version=windows_version_info() if sys.platform == "win32" else None,
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
        bundle_identifier="io.github.mgriot.polymazearchitect",
        version=VERSION,
        info_plist={"CFBundleShortVersionString": VERSION, "NSHighResolutionCapable": True},
    )
