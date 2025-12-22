# renderer.py
import arcade
import math
import config
from maze_topology import Grid, HexCellGrid, TriCellGrid, PolarCellGrid

class MazeRenderer:
    def __init__(self, grid: Grid, cell_radius: float, grid_type: str, top_margin: int, bottom_margin: int):
        self.grid = grid
        self.cell_radius = cell_radius
        self.grid_type = grid_type
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin

    def get_pixel(self, r, c, scale=1.0, offset=(0,0)):
        R = self.cell_radius * scale
        ox, oy = config.SCREEN_WIDTH / 2 + offset[0], (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2 + offset[1]
        
        if self.grid_type == "hex":
            w, h = math.sqrt(3) * R, 1.5 * R
            start_x, start_y = ox - (self.grid.columns + 0.5) * w / 2, oy - ((self.grid.rows - 1) * h + 2 * R) / 2
            return start_x + c*w + (w/2 if r % 2 == 1 else 0) + w/2, start_y + r*h + R
        elif self.grid_type == "tri":
            s = R * math.sqrt(3)
            # Center distance logic for perfect shared base tiling
            grid_w = (self.grid.columns + 1) * (s/2)
            grid_h = self.grid.rows * 1.5 * R
            start_x, start_y = ox - grid_w/2, oy - grid_h/2
            cx = start_x + (c + 1) * (s/2)
            cy = start_y + r * 1.5 * R + (0.5 * R if (r + c) % 2 == 0 else R)
            return cx, cy
        elif self.grid_type == "polar":
            rw = R * 1.5
            radius = (rw * 2) + r * rw + rw/2
            angle = (c * (2 * math.pi / self.grid.columns)) - math.pi / 2
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

    def create_wall_shapes(self, level: int):
        shapes = arcade.shape_list.ShapeElementList()
        processed = set()
        R = self.cell_radius
        for cell in self.grid.each_cell():
            if cell.level != level: continue
            r, c = cell.row, cell.column
            cx, cy = self.get_pixel(r, c)
            if self.grid_type == "rect":
                deltas = [(1, 0, -R, R, R, R), (0, -1, -R, -R, -R, R), (-1, 0, -R, -R, R, -R), (0, 1, R, -R, R, R)]
                for dr, dc, x1, y1, x2, y2 in deltas:
                    n = self.grid.get_cell(r+dr, c+dc, level)
                    if not n or not cell.is_linked(n): self._add_to_list(shapes, (cx+x1, cy+y1), (cx+x2, cy+y2), processed)
            elif self.grid_type == "hex":
                angles, deltas = [30, 90, 150, 210, 270, 330], ([(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (0, 1)] if r % 2 == 0 else [(1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1), (0, 1)])
                for i, (dr, dc) in enumerate(deltas):
                    n = self.grid.get_cell(r+dr, c+dc, level)
                    if not n or not cell.is_linked(n):
                        a1, a2 = math.radians(angles[i]), math.radians(angles[(i+1)%6])
                        self._add_to_list(shapes, (cx+R*math.cos(a1), cy+R*math.sin(a1)), (cx+R*math.cos(a2), cy+R*math.sin(a2)), processed)
            elif self.grid_type == "tri":
                p1, p2, p3 = self.get_tri_verts(r, c, cx, cy, R)
                if (r + c) % 2 == 0:
                    edges = [(p2, p3, (-1, 0)), (p1, p2, (0, 1)), (p1, p3, (0, -1))]
                else:
                    edges = [(p2, p3, (1, 0)), (p1, p2, (0, 1)), (p1, p3, (0, -1))]
                for v1, v2, (dr, dc) in edges:
                    n = self.grid.get_cell(r+dr, c+dc, level)
                    if not n or not cell.is_linked(n): self._add_to_list(shapes, v1, v2, processed)
            elif self.grid_type == "polar":
                rw = R * 1.5
                ir, or_ = (rw * 2) + r * rw, (rw * 2) + (r + 1) * rw
                step = 2 * math.pi / self.grid.columns
                ts, te = c * step - math.pi/2, (c + 1) * step - math.pi/2
                ox, oy = config.SCREEN_WIDTH / 2, (config.SCREEN_HEIGHT - self.top_margin + self.bottom_margin) / 2
                n_in = self.grid.get_cell(r-1, c, level)
                if r == 0 or (not n_in or not cell.is_linked(n_in)): self._add_to_list(shapes, (ox + ir*math.cos(ts), oy + ir*math.sin(ts)), (ox + ir*math.cos(te), oy + ir*math.sin(te)), processed)
                n_out = self.grid.get_cell(r+1, c, level)
                if not n_out or not cell.is_linked(n_out): self._add_to_list(shapes, (ox + or_*math.cos(ts), oy + or_*math.sin(ts)), (ox + or_*math.cos(te), oy + or_*math.sin(te)), processed)
                n_side = self.grid.get_cell(r, (c-1)%self.grid.columns, level)
                if not n_side or not cell.is_linked(n_side): self._add_to_list(shapes, (ox + ir*math.cos(ts), oy + ir*math.sin(ts)), (ox + or_*math.cos(ts), oy + or_*math.sin(ts)), processed)
        return shapes

    def _add_to_list(self, shapes, p1, p2, processed):
        wid = tuple(sorted([(round(p1[0],2), round(p1[1],2)), (round(p2[0],2), round(p2[1],2))]))
        if wid in processed: return
        processed.add(wid)
        shapes.append(arcade.shape_list.create_line(p1[0], p1[1], p2[0], p2[1], config.WALL_COLOR, config.WALL_THICKNESS))