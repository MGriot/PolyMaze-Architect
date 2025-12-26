# Maze Generation Algorithms - Trade-offs

This document outlines the performance characteristics and visual biases of the algorithms implemented in PolyMaze Architect. For the underlying graph theory, see [Maze Theory](theory.md).

## 1. Recursive Backtracker (DFS)
- **Visuals**: Long, winding corridors with few dead ends.
- **Trade-offs**: Very simple to implement. Memory usage scales with maze size (recursion stack).
- **Ideal for**: Traditional "hard" mazes.

## 2. Randomized Prim's
- **Visuals**: Many short corridors and numerous dead ends. Looks "organic" or like a crystal growth.
- **Trade-offs**: Fast, but doesn't produce uniform spanning trees.
- **Ideal for**: Decorative mazes.

## 3. Aldous-Broder
- **Visuals**: Uniform Spanning Tree (mathematically unbiased).
- **Trade-offs**: Extremely inefficient. Can take a very long time to finish as it relies on a random walk hitting every single cell.
- **Ideal for**: Scientific/Mathematical analysis of mazes.

## 4. Wilson's
- **Visuals**: Uniform Spanning Tree.
- **Trade-offs**: More efficient than Aldous-Broder but has a "slow start" as the first path is hard to find.
- **Ideal for**: Unbiased mazes without the AB performance penalty.

## 5. Eller's Algorithm
- **Visuals**: No specific visual bias in 2D, but capable of creating infinitely long mazes.
- **Trade-offs**: **Highly Efficient**. Only requires memory for one row at a time. Complex logic involving set merging.
- **Ideal for**: Extremely large mazes.

## 6. Hunt and Kill
- **Visuals**: Similar to Recursive Backtracker but has a distinct "hunting" pattern when stuck.
- **Trade-offs**: Slower than Backtracker because of the search phase, but uses less memory (no stack required).
- **Ideal for**: Medium-sized mazes where memory is a concern.

## 7. Sidewinder
- **Visuals**: Characterized by a long unbroken corridor at the top and vertical biases.
- **Trade-offs**: Very fast and memory efficient (one row).
- **Ideal for**: Real-time generation.

## 8. Binary Tree
- **Visuals**: Strong diagonal bias. Paths always lead toward two directions (e.g., North and East).
- **Trade-offs**: Simplest possible algorithm. Extremely fast.
- **Ideal for**: Beginners learning procedural generation.

## 9. Recursive Division
- **Visuals**: Long straight walls. Looks like a collection of rooms.
- **Trade-offs**: Not a "perfect" maze in the same way as others (tends to create rooms).
- **Ideal for**: Dungeon-like environments.

## 10. Kruskal's
- **Visuals**: Balanced corridors.
- **Trade-offs**: Reliable and efficient. Uses union-find structures.
- **Ideal for**: High-quality, fast mazes.
