# maze_widget.py
"""Draws the current floor of a GameState with a follow camera and stencil-masked FOV."""
from typing import Dict, Optional

from kivy.graphics import (Color, InstructionGroup, PopMatrix, PushMatrix,
                           StencilPop, StencilPush, StencilUnUse, StencilUse)
from kivy.uix.widget import Widget

from ..core import settings
from ..core.game_state import GameState
from ..core.geometry import star_points
from .gfx import Camera, circle, fan_mesh, polygon_meshes, polyline, rgba, segment_quads, set_fan

class MazeView(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state: Optional[GameState] = None
        self.camera = Camera(min_zoom=0.1, max_zoom=3.0)
        self.player_xy = (0.0, 0.0)  # animated sprite position
        self.target_xy = (0.0, 0.0)
        self._walls: Dict[int, InstructionGroup] = {}
        self._last_fov_pos = None
        self._composed_key = None
        self._gen_frame = 0

        # Layers, back to front. FOV mode wraps the "inside" layer in a stencil.
        self._fov_begin = InstructionGroup()
        self._inside = InstructionGroup()
        self._fov_end = InstructionGroup()
        self._markers = InstructionGroup()
        self._attenuation = InstructionGroup()
        self._extras = InstructionGroup()
        self._outline = InstructionGroup()
        self._gen_links = InstructionGroup()
        self._fov_mesh_a = fan_mesh((0, 0), [(0, 0)] * 3)
        self._fov_mesh_b = fan_mesh((0, 0), [(0, 0)] * 3)

        with self.canvas:
            PushMatrix()
        for instr in self.camera.instructions(self): self.canvas.add(instr)
        for group in (self._fov_begin, self._inside, self._fov_end, self._markers):
            self.canvas.add(group)
        with self.canvas:
            PopMatrix()
        self.bind(pos=self._on_layout, size=self._on_layout)

    # --- Setup ---
    def set_state(self, state: GameState, top_margin: float, bottom_margin: float):
        self.state = state
        self._walls.clear()
        self._last_fov_pos = None
        self._composed_key = None
        self._top_margin, self._bottom_margin = top_margin, bottom_margin
        self._build_outline()
        self.fit_zoom()
        self.camera.x, self.camera.y = 0.0, 0.0
        if not state.generating: self.on_generation_finished()
        self.refresh()

    def fit_zoom(self):
        if not self.state: return
        mw, mh = self.state.geometry.get_maze_size()
        avail_w = self.width * 0.9
        avail_h = (self.height - self._top_margin - self._bottom_margin) * 0.9
        self.default_zoom = min(avail_w / mw, avail_h / mh, 1.5)
        self.camera.set_zoom(self.default_zoom)

    def on_generation_finished(self):
        self.player_xy = self.target_xy = self.state.player_world_pos()
        self.camera.x, self.camera.y = self.player_xy
        self._gen_links.clear()

    def _build_outline(self):
        self._outline.clear()
        geo = self.state.geometry
        segs = []
        for cell in self.state.grid.each_cell():
            if cell.level != 0: continue
            pts = geo.cell_outline(cell)
            segs += [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
        self._outline.add(Color(*rgba(settings.GRID_OUTLINE_COLOR)))
        for mesh in polygon_meshes(segment_quads(segs, 1.5)): self._outline.add(mesh)

    def _level_walls(self, level: int) -> InstructionGroup:
        group = self._walls.get(level)
        if group is None:
            theme, geo = settings.theme, self.state.geometry
            group = self._walls[level] = InstructionGroup()
            group.add(Color(*rgba(theme.WALL_COLOR)))
            for mesh in polygon_meshes(geo.get_occlusion_polygons(level)): group.add(mesh)
            stairs = geo.stair_triangles(level)
            for kind, color in (("U", settings.STAIR_UP_COLOR), ("D", settings.STAIR_DOWN_COLOR)):
                group.add(Color(*rgba(color)))
                for mesh in polygon_meshes(p for p, k in stairs if k == kind): group.add(mesh)
        return group

    # --- Per frame ---
    def tick(self):
        s = self.state
        if not s: return
        if s.generating:
            if s.step_generation(): self.on_generation_finished()
            else: self._rebuild_generation_links()
        else:
            s.step_solver()
            self.target_xy = s.player_world_pos()
            px, py = self.player_xy; tx, ty = self.target_xy
            self.player_xy = (px + (tx - px) * 0.4, py + (ty - py) * 0.4)
            cx, cy = self.camera.x, self.camera.y
            self.camera.x, self.camera.y = cx + (self.player_xy[0] - cx) * 0.1, cy + (self.player_xy[1] - cy) * 0.1
            if s.show_fov: self._update_fov()
        self.refresh()

    def snap_player(self):
        """Jump the sprite to its cell (used when changing floors)."""
        self.player_xy = self.target_xy = self.state.player_world_pos()

    def _rebuild_generation_links(self):
        # Rebuilding every link is O(cells); throttle it on very large grids.
        self._gen_frame += 1
        size = self.state.grid.size()
        if self._gen_frame % max(1, size // 3000): return
        geo = self.state.geometry
        segs = []
        for cell in self.state.grid.each_cell():
            a = geo.get_pixel(cell.row, cell.column)
            for link in cell.get_links():
                if link.level == cell.level and (link.row, link.column) > (cell.row, cell.column):
                    segs.append((a, geo.get_pixel(link.row, link.column)))
        self._gen_links.clear()
        self._gen_links.add(Color(*rgba(settings.theme.GENERATION_COLOR)))
        for mesh in polygon_meshes(segment_quads(segs, 3)): self._gen_links.add(mesh)

    def _update_fov(self):
        pos = (round(self.player_xy[0], 1), round(self.player_xy[1], 1))
        if pos == self._last_fov_pos: return
        s = self.state
        outline = s.geometry.fov_polygon(pos, s.current_level, radius=s.fov_radius_world(), rays=settings.FOV_RAYS)
        set_fan(self._fov_mesh_a, pos, outline)
        set_fan(self._fov_mesh_b, pos, outline)
        self._last_fov_pos = pos

        self._attenuation.clear()
        step, steps = s.geometry.cell_radius, int(s.fov_radius_cells)
        for i in range(steps, 0, -1):
            alpha = int(100 * (1.0 - (i - 1) / steps))
            self._attenuation.add(Color(1, 1, 1, (alpha // 4) / 255.0))
            self._attenuation.add(circle(pos[0], pos[1], i * step))

    def refresh(self):
        self._compose()
        self._draw_dynamic()
        self.camera.apply()

    def _compose(self):
        s = self.state
        key = (s.generating, s.current_level, s.show_fov, settings.theme.name) if s else None
        if key == self._composed_key: return
        self._composed_key = key
        for g in (self._fov_begin, self._inside, self._fov_end): g.clear()
        if not s: return
        if s.generating:
            self._inside.add(self._outline); self._inside.add(self._gen_links)
            return
        if s.show_fov:
            self._last_fov_pos = None
            self._update_fov()
            self._fov_begin.add(StencilPush()); self._fov_begin.add(Color(1, 1, 1, 1))
            self._fov_begin.add(self._fov_mesh_a); self._fov_begin.add(StencilUse())
            self._inside.add(self._attenuation)
            self._fov_end.add(StencilUnUse()); self._fov_end.add(self._fov_mesh_b); self._fov_end.add(StencilPop())
        self._inside.add(self._level_walls(s.current_level))
        self._inside.add(self._extras)

    def _draw_dynamic(self):
        s = self.state
        self._extras.clear(); self._markers.clear()
        if not s or s.generating: return
        theme, geo, lvl = settings.theme, s.geometry, s.current_level

        if s.show_solution and s.solution_path:
            pts = [geo.get_pixel(r, c) for r, c, lv in s.solution_path if lv == lvl]
            if len(pts) > 1:
                self._extras.add(Color(*rgba(theme.solver_colors[s.current_solver_idx])))
                self._extras.add(polyline(pts, 4))
        if s.show_trace and len(s.path_history) > 1:
            pts = [geo.get_pixel(r, c) for (r, c), lv in s.path_history if lv == lvl]
            if len(pts) > 1:
                self._extras.add(Color(*rgba(theme.PATH_TRACE_COLOR)))
                self._extras.add(polyline(pts, 2))

        # Goal, stars and player stay visible outside the FOV mask
        R = geo.cell_radius
        if lvl == s.end_pos[2]:
            gx, gy = geo.get_pixel(*s.end_pos[:2])
            self._markers.add(Color(*rgba(theme.GOAL_COLOR))); self._markers.add(circle(gx, gy, R * 0.4))
        for star in s.stars:
            if star.level != lvl: continue
            sx, sy = geo.get_pixel(star.row, star.column)
            color = settings.STAR_COLOR if star not in s.stars_collected else settings.STAR_COLLECTED_COLOR
            self._markers.add(Color(*rgba(color)))
            self._markers.add(fan_mesh((sx, sy), star_points(sx, sy, R * 0.5, R * 0.2)))
        self._markers.add(Color(*rgba(theme.PLAYER_COLOR)))
        self._markers.add(circle(self.player_xy[0], self.player_xy[1], R * 0.3))

    def invalidate_theme(self):
        self._walls.clear()
        self._composed_key = None
        if self.state: self._build_outline()

    def _on_layout(self, *_):
        self.camera.apply()

    # --- Camera controls ---
    def zoom_by(self, delta: float):
        self.camera.set_zoom(self.camera.zoom + delta)
        self.camera.apply()

    def reset_zoom(self):
        self.camera.set_zoom(1.0)
        self.camera.apply()

    def player_screen_pos(self):
        return self.camera.world_to_screen(*self.player_xy)
