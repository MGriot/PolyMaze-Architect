# Adaptive Difficulty System (Adventure Mode)

This document explains the **Personalized Skill Profile** system used in Adventure Mode to provide a highly adaptive and personalized experience. Instead of a linear level, the system tracks a multidimensional vector of the player's abilities.

## 1. The Multidimensional Profile
The engine tracks four distinct skill vectors for each player:
- **Spatial Complexity:** Ability to navigate large grids and multi-level (3D) structures.
- **Perceptual Awareness:** Skill in navigating with limited visibility (FOV) and hidden maps (Fog of War).
- **Structural Adaptation:** Mastery of different grid topologies (Polar, Hex, Tri) and complex algorithms.
- **Efficiency:** Navigational logic, measured by the ability to find paths without dead-ends (Braiding) or tool assistance.
- **Collection Proficiency:** Skill in locating and retrieving optional objectives (Stars) within the structure.

## 2. The Learning Feedback Loop
After every maze, the engine calculates a **Performance Score ($P_{score}$)**:

1. **Velocity Check:** Compares solve time against an "expected time" for that specific maze complexity.
2. **Collection Bonus:** Each star collected provides a multiplier to the final performance score.
3. **Tool Penalty:** Heavy penalties for using the AI Solution (80% reduction) or the Map (40% reduction).
4. **Momentum:** Successive high-velocity wins without tools trigger a "Momentum" state, accelerating difficulty growth.

### Growth Formula
Skills grow proportionally to $P_{score}$. If a player struggles (low $P_{score}$), the specific skill vector stabilizes or slightly decays to ensure the game remains fun. 

**Manual Reset:** Using the `BACKSPACE` key to exit a maze prematurely results in an immediate XP penalty and a slight decay across all skill vectors.

## 3. Dynamic Difficulty Adjustment (DDA)
The engine translates the skill profile into maze parameters:
- **Spatial Skill** $\rightarrow$ Rows, Columns, Floors.
- **Perception Skill** $\rightarrow$ Triggers **Fog of War** and shrinks **FOV Radius**.
- **Collection Skill** $\rightarrow$ Triggers **Star Collection** challenges.
- **Structural Skill** $\rightarrow$ Unlocks Hex/Polar topologies and harder algorithms.
- **Efficiency Skill** $\rightarrow$ Increases **Braid Factor** (less dead ends).

## 4. Momentum & Grace Periods
- **Momentum:** Winning 3+ times efficiently increases the `growth_rate`.
- **Grace Period:** Significant struggles (very slow times or heavy tool usage) stop all growth, allowing the player to practice at their current level without further complexity spikes.

## 5. Benefits
- **Personalized Challenge:** A player who is good at logic but poor at spatial memory will get large, well-lit mazes.
- **Anti-Frustration:** The system detects when a player is "guessing" (heavy tool use) and adjusts the perceptual challenge down.
- **Infinite Scaling:** There are no hard level caps; the engine scales until the hardware limits are reached.
