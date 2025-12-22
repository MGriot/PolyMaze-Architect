import unittest
from src.maze_topology import SquareCellGrid
from src.maze_algorithms import HuntAndKill, Ellers, RecursiveBacktracker

class TestAlgorithms(unittest.TestCase):
    def test_hunt_and_kill(self):
        grid = SquareCellGrid(5, 5)
        algo = HuntAndKill()
        algo.generate(grid)
        # Verify perfect maze (no loops, fully connected)
        # Simple check: size-1 links for full spanning tree?
        # Num links should be size - 1 for a tree
        total_links = sum(len(c.get_links()) for c in grid.each_cell()) // 2
        self.assertEqual(total_links, grid.size() - 1)

    def test_ellers(self):
        grid = SquareCellGrid(5, 5)
        algo = Ellers()
        algo.generate(grid)
        total_links = sum(len(c.get_links()) for c in grid.each_cell()) // 2
        self.assertEqual(total_links, grid.size() - 1)

if __name__ == '__main__':
    unittest.main()