# User Guide & Controls

## Launching the Application
To start PolyMaze Architect, ensure your virtual environment is active and use the entry script:
```bash
python run_app.py
```
This script automatically configures the necessary paths.

## Main Menu
- **ADVENTURE**: Progress through an adaptive challenge. See [Adaptive Difficulty](adaptive_difficulty.md) for details.
- **CREATIVE / TRAINING**: Customize every aspect of the maze.

## Profile Selection (Adventure Mode)
- **UP/DOWN**: Select between **3 Profile Slots**.
- **ENTER**: Play with the selected profile.
- **DEL**: Reset/Overwrite the selected profile.
- **ESC**: Return to Main Menu.

## Creative / Training Setup
Navigate using the following keys:
- **G**: Cycle Cell Topology (**Square, Hexagonal, Triangular, Polar**).
- **F**: Cycle Maze Form (**Rectangle, Circle, Triangle, Hexagon**).
- **Z**: Cycle Maze Size (Small, Medium, Large, X-Large, Epic, Colossal).
- **A**: Cycle Generation Algorithm (10 available).
- **L**: Set number of **3D Levels** (up to 6 floors).
- **M**: Toggle **Multi-Path** (Braided) mode.
- **V**: Toggle **Generation Animation**.
- **E**: Toggle **Random Endpoints**.
- **R**: Toggle **Trace** (Breadcrumbs).
- **X**: Toggle **Explorative Map** (Hides unvisited areas in Map view).
- **S**: Toggle **Star Collection** (Spawn 3 stars that must be collected before exit).
- **T**: Toggle **Dark/Light** theme.
- **ENTER**: Begin Architecting.
- **ESC**: Return to Main Menu.

## Exploration (In-Game)
- **WASD / Arrow Keys**: Discrete, cell-based movement with spatial alignment.
- **U / D**: Move **Up** or **Down** levels when standing on a Stair.
- **X**: AI Solution Animation. 
    - *1st Press*: Show path to Exit.
    - *2nd Press*: Show path to all Stars + Exit (if Stars active).
    - *3rd Press*: Clear Solution.
- **V**: Toggle **Dynamic FOV** (Creative mode only).
- **BACKSPACE**: **Reset Run**. Exits current maze (Applies XP penalty in Adventure).
- **+/-**: **Zoom In / Out** (0.1x to 3.0x).
- **0**: Reset Zoom to 1.0x.
- **TAB**: Change the AI solver algorithm (BFS, DFS, A*).
- **M**: Toggle **Architectural Map** (Vertical exploded view).
- **P**: **Print** (Save current view as PNG).
- **ESC**: Back to Menu (Profile Select or Creative Setup).

## The HUD (Heads-Up Display)
The HUD bar at the top provides real-time information:
- **Top Left**: Current generation algorithm and your floor location.
- **Top Right**: 
    - **STEPS**: Number of cells moved.
    - **TIME**: Total time spent exploring the current maze.
    - **ZOOM**: Current magnification level.

## Visual Indicators
- **Azure Triangle**: Stair leading Up.
- **Brown Triangle**: Stair leading Down.
- **Gold Circle**: Goal (Exit).
- **Green Circle**: Your Avatar (Architect).
- **Thin Grey Outline**: Underlying grid structure (during generation).
- **Blue Line**: Generation progress.
