import unittest
from src.maze_topology import SquareCellGrid, HexCellGrid, TriCellGrid, PolarCellGrid

class TestTopology(unittest.TestCase):
    def test_square_grid_neighbors(self):
        grid = SquareCellGrid(3, 3)
        center = grid.get_cell(1, 1)
        # Should have 4 neighbors (up, down, left, right)
        self.assertEqual(len(center.neighbors), 4)
        corner = grid.get_cell(0, 0)
        self.assertEqual(len(corner.neighbors), 2)

    def test_hex_grid_neighbors(self):
        grid = HexCellGrid(3, 3)
        # Pointy-top hexes
        center = grid.get_cell(1, 1)
        self.assertEqual(len(center.neighbors), 6)

    def test_tri_grid_neighbors(self):
        grid = TriCellGrid(3, 3)
        # Upright or inverted, center usually has 3 neighbors if internal
        center = grid.get_cell(1, 1)
        self.assertTrue(len(center.neighbors) <= 3)

    def test_polar_grid_neighbors(self):
        grid = PolarCellGrid(3, 8) # 3 rings, 8 segments
        # Center ring (0)
        # Middle ring (1) -> Inward(1), Outward(1), CW(1), CCW(1) = 4
        mid = grid.get_cell(1, 0)
        self.assertEqual(len(mid.neighbors), 4)
        
        # Test Wrap-around
        c0 = grid.get_cell(1, 0)
        c7 = grid.get_cell(1, 7)
        self.assertIn(c7, c0.neighbors) # 0 should be connected to 7 (last)
        self.assertIn(c0, c7.neighbors)

if __name__ == '__main__':
    unittest.main()