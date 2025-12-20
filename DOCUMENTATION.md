# PolyMaze Architect: Technical & Theoretical Overview

## 1. Abstract
**PolyMaze Architect** is a comprehensive software suite designed to visualize the intersection of **Graph Theory**, **Randomized Algorithms**, and **Heuristic Search**. By implementing the **Strategy Pattern**, it decouples maze topology (the "map") from generation (the "builder") and solving (the "pathfinder").

---

## 2. System Architecture

### 2.1 The Graph-Based Model
The project treats every maze as a **connected graph** $G = (V, E)$.
- **Vertices ($V$)**: Represented by `Cell` objects in a grid.
- **Edges ($E$)**: Represented by `links` between cells.
A "Perfect Maze" is mathematically defined as a **Spanning Tree** of the grid graph—a subgraph that contains all vertices of the original graph but has no cycles and is fully connected.

### 2.2 Design Patterns
- **Strategy Pattern**: Generators and Solvers are interchangeable strategies. This allows the system to support any number of algorithms without modifying the core `Grid` or `View` logic.
- **Generator Pattern**: Algorithms use Python's `yield` keyword to return partial states. This enables "Step-through" animations where the user can watch the algorithm explore and build the maze in real-time.

---

## 3. Maze Generation: The Spanning Tree Problem

### 3.1 Randomized Depth-First Search (Recursive Backtracker)
- **Theory**: Performs a random walk that backtracks when it hits a dead end.
- **Bias**: Highly biased toward long, winding corridors and low branching.
- **Complexity**: $O(V)$.
- **Citation**: [Randomized DFS](https://en.wikipedia.org/wiki/Maze_generation_algorithm#Randomized_depth-first_search)

### 3.2 Randomized Kruskal's Algorithm
- **Theory**: Treats every cell as a separate set and randomly merges sets by removing walls, provided they don't belong to the same set (using **Disjoint-Set/Union-Find** logic).
- **Bias**: Produces many short dead-ends and a "bony" texture.
- **Citation**: [Kruskal's Maze](https://en.wikipedia.org/wiki/Maze_generation_algorithm#Iterative_randomized_Kruskal's_algorithm)

### 3.3 Randomized Prim's Algorithm
- **Theory**: Grows the maze outward from a single starting point by picking random adjacent "frontier" walls.
- **Bias**: Stylistically similar to Kruskal's but grows more "locally."
- **Citation**: [Prim's Algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm#Iterative_randomized_Prim's_algorithm)

### 3.4 Wilson's Algorithm
- **Theory**: Uses **Loop-Erased Random Walks**. It picks a random unvisited cell and performs a walk until it hits the maze, erasing any loops formed.
- **Outcome**: Generates an **unbiased** uniform spanning tree.
- **Citation**: [Wilson's Algorithm](https://en.wikipedia.org/wiki/Wilson%27s_algorithm)

### 3.5 Recursive Division
- **Theory**: A "Top-Down" algorithm. Starts with a large empty chamber and recursively bisects it with walls, leaving a single passage in each wall.
- **Bias**: Produces long straight walls, similar to a city grid with gates.
- **Citation**: [Recursive Division](https://en.wikipedia.org/wiki/Maze_generation_algorithm#Recursive_division_method)

### 3.6 Sidewinder Algorithm
- **Theory**: Processes the maze row by row, deciding whether to continue a horizontal run or "carve" a passage upward.
- **Bias**: Unique because it guarantees a clear path to the top row (no upward dead-ends).
- **Citation**: [Sidewinder Algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm#Simple_algorithms)

---

## 4. Pathfinding: Search & Optimization

### 4.1 Breadth-First Search (BFS)
- **Strategy**: Uninformed search that explores all neighbors at distance $d$ before moving to $d+1$.
- **Efficiency**: Guaranteed to find the **absolute shortest path** in an unweighted grid.
- **Citation**: [BFS](https://en.wikipedia.org/wiki/Breadth-first_search)

### 4.2 A* Search (Informed Search)
- **Strategy**: Uses the function $f(n) = g(n) + h(n)$, where $g(n)$ is the cost from the start and $h(n)$ is a heuristic estimating the cost to the goal.
- **Heuristic**: Uses **Manhattan Distance**: $D = |x_1 - x_2| + |y_1 - y_2|$.
- **Efficiency**: Significantly faster than BFS as it "prunes" the search space by heading toward the goal.
- **Citation**: [A* Search](https://en.wikipedia.org/wiki/A*_search_algorithm)

---

## 5. Topological Geometry

### 5.1 Square (Orthogonal) Grid
Standard 4-way connectivity (North, South, East, West).

### 5.2 Hexagonal Grid
6-way connectivity. Using an **odd-r offset coordinate system**, the hex grid allows for more organic branching and avoids the "blocky" feel of square mazes. Pathfinding on hex grids requires adjusting the Manhattan distance to account for diagonal movement.

---

## 6. Controls & Usage
- **G**: Cycle Grid Shape (Square/Hex).
- **Z**: Cycle Maze Size (Small/Medium/Large).
- **A**: Cycle Generation Algorithm.
- **V**: Toggle Step-by-Step Animation.
- **ENTER**: Generate Maze.
- **S**: Toggle Solution Visibility.
- **TAB**: Cycle Solver (BFS/DFS/A*).
- **Arrows**: Move Player.

---

## 7. References
1. Buck, Jamis. *Mazes for Programmers*. Pragmatic Bookshelf, 2015.
2. Wikipedia contributors. "Maze generation algorithm." Wikipedia, The Free Encyclopedia.
3. Wikipedia contributors. "Spanning tree." Wikipedia, The Free Encyclopedia.