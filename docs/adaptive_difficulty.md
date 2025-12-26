# Adaptive Difficulty System (Adventure Mode)

This document explains the "Light Machine Learning" implementation used in Adventure Mode to provide an adaptive difficulty curve for the player. Instead of a deep neural network, we use a **Heuristic-based Reinforcement Learning (RL)** approach, which is lightweight and highly predictable for game balance.

## 1. Overview
The goal is to automatically adjust the maze complexity based on the player's historical performance.

## 2. The Feedback Loop
The system tracks several metrics after each maze resolution:
- **Solve Time ($T$):** Total seconds from start to finish.
- **Efficiency ($E$):** Ratio of `optimal_path_length / player_steps`.
- **Tool Usage ($U$):** Penalty multiplier for using the Map (`m`) or Solution (`x`).
- **Level Complexity ($C$):** The difficulty rating of the maze just solved.

### Scoring Formula
A "Performance Score" ($P$) is calculated:
$$P = \frac{C}{T \times (1 + U_{penalty})}$$

If $P$ is high, the player is finding the game too easy, and the **Skill Level** increases.

## 3. Difficulty Parameters (The "Action Space")
The engine adjusts the following variables to increase difficulty:
1. **Grid Dimensions:** Incremental increase in rows and columns.
2. **Topology Type:** 
   - *Easy:* Square
   - *Medium:* Triangular / Polar
   - *Hard:* Hexagonal
3. **Levels (3D):** Adding floors increases spatial complexity significantly.
4. **Algorithm Selection:**
   - *Simple (High Bias):* Binary Tree, Sidewinder.
   - *Medium:* Prim's, Aldous-Broder.
   - *Complex (Long Corridors):* Recursive Backtracker, Wilson's.

## 4. Implementation Strategy
- **Persistence:** Progress is stored across three independent slots (`player_profile_1.json`, etc.).
- **Adventure Engine:** A dedicated class (`AdventureEngine`) calculates the next maze's parameters by mapping the current Skill Level to the parameter ranges defined in a difficulty matrix.
- **Profile Selection:** Players can manage multiple careers simultaneously, with the ability to reset progress for any specific slot.
- **Progression:** 
  - **Win:** Level +1.
  - **Perfect Win (No tools, fast):** Level +2.
  - **Struggle (Very slow):** Level +0 (Stay same to practice).

## 5. Benefits
- **Personalized Experience:** Beginners get small, simple mazes; experts get massive, multi-level hexagonal labyrinths.
- **Infinite Gameplay:** The procedural nature ensures the challenge never ends.
