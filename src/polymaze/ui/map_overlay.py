# map_overlay.py
"""Exploded architectural view: every floor stacked vertically, optionally masked to explored cells."""
import math
from typing import Optional

from kivy.graphics import (Color, InstructionGroup, PopMatrix, PushMatrix, Rectangle,
                           StencilPop, StencilPush, StencilUnUse, StencilUse)
from kivy.uix.widget import Widget

from ..core import settings
from ..core.game_state import GameState
from ..core.geometry import column_label, star_points
from .controls import Gestures
from .gfx import Camera, circle, fan_mesh, polygon_meshes, polyline, rgba, text_rect, u

class MapView(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state: Optional[GameState] = None
        self.camera = Camera(min_zoom=0.02, max_zoom=2.0)
        self._static = InstructionGroup()
        self._mask = InstructionGroup()
        self._dynamic = InstructionGroup()
        self._mask_a = InstructionGroup(); self._mask_b = InstructionGroup()
        self._stencil_begin = InstructionGroup(); self._stencil_end = InstructionGroup()
        self._visited_count = -1
        self._needs_fit = False

        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 0.92)
            self._bg = Rectangle()
        with self.canvas:
            PushMatrix()
        for instr in self.camera.instructions(self): self.canvas.add(instr)
        for g in (self._stencil_begin, self._static, self._dynamic, self._stencil_end): self.canvas.add(g)
        with self.canvas:
            PopMatrix()
        self._overlay = InstructionGroup()
        self.canvas.after.add(self._overlay)

        self.gestures = Gestures(self, on_drag=self._drag, on_pinch=self._pinch,
                                 on_pinch_start=self._pinch_start, on_wheel=self._wheel)
        self.bind(pos=self._on_layout, size=self._on_layout)

    # --- Build ---
    def set_state(self, state: GameState):
        self.state = state
        self._visited_count = -1
        self.gestures.reset()
        self._build_static()
        self._needs_fit = True  # size is only final after the parent lays us out
        self._on_layout()

    def fit(self):
        if not self.state: return
        geo = self.state.geometry
        mw, mh = geo.get_maze_size()
        total_h = self.state.grid.levels * mh * 1.5
        self.camera.set_zoom(min(self.width / (mw * 1.2), self.height / (total_h * 1.2)))
        self.camera.x, self.camera.y = 0.0, ((self.state.grid.levels - 1) * mh * 1.5) / 2
        self.camera.apply()

    def _build_static(self):
        s, theme = self.state, settings.theme
        geo, grid = s.geometry, s.grid
        mw, mh = geo.get_maze_size()
        polar = geo.grid_type == "polar"
        self._static.clear()
        box_color = (60, 60, 60, 80) if theme.name == "dark" else (200, 200, 200, 80)
        for l in range(grid.levels):
            ox, oy = geo.floor_offset(l)
            self._static.add(Color(*rgba(box_color)))
            self._static.add(Rectangle(pos=(ox - mw * 0.525, oy - mh * 0.525), size=(mw * 1.05, mh * 1.05)))
            self._static.add(Color(*rgba(theme.HIGHLIGHT_COLOR)))
            self._static.add(text_rect(f"FLOOR {l+1}", ox, oy + mh * 0.55 + 10, 46, bold=True, anchor_y="bottom"))

            # Coordinate labels: columns A, B, C... and rows 1, 2, 3...
            self._static.add(Color(*rgba(theme.TEXT_COLOR)))
            for c in range(grid.columns):
                px, py = geo.get_pixel(grid.rows - 1 if polar else 0, c, 1.0, (ox, oy))
                if polar:
                    dx, dy = px - ox, py - oy; dist = math.hypot(dx, dy)
                    if dist > 0: px += dx / dist * 25; py += dy / dist * 25
                else:
                    py -= geo.cell_radius * 2.0
                self._static.add(text_rect(column_label(c), px, py, 24))
            for r in range(grid.rows):
                px, py = geo.get_pixel(r, grid.columns // 2 if polar else 0, 1.0, (ox, oy))
                px -= 25 if polar else geo.cell_radius * 2.0
                self._static.add(text_rect(str(r + 1), px, py, 24))

            self._static.add(Color(*rgba(theme.WALL_COLOR)))
            for mesh in polygon_meshes(geo.get_occlusion_polygons(l, offset=(ox, oy), thickness_mult=0.6)):
                self._static.add(mesh)
            stairs = geo.stair_triangles(l, offset=(ox, oy))
            for kind, color in (("U", settings.STAIR_UP_COLOR), ("D", settings.STAIR_DOWN_COLOR)):
                self._static.add(Color(*rgba(color)))
                for mesh in polygon_meshes(p for p, k in stairs if k == kind): self._static.add(mesh)

    def _build_mask(self):
        """Explorative map: only cells the player has visited are revealed."""
        s = self.state
        self._stencil_begin.clear(); self._stencil_end.clear()
        if not s.explorative_map: return
        geo, half = s.geometry, s.geometry.cell_radius * 1.1
        squares = []
        for r, c, l in s.cells_visited:
            cx, cy = geo.get_pixel(r, c, 1.0, geo.floor_offset(l))
            squares.append([(cx - half, cy - half), (cx + half, cy - half), (cx + half, cy + half), (cx - half, cy + half)])
        self._stencil_begin.add(StencilPush()); self._stencil_begin.add(Color(1, 1, 1, 1))
        for mesh in polygon_meshes(squares): self._stencil_begin.add(mesh)
        self._stencil_begin.add(StencilUse())
        self._stencil_end.add(StencilUnUse())
        for mesh in polygon_meshes(squares): self._stencil_end.add(mesh)
        self._stencil_end.add(StencilPop())

    # --- Per frame ---
    def tick(self, pan_dx: float = 0, pan_dy: float = 0):
        s = self.state
        if not s: return
        if pan_dx or pan_dy:
            speed = 10 / self.camera.zoom
            self.camera.x += pan_dx * speed; self.camera.y += pan_dy * speed
        if len(s.cells_visited) != self._visited_count:
            self._visited_count = len(s.cells_visited)
            self._build_mask()
        self._draw_dynamic()
        self._draw_overlay()
        self.camera.apply()

    def _draw_dynamic(self):
        s, theme = self.state, settings.theme
        geo = s.geometry
        self._dynamic.clear()
        for l in range(s.grid.levels):
            off = geo.floor_offset(l)
            if s.show_solution and s.solution_path:
                pts = [geo.get_pixel(r, c, 1.0, off) for r, c, lv in s.solution_path if lv == l]
                if len(pts) > 1:
                    self._dynamic.add(Color(*rgba(theme.solver_colors[s.current_solver_idx]))); self._dynamic.add(polyline(pts, 3))
            if s.show_trace and len(s.path_history) > 1:
                pts = [geo.get_pixel(r, c, 1.0, off) for (r, c), lv in s.path_history if lv == l]
                if len(pts) > 1:
                    self._dynamic.add(Color(*rgba(theme.PATH_TRACE_COLOR))); self._dynamic.add(polyline(pts, 2))
            if l == s.start_pos[2]:
                self._dynamic.add(Color(*rgba(theme.TEXT_COLOR))); self._dynamic.add(circle(*geo.get_pixel(*s.start_pos[:2], 1.0, off), 6))
            if l == s.end_pos[2]:
                self._dynamic.add(Color(*rgba(theme.GOAL_COLOR))); self._dynamic.add(circle(*geo.get_pixel(*s.end_pos[:2], 1.0, off), 6))
            for star in s.stars:
                if star.level != l: continue
                px, py = geo.get_pixel(star.row, star.column, 1.0, off)
                self._dynamic.add(Color(*rgba(settings.STAR_COLOR if star not in s.stars_collected else settings.STAR_COLLECTED_COLOR)))
                self._dynamic.add(fan_mesh((px, py), star_points(px, py, 8, 3)))
            if l == s.current_level and s.player_cell:
                self._dynamic.add(Color(*rgba(theme.PLAYER_COLOR)))
                self._dynamic.add(circle(*geo.get_pixel(s.player_cell.row, s.player_cell.column, 1.0, off), 8))

    def _draw_overlay(self):
        """Screen-space title and legend."""
        s, theme = self.state, settings.theme
        g = self._overlay
        g.clear()
        g.add(Color(*rgba(theme.HIGHLIGHT_COLOR)))
        g.add(text_rect("EXPLODED ARCHITECTURAL VIEW", self.center_x, self.top - u(100), round(u(32)), bold=True))

        items = [
            ("WALL", theme.WALL_COLOR, "rect"), ("PLAYER", theme.PLAYER_COLOR, "circle"),
            ("GOAL", theme.GOAL_COLOR, "circle"), ("STAR", settings.STAR_COLOR, "star"),
            ("TRACE", theme.PATH_TRACE_COLOR, "line"),
            (f"SOLUTION ({s.solver_name})", theme.solver_colors[s.current_solver_idx], "line"),
            (f"FOG: {'ACTIVE' if s.explorative_map else 'OFF'}", settings.FOG_LEGEND_COLOR, "rect"),
        ]
        row, lx, ly = u(25), self.x + u(30), self.y + u(150)
        g.add(Color(*rgba(theme.BG_COLOR, 180)))
        g.add(Rectangle(pos=(lx - u(10), ly - u(10)), size=(u(190), len(items) * row + u(15))))
        for i, (name, color, shape) in enumerate(items):
            y = ly + i * row
            g.add(Color(*rgba(color)))
            if shape == "rect": g.add(Rectangle(pos=(lx + u(2.5), y + u(0.5)), size=(u(15), u(15))))
            elif shape == "circle": g.add(circle(lx + u(10), y + u(8), u(7)))
            elif shape == "star": g.add(fan_mesh((lx + u(10), y + u(8)), star_points(lx + u(10), y + u(8), u(8), u(3))))
            elif shape == "line": g.add(Rectangle(pos=(lx + u(2), y + u(6.5)), size=(u(16), u(3))))
            g.add(Color(*rgba(theme.TEXT_COLOR)))
            g.add(text_rect(name, lx + u(25), y + u(8), round(u(11)), bold=True, anchor_x="left"))

    # --- Input ---
    def _drag(self, dx, dy):
        self.camera.x -= dx / self.camera.zoom; self.camera.y -= dy / self.camera.zoom
        self.camera.apply()

    def _pinch_start(self):
        self._pinch_zoom = self.camera.zoom

    def _pinch(self, factor):
        self.camera.set_zoom(self._pinch_zoom * factor); self.camera.apply()

    def _wheel(self, zoom_in: bool):
        self.zoom_by(0.05 if zoom_in else -0.05)

    def zoom_by(self, delta: float):
        self.camera.set_zoom(self.camera.zoom + delta); self.camera.apply()

    def on_touch_down(self, touch):
        return self.gestures.touch_down(touch)

    def on_touch_move(self, touch):
        return self.gestures.touch_move(touch)

    def on_touch_up(self, touch):
        return self.gestures.touch_up(touch)

    def invalidate_theme(self):
        if self.state: self._build_static(); self._visited_count = -1
        self._on_layout()

    def _on_layout(self, *_):
        self._bg.pos, self._bg.size = self.pos, self.size
        self._bg_color.rgba = rgba(settings.theme.BG_COLOR, 235)
        if self._needs_fit and self.parent and self.size == self.parent.size:
            self._needs_fit = False
            self.fit()
        self.camera.apply()
