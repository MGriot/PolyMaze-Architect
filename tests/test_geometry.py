import math
import unittest
from polymaze.core.topology import SquareCellGrid, HexCellGrid, TriCellGrid, PolarCellGrid
from polymaze.core.algorithms import RecursiveBacktracker
from polymaze.core.catalog import grid_type_for
from polymaze.core.geometry import MazeGeometry, star_points, column_label

def _maze(grid_class, rows=7, cols=9, levels=1):
    grid = grid_class(rows, cols, levels)
    RecursiveBacktracker().generate(grid)
    return MazeGeometry(grid, 30.0, grid_type_for(grid_class))

class TestGeometry(unittest.TestCase):
    def test_maze_is_centred_on_origin(self):
        geo = _maze(SquareCellGrid, rows=4, cols=6)
        xs = [geo.get_pixel(r, c)[0] for r in range(4) for c in range(6)]
        ys = [geo.get_pixel(r, c)[1] for r in range(4) for c in range(6)]
        self.assertAlmostEqual((min(xs) + max(xs)) / 2, 0.0)
        self.assertAlmostEqual((min(ys) + max(ys)) / 2, 0.0)

    def test_offset_translates_pixels(self):
        geo = _maze(HexCellGrid)
        base, moved = geo.get_pixel(2, 3), geo.get_pixel(2, 3, offset=(100, -50))
        self.assertAlmostEqual(moved[0] - base[0], 100)
        self.assertAlmostEqual(moved[1] - base[1], -50)

    def test_wall_polygons_are_convex(self):
        # The Kivy mesh builder fan-triangulates walls, which is only valid for convex polygons.
        for gc in (SquareCellGrid, HexCellGrid, TriCellGrid, PolarCellGrid):
            geo = _maze(gc)
            for poly in geo.get_occlusion_polygons(0):
                signs = set()
                for i in range(len(poly)):
                    (x1, y1), (x2, y2), (x3, y3) = poly[i], poly[(i+1) % len(poly)], poly[(i+2) % len(poly)]
                    cross = (x2-x1)*(y3-y2) - (y2-y1)*(x3-x2)
                    if abs(cross) > 1e-6: signs.add(cross > 0)
                self.assertLessEqual(len(signs), 1, f"non-convex wall polygon in {gc.__name__}")

    def test_star_points_and_labels(self):
        self.assertEqual(len(star_points(0, 0, 10, 4)), 10)
        self.assertEqual([column_label(i) for i in (0, 25, 26, 27)], ["A", "Z", "AA", "AB"])

class TestFOVPolygon(unittest.TestCase):
    def test_ray_count_and_radius_bound(self):
        for gc in (SquareCellGrid, HexCellGrid, TriCellGrid, PolarCellGrid):
            geo = _maze(gc)
            cell = next(geo.grid.each_cell())
            origin = geo.get_pixel(cell.row, cell.column)
            radius = geo.cell_radius * 6
            poly = geo.fov_polygon(origin, 0, radius=radius, rays=60)
            self.assertEqual(len(poly), 60)
            slack = geo.wall_thickness * 0.4 + 1e-6
            for x, y in poly:
                self.assertLessEqual(math.hypot(x - origin[0], y - origin[1]), radius + slack)

    def test_walls_block_view(self):
        # A 1x3 strip with no links: every ray stops at the walls of the middle cell.
        grid = SquareCellGrid(1, 3)
        geo = MazeGeometry(grid, 30.0, "rect")
        origin = geo.get_pixel(0, 1)
        for x, y in geo.fov_polygon(origin, 0, radius=1000):
            self.assertLess(math.hypot(x - origin[0], y - origin[1]), 60)

    def test_open_space_reaches_radius(self):
        # Standing in an empty floor far from any wall, rays travel the full radius.
        grid = SquareCellGrid(1, 1)
        geo = MazeGeometry(grid, 30.0, "rect")
        for x, y in geo.fov_polygon((5000, 5000), 0, radius=50):
            self.assertAlmostEqual(math.hypot(x - 5000, y - 5000), 50)

    def test_ray_segment_intersection(self):
        hit = MazeGeometry._ray_segment_intersect((0, 0), (1, 0), (10, -5), (10, 5))
        self.assertAlmostEqual(hit, 10)
        self.assertIsNone(MazeGeometry._ray_segment_intersect((0, 0), (-1, 0), (10, -5), (10, 5)))
        self.assertIsNone(MazeGeometry._ray_segment_intersect((0, 0), (1, 0), (10, 1), (10, 5)))

if __name__ == "__main__":
    unittest.main()
