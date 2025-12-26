import arcade
import math
import config
from typing import Tuple, List, Set, Optional, Dict
from maze_topology import Grid, Cell

class MazeRenderer:
    def __init__(self, grid: Grid, cell_radius: float, grid_type: str, top_margin: int, bottom_margin: int):
        self.grid = grid
        self.cell_radius = cell_radius
        self.grid_type = grid_type
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.inset_factor = 0.8 
        self._segment_cache: Dict[int, List[Tuple[Tuple[float, float], Tuple[float, float]]]] = {}

    def get_pixel(self, r, c, scale=1.0, offset=(0,0)):
        R = self.cell_radius * scale
        ox, oy = config.SCREEN_WIDTH / 2 + offset[0], (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2 + offset[1]
        
        if self.grid_type == "hex":
            w, h = math.sqrt(3) * R, 1.5 * R
            start_x, start_y = ox - (self.grid.columns + 0.5) * w / 2, oy - ((self.grid.rows - 1) * h + 2 * R) / 2
            return start_x + c*w + (w/2 if r % 2 == 1 else 0) + w/2, start_y + r*h + R
        elif self.grid_type == "tri":
            s = R * math.sqrt(3)
            grid_w = (self.grid.columns + 1) * (s/2)
            grid_h = self.grid.rows * 1.5 * R
            start_x, start_y = ox - grid_w/2, oy - grid_h/2
            cx = start_x + (c + 1) * (s/2)
            cy = start_y + r * 1.5 * R + (0.5 * R if (r + c) % 2 == 0 else R)
            return cx, cy
        elif self.grid_type == "polar":
            rw = R * 1.5
            radius = (rw * 2) + r * rw + rw/2
            step = 2 * math.pi / self.grid.columns
            angle = ((c + 0.5) * step) - math.pi / 2
            return ox + radius * math.cos(angle), oy + radius * math.sin(angle)
        else: # rect
            s = R * 2
            start_x, start_y = ox - (self.grid.columns * s)/2, oy - (self.grid.rows * s)/2
            return start_x + c*s + R, start_y + r*s + R

    def get_tri_verts(self, r, c, cx, cy, R):
        s = R * math.sqrt(3)
        if (r + c) % 2 == 0: # Upright ^
            return (cx, cy + R), (cx + s/2, cy - R/2), (cx - s/2, cy - R/2)
        else: # Inverted v
            return (cx, cy - R), (cx + s/2, cy + R/2), (cx - s/2, cy + R/2)

    def _get_segments(self, level: int) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """Lazy-load and cache flattened segments for the level."""
        if level in self._segment_cache:
            return self._segment_cache[level]
        
        polygons = self.get_occlusion_polygons(level)
        segments = []
        for poly in polygons:
            for i in range(len(poly)):
                segments.append((poly[i], poly[(i + 1) % len(poly)]))
        
        self._segment_cache[level] = segments
        return segments

    def get_occlusion_polygons(self, level: int, scale: float = 1.0, offset: Tuple[float, float] = (0, 0), thickness_mult: float = 1.0) -> List[List[Tuple[float, float]]]:
        """Calculates solid wall geometry using a Post-and-Beam model."""
        polygons = []
        R = self.cell_radius * scale
        T = R * (1.0 - self.inset_factor) * thickness_mult
        posts = {} 

        def add_post(px, py):
            key = (round(px, 2), round(py, 2))
            if key not in posts:
                posts[key] = [(px - T, py - T), (px + T, py - T), (px + T, py + T), (px - T, py + T)]

        if self.grid_type == "rect":
            s = R * 2
            ox, oy = config.SCREEN_WIDTH / 2 + offset[0], (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2 + offset[1]
            start_x, start_y = ox - (self.grid.columns * s)/2, oy - (self.grid.rows * s)/2
            for r in range(self.grid.rows + 1):
                for c in range(self.grid.columns + 1):
                    px, py = start_x + c*s, start_y + r*s
                    add_post(px, py)
                    if r < self.grid.rows:
                        c1, c2 = self.grid.get_cell(r, c-1, level), self.grid.get_cell(r, c, level)
                        if not c1 or not c2 or not c1.is_linked(c2):
                            polygons.append([(px - T, py + T), (px + T, py + T), (px + T, py + s - T), (px - T, py + s - T)])
                    if c < self.grid.columns:
                        c1, c2 = self.grid.get_cell(r-1, c, level), self.grid.get_cell(r, c, level)
                        if not c1 or not c2 or not c1.is_linked(c2):
                            polygons.append([(px + T, py - T), (px + s - T, py - T), (px + s - T, py + T), (px + T, py + T)])
        else:
            for cell in self.grid.each_cell():
                if cell.level != level: continue
                cx, cy = self.get_pixel(cell.row, cell.column, scale, offset)
                r, c = cell.row, cell.column
                edges = []
                if self.grid_type == "hex":
                    angles, deltas = [30, 90, 150, 210, 270, 330], ([(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (0, 1)] if r % 2 == 0 else [(1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (0, 1)])
                    for i, (dr, dc) in enumerate(deltas):
                        p1 = (cx + R * math.cos(math.radians(angles[i])), cy + R * math.sin(math.radians(angles[i])))
                        p2 = (cx + R * math.cos(math.radians(angles[(i+1)%6])), cy + R * math.sin(math.radians(angles[(i+1)%6])))
                        edges.append((p1, p2, (dr, dc)))
                elif self.grid_type == "tri":
                    p1, p2, p3 = self.get_tri_verts(r, c, cx, cy, R)
                    edges = [(p2, p3, (-1, 0)), (p1, p2, (0, 1)), (p1, p3, (0, -1))] if (r + c) % 2 == 0 else [(p2, p3, (1, 0)), (p1, p2, (0, 1)), (p1, p3, (0, -1))]
                elif self.grid_type == "polar":
                    rw = R * 1.5; ir, or_ = (rw * 2) + r * rw, (rw * 2) + (r + 1) * rw
                    step = 2 * math.pi / self.grid.columns; ts, te = c * step - math.pi/2, (c + 1) * step - math.pi/2
                    ox, oy = config.SCREEN_WIDTH / 2 + offset[0], (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2 + offset[1]
                    v1, v2 = (ox+ir*math.cos(ts), oy+ir*math.sin(ts)), (ox+ir*math.cos(te), oy+ir*math.sin(te))
                    v3, v4 = (ox+or_*math.cos(te), oy+or_*math.sin(te)), (ox+or_*math.cos(ts), oy+or_*math.sin(ts))
                    edges = [(v1, v2, (-1, 0)), (v3, v4, (1, 0)), (v1, v4, (0, -1)), (v2, v3, (0, 1))]

                for v1, v2, (dr, dc) in edges:
                    target_c = (c + dc) % self.grid.columns if self.grid_type == "polar" else c + dc
                    n = self.grid.get_cell(r + dr, target_c, level)
                    if not n or not cell.is_linked(n):
                        add_post(v1[0], v1[1]); add_post(v2[0], v2[1])
                        dx, dy = v2[0] - v1[0], v2[1] - v1[1]; dist = math.sqrt(dx*dx + dy*dy)
                        if dist > 0:
                            nx, ny = -dy/dist * T, dx/dist * T
                            polygons.append([(v1[0]-nx, v1[1]-ny), (v1[0]+nx, v1[1]+ny), (v2[0]+nx, v2[1]+ny), (v2[0]-nx, v2[1]-ny)])
        return list(posts.values()) + polygons

    def create_fov_geometry(self, origin: Tuple[float, float], level: int, radius: float = 300) -> arcade.shape_list.ShapeElementList:
        """Low-Poly FOV with safety padding for thick walls and corner stability."""
        all_segments = self._get_segments(level)
        active_segments, r2 = [], (radius * 1.5) ** 2
        T = self.cell_radius * (1.0 - self.inset_factor)
        
        for p1, p2 in all_segments:
            d1, d2 = (p1[0]-origin[0])**2 + (p1[1]-origin[1])**2, (p2[0]-origin[0])**2 + (p2[1]-origin[1])**2
            if d1 < r2 or d2 < r2:
                active_segments.append((p1, p2))

        outer_points = []
        for i in range(60):
            angle = math.radians(i * 6)
            dx, dy, min_t = math.cos(angle), math.sin(angle), radius
            for p1, p2 in active_segments:
                t = self._ray_segment_intersect(origin, (dx, dy), p1, p2)
                if t is not None and t < min_t:
                    min_t = t + (T * 0.4) # Push slightly into wall for watertight mask
            outer_points.append((origin[0] + dx * min_t, origin[1] + dy * min_t))
        
        shapes = arcade.shape_list.ShapeElementList()
        if len(outer_points) > 2:
            shapes.append(arcade.shape_list.create_polygon(outer_points, (255, 255, 255, 255)))
        return shapes

    def _ray_segment_intersect(self, or_pos, or_dir, p1, p2):
        v1, v2, v3 = (or_pos[0] - p1[0], or_pos[1] - p1[1]), (p2[0] - p1[0], p2[1] - p1[1]), (-or_dir[1], or_dir[0])
        dot = v2[0] * v3[0] + v2[1] * v3[1]
        if abs(dot) < 1e-9: return None
        t = (v2[0] * v1[1] - v2[1] * v1[0]) / dot
        u = (v1[0] * v3[0] + v1[1] * v3[1]) / dot
        return t if (t >= 0 and 0 <= u <= 1) else None

    def create_wall_shapes(self, level: int, scale=1.0, offset=(0,0), thickness_mult=1.0):
        shapes = arcade.shape_list.ShapeElementList()
        polygons = self.get_occlusion_polygons(level, scale, offset, thickness_mult)
        for poly in polygons: shapes.append(arcade.shape_list.create_polygon(poly, config.WALL_COLOR))
        return shapes

    def create_stair_shapes(self, level: int, scale=1.0, offset=(0,0)):
        shapes = arcade.shape_list.ShapeElementList()
        size = 8 * scale
        for cell in self.grid.each_cell():
            if cell.level != level: continue
            cx, cy = self.get_pixel(cell.row, cell.column, scale, offset)
            for link in cell.get_links():
                if link.level > cell.level: shapes.append(arcade.shape_list.create_polygon([(cx, cy+size), (cx-size, cy-size*0.75), (cx+size, cy-size*0.75)], arcade.color.AZURE))
                elif link.level < cell.level: shapes.append(arcade.shape_list.create_polygon([(cx, cy-size), (cx-size, cy+size*0.75), (cx+size, cy+size*0.75)], arcade.color.BROWN))
        return shapes

    def get_maze_size(self) -> Tuple[float, float]:
        R = self.cell_radius
        if self.grid_type == "hex":
            w, h = math.sqrt(3) * R, 1.5 * R
            return (self.grid.columns + 0.5) * w, (self.grid.rows - 1) * h + 2 * R
        elif self.grid_type == "tri":
            s = R * math.sqrt(3)
            return (self.grid.columns + 1) * (s/2), self.grid.rows * 1.5 * R + 0.5 * R
        elif self.grid_type == "polar":
            rw = R * 1.5; max_r = (rw * 2) + self.grid.rows * rw
            return max_r * 2, max_r * 2
        else: # rect
            s = R * 2; return self.grid.columns * s, self.grid.rows * s