import tempfile
import unittest
from polymaze.core.topology import SquareCellGrid
from polymaze.core.algorithms import MazeGenerator
from polymaze.core.game_state import GameState

class LinkGenerator(MazeGenerator):
    """Links a fixed list of ((r, c, l), (r, c, l)) pairs."""
    def __init__(self, links): self.links = links
    def generate_step(self, grid):
        for a, b in self.links:
            grid.get_cell(*a).link(grid.get_cell(*b)); yield

class FakeClock:
    def __init__(self): self.t = 100.0
    def __call__(self): return self.t

def make_state(rows, cols, levels, links, **kw):
    kw.setdefault("clock", FakeClock())
    return GameState(SquareCellGrid, "rectangle", rows, cols, levels, LinkGenerator(links), "Test",
                     animate=False, braid_pct=0.0, show_trace=True, randomize_start_end=False, **kw)

CORRIDOR = [((0, 0, 0), (0, 1, 0)), ((0, 1, 0), (0, 2, 0))]
UP, DOWN, LEFT, RIGHT = (0, 1), (0, -1), (-1, 0), (1, 0)

class TestGameState(unittest.TestCase):
    def test_walk_corridor_to_win(self):
        clock = FakeClock()
        s = make_state(1, 3, 1, CORRIDOR, clock=clock)
        self.assertEqual((s.start_pos, s.end_pos), ((0, 0, 0), (0, 2, 0)))
        self.assertFalse(s.move(LEFT))  # wall
        self.assertTrue(s.move(RIGHT))
        clock.t += 12
        self.assertTrue(s.move((5, 0.5)))  # any vector length, slightly off-axis
        self.assertTrue(s.game_won)
        self.assertEqual((s.step_count, s.elapsed()), (2, 12))
        self.assertEqual(len(s.path_history), 3)
        self.assertFalse(s.move(LEFT))  # input ignored after win

    def test_stairs(self):
        links = [((0, 0, 0), (0, 1, 0)), ((0, 1, 0), (0, 1, 1)), ((0, 1, 1), (0, 0, 1))]
        s = make_state(1, 2, 2, links)
        self.assertEqual(s.end_pos, (0, 0, 1))
        self.assertEqual(s.stair_options, [])
        self.assertTrue(s.move(RIGHT))
        self.assertEqual(s.stair_options, [(1, "U")])
        self.assertFalse(s.take_stairs("D"))
        self.assertTrue(s.take_stairs("U"))
        self.assertEqual(s.current_level, 1)
        self.assertTrue(s.move(LEFT))
        self.assertTrue(s.game_won)

    def test_stars_required_before_win(self):
        links = [((0, 0, 0), (0, 1, 0)), ((0, 0, 0), (1, 0, 0)), ((1, 0, 0), (1, 1, 0))]
        s = make_state(2, 2, 1, links, collect_stars=True)
        s.stars, s.stars_collected = [s.grid.get_cell(0, 1)], set()
        s.move(UP); s.move(RIGHT)
        self.assertEqual(s.player_cell, s.grid.get_cell(1, 1))
        self.assertFalse(s.game_won)
        s.move(LEFT); s.move(DOWN); s.move(RIGHT)
        self.assertEqual(len(s.stars_collected), 1)
        s.move(LEFT); s.move(UP); s.move(RIGHT)
        self.assertTrue(s.game_won)

    def test_solution_tiers(self):
        s = make_state(1, 3, 1, CORRIDOR)
        s.toggle_solution()
        self.assertTrue(s.show_solution and s.used_solution)
        for _ in range(10): s.step_solver()
        self.assertEqual(s.solution_path, [(0, 0, 0), (0, 1, 0), (0, 2, 0)])
        s.cycle_solver()
        self.assertEqual(s.solver_name, "DFS")
        s.toggle_solution()
        self.assertFalse(s.show_solution)

    def test_animated_generation(self):
        s = GameState(SquareCellGrid, "rectangle", 1, 3, 1, LinkGenerator(CORRIDOR), "Test",
                      animate=True, braid_pct=0.0, show_trace=True, randomize_start_end=False)
        self.assertTrue(s.generating)
        self.assertFalse(s.move(RIGHT))
        while not s.step_generation(): pass
        self.assertEqual(s.player_cell, s.grid.get_cell(0, 0))

    def test_adventure_win_saves_profile(self):
        with tempfile.TemporaryDirectory() as d:
            s = make_state(1, 3, 1, CORRIDOR, mode="ADVENTURE", adventure_slot=2, data_dir=d)
            s.move(RIGHT); s.move(RIGHT)
            self.assertTrue(s.adventure_result["exists"])
            self.assertEqual(s.adventure_result["total_mazes"], 1)
            self.assertIn("rows", s.next_adventure_params())

if __name__ == "__main__":
    unittest.main()
