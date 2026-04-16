"""
renderer.py  —  Reusable OpenGL 3-D Rubik's Cube renderer
Animation logic copied EXACTLY from reference Solver_UI.py CubeGLFrame.
"""
import math
import tkinter as tk

from pyopengltk import OpenGLFrame
from OpenGL.GL  import *
from OpenGL.GLU import *

from cube_model import Cubie


class CubeGLFrame(OpenGLFrame):
    """
    Drop-in OpenGL frame.  Caller must set:
        frame.cubies        — list[Cubie]  (shared reference)
        frame.on_move_done  — callable()   (called after each animated move)
    """

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.cubies        = []
        self.on_move_done  = None

        # view rotation — same defaults as reference (rx=30, ry=-40)
        self.rx = 30.0
        self.ry = -40.0
        self._last_x = 0
        self._last_y = 0

        # animation state — mirrors reference CubeApp attributes
        self.animating  = False
        self.anim_layer = None   # ("x"|"y"|"z", int)
        self.anim_axis  = None
        self.anim_dir   = 1
        self.anim_angle = 0.0
        self.anim_speed = 8      # degrees per frame

        # move queue
        self.move_queue  = []
        self.step_mode   = False
        self._manual_trigger = False
        self._running    = False

        self.bind("<Button-1>",  self._mouse_press)
        self.bind("<B1-Motion>", self._mouse_drag)

    # ── OpenGL callbacks ──────────────────────────────────────────
    def initgl(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.06, 0.09, 0.16, 1.0)   # matches reference

    def redraw(self):
        try:
            self._tick()
            self._render()
        except Exception:
            pass

    # ── tick — identical flow to reference redraw() ───────────────
    def _tick(self):
        # Copied from reference redraw() step-mode block:
        if not self.animating and self.move_queue:
            if not self.step_mode or self._manual_trigger:
                self._start_animation(self.move_queue.pop(0))
                self._manual_trigger = False

        if self.animating:
            self.anim_angle += self.anim_speed
            if self.anim_angle >= 90:
                self._finish_animation()

    # ── render — identical to reference redraw() draw loop ────────
    def _render(self):
        w = max(self.winfo_width(),  1)
        h = max(self.winfo_height(), 1)
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0, -14)
        glRotatef(self.rx, 1, 0, 0)
        glRotatef(self.ry, 0, 1, 0)

        hs = 0.45   # half-size — same as reference
        for c in self.cubies:
            glPushMatrix()

            # rotate the animating layer — identical to reference
            if self.animating:
                idx = "xyz".index(self.anim_layer[0])
                if round(c.pos[idx]) == self.anim_layer[1]:
                    glRotatef(
                        self.anim_dir * self.anim_angle,
                        *(1 if self.anim_axis == a else 0 for a in "xyz")
                    )

            cx, cy, cz = c.pos
            v = [
                [cx-hs, cy-hs, cz-hs], [cx+hs, cy-hs, cz-hs],
                [cx+hs, cy+hs, cz-hs], [cx-hs, cy+hs, cz-hs],
                [cx-hs, cy-hs, cz+hs], [cx+hs, cy-hs, cz+hs],
                [cx+hs, cy+hs, cz+hs], [cx-hs, cy+hs, cz+hs],
            ]
            # face order identical to reference
            faces = [
                ([0,1,2,3], "B"), ([4,5,6,7], "F"),
                ([0,1,5,4], "D"), ([2,3,7,6], "U"),
                ([1,2,6,5], "R"), ([0,3,7,4], "L"),
            ]
            glBegin(GL_QUADS)
            for idxs, f in faces:
                glColor3fv(c.stickers.get(f, (0.05, 0.05, 0.05)))
                for i in idxs:
                    glVertex3fv(v[i])
            glEnd()

            glPopMatrix()

    # ── start_animation — EXACTLY reference logic ─────────────────
    def _start_animation(self, move: str):
        """Mirrors reference start_animation() 1-to-1."""
        face = move[0]
        ccw  = move.endswith("'")
        d    = -1 if ccw else 1
        mapping = {
            "U": (("y",  1), "y", -d),
            "D": (("y", -1), "y",  d),
            "R": (("x",  1), "x", -d),
            "L": (("x", -1), "x",  d),
            "F": (("z",  1), "z", -d),
            "B": (("z", -1), "z",  d),
        }
        self.anim_layer, self.anim_axis, self.anim_dir = mapping[face]
        self.animating  = True
        self.anim_angle = 0

    # ── finish_animation — EXACTLY reference logic ────────────────
    def _finish_animation(self):
        """Mirrors reference finish_animation() 1-to-1."""
        ax, val = self.anim_layer
        a  = math.radians(self.anim_dir * 90)
        co = round(math.cos(a))
        si = round(math.sin(a))
        for c in self.cubies:
            if round(c.pos["xyz".index(ax)]) != val:
                continue
            x, y, z = c.pos
            if self.anim_axis == "x":
                c.pos = [x, y*co - z*si, y*si + z*co]
            elif self.anim_axis == "y":
                c.pos = [x*co + z*si, y, -x*si + z*co]
            elif self.anim_axis == "z":
                c.pos = [x*co - y*si, x*si + y*co, z]
            c.rotate_stickers(self.anim_axis, self.anim_dir)
        self.animating  = False
        self.anim_angle = 0
        if self.on_move_done:
            self.on_move_done()

    # ── public API ────────────────────────────────────────────────
    def enqueue(self, moves):
        """
        Queue moves for animation.
        '2' moves are split into two plain moves, matching reference queue_move():
            if "2" in m: extend([m[0], m[0]])
        """
        for m in moves:
            if "2" in m:
                self.move_queue.extend([m[0], m[0]])
            else:
                self.move_queue.append(m)

    def clear_queue(self):
        self.move_queue.clear()
        self.animating  = False
        self.anim_angle = 0

    def trigger_next(self):
        self._manual_trigger = True

    def start_loop(self, interval_ms=16):
        if not self._running:
            self._running = True
            self._loop(interval_ms)

    def _loop(self, interval_ms):
        if self.winfo_exists():
            try:
                self.tkExpose(None)
            except Exception:
                pass
            self.after(interval_ms, lambda: self._loop(interval_ms))

    # ── mouse ─────────────────────────────────────────────────────
    def _mouse_press(self, e):
        self._last_x, self._last_y = e.x, e.y

    def _mouse_drag(self, e):
        # identical multiplier to reference (0.5)
        self.ry += (e.x - self._last_x) * 0.5
        self.rx += (e.y - self._last_y) * 0.5
        self._last_x, self._last_y = e.x, e.y

    @property
    def is_animating(self):
        return self.animating or bool(self.move_queue)

    @property
    def is_idle(self):
        return not self.animating and not self.move_queue
