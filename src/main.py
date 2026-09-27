# main.py
"""Entry point used by Buildozer (Android) and PyInstaller (desktop). For development: python src/main.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("KIVY_NO_ARGS", "1")  # our own argv is not Kivy's
if sys.stderr is None:  # windowed desktop builds have no console
    os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

from polymaze.ui.app import run  # noqa: E402

if __name__ == "__main__":
    run()
