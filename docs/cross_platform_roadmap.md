# Cross-Platform Conversion Roadmap

This document outlines the strategy for porting **PolyMaze Architect** from a desktop-only application (Python + Arcade) to a cross-platform mobile and desktop application (Android, iOS, Windows, Linux, MacOS).

## 1. Primary Technical Objective
Replace the **Arcade** library (which only supports Desktop) with **Kivy**, an industry-standard Python framework for cross-platform development that supports touch interfaces and mobile GPUs.

## 2. Core Porting Strategy: "Brain vs. Eyes"
The project must be strictly decoupled into two layers:

### A. The Brain (Logic Layer) - 100% Reuse
The following files are "Pure Python" and will be moved into a core package that has **no dependencies** on UI libraries:
- `maze_topology.py`: Grid mathematics and graph structures.
- `maze_algorithms.py`: Spanning tree generators and A*/BFS solvers.
- `adventure_engine.py`: Personalized skill profiles and adaptive learning model.

### B. The Eyes (Renderer Layer) - Full Rewrite
The rendering and input handling must be rebuilt for Kivy:
- `renderer.py`: Rewrite Arcade's `ShapeElementList` and vertex calculations using Kivy's `Canvas` instructions and `Vertex Instructions`.
- `views.py`: Rebuild the menu system using Kivy's `Widget` and `Layout` system. Replace keyboard handlers with a unified input manager (Keyboard for Desktop, Virtual D-Pad/Touch for Mobile).

## 3. Platform-Specific Tools
- **Android/iOS**: Use **Buildozer** to compile the Python code into an ARM-compatible binary (`.apk`, `.aab`, or `.ipa`).
- **Windows/Linux/Mac**: Use **PyInstaller** to bundle the app into a standalone executable.

## 4. Key Technical Hurdles
1. **Stencil Management**: Migrate the "Fog of War" and "Field of View" logic from Arcade's raw OpenGL stencil calls to Kivy's `StencilPush` and `StencilPop` instructions.
2. **Dynamic Paths**: Update `adventure_engine.py` to detect the OS and use `app.user_data_dir` for saving profiles, as mobile OSs restrict direct file writing.
3. **Responsive UI**: Replace fixed screen coordinates with a relative layout system to handle varying aspect ratios (e.g., 16:9 phones vs. 4:3 tablets).

## 5. Phased Implementation Plan
1. **Refactor Core**: Move logic to `src/core/` and ensure zero `import arcade` statements.
2. **Kivy Prototype**: Build a basic "Main Menu" and "Square Grid" renderer in Kivy.
3. **Input Layer**: Implement the touch-based navigation system.
4. **Mobile Packaging**: Run the first Buildozer pass to test performance on an Android device.
