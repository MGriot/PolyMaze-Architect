# main.py
"""Entry point used by Buildozer (Android) and PyInstaller (desktop). For development: python src/main.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymaze.ui.app import run  # noqa: E402

if __name__ == "__main__":
    run()
