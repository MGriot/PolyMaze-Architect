# Maze Theory & Algorithms

## 1. The Mathematical Maze
In graph theory, a **perfect maze** is a **Spanning Tree** of a grid graph.
- Every cell is a node ($V$).
- Every path is an edge ($E$).
- A spanning tree is a subset of edges that connects all nodes without any cycles.

## 2. Generation Algorithms
For a detailed analysis of performance and visual biases, see [Generation Algorithms - Trade-offs](algorithms.md).

### Randomized Depth-First Search (Recursive Backtracker)
- **Mechanism**: A random walk that backtracks when trapped.
- **Visuals**: Long, winding corridors with very few branches.
- **Complexity**: $O(N)$ where $N$ is the number of cells.

### Wilson's Algorithm
- **Mechanism**: Loop-erased random walks.
- **Result**: Generates a **Uniform Spanning Tree** (perfectly unbiased).
- **Efficiency**: Slower than others but mathematically superior for unbiased results.

### Kruskal's & Prim's
- **Mechanism**: Growing the maze by adding edges based on random weights or set merging.
- **Visuals**: High branching factor, creating a "bony" or "cracked" texture.

### Recursive Division
- **Mechanism**: Starts with an empty space and recursively adds walls with one hole.
- **Visuals**: Distinct grid-like structure with long straight corridors.

## 3. Pathfinding (Solving)

### Breadth-First Search (BFS)
Finds the **shortest path** guaranteed. It explores layer by layer.

### A* (A-Star)
- Uses a **Heuristic** (Manhattan distance) to guide the search toward the goal.
- In 3D mode, the heuristic is adjusted: $|x_1-x_2| + |y_1-y_2| + |z_1-z_2| \times 5$.
