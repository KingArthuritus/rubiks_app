"""
cube_model.py  —  Cubie data model + move application
Logic follows reference Solver_UI.py EXACTLY.
"""
import math
from theme import FC

# ── Cubie ─────────────────────────────────────────────────────────
class Cubie:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.stickers = {}
        if y ==  1: self.stickers["U"] = FC["U"]
        if y == -1: self.stickers["D"] = FC["D"]
        if z ==  1: self.stickers["F"] = FC["F"]
        if z == -1: self.stickers["B"] = FC["B"]
        if x ==  1: self.stickers["R"] = FC["R"]
        if x == -1: self.stickers["L"] = FC["L"]

    def rotate_stickers(self, axis, direction):
        cycles = {
            "x": [("U", "F", "D", "B")],
            "y": [("F", "R", "B", "L")],
            "z": [("U", "L", "D", "R")],
        }
        steps = (direction % 4 + 4) % 4
        for _ in range(steps):
            new = {}
            for face, col in self.stickers.items():
                moved = False
                for cycle in cycles[axis]:
                    if face in cycle:
                        idx = cycle.index(face)
                        new_face = cycle[(idx + 1) % 4]
                        new[new_face] = col
                        moved = True
                        break
                if not moved:
                    new[face] = col
            self.stickers = new

    def copy(self):
        c = Cubie.__new__(Cubie)
        c.pos = self.pos[:]
        c.stickers = dict(self.stickers)
        return c


# ── Cube factory ──────────────────────────────────────────────────
def fresh_cubies():
    return [Cubie(x, y, z)
            for x in [-1, 0, 1]
            for y in [-1, 0, 1]
            for z in [-1, 0, 1]]

def copy_cubies(cubies):
    return [c.copy() for c in cubies]


# ── Core finish-move helper (mirrors reference finish_animation) ──
def _do_finish(cubies, anim_layer, anim_axis, anim_dir):
    """Apply a completed 90° rotation to cubie positions+stickers."""
    ax, val = anim_layer
    a  = math.radians(anim_dir * 90)
    co = round(math.cos(a))
    si = round(math.sin(a))
    for c in cubies:
        if round(c.pos["xyz".index(ax)]) != val:
            continue
        x, y, z = c.pos
        if anim_axis == "x":
            c.pos = [x, y*co - z*si, y*si + z*co]
        elif anim_axis == "y":
            c.pos = [x*co + z*si, y, -x*si + z*co]
        elif anim_axis == "z":
            c.pos = [x*co - y*si, x*si + y*co, z]
        c.rotate_stickers(anim_axis, anim_dir)


# ── Instant move application ──────────────────────────────────────
# Mirrors reference start_animation() mapping + finish_animation().
# For "2" moves we apply the plain face move TWICE (CW twice = 180°).
_MAPPING = {
    # face: (layer, axis, base_dir_for_CW)
    # base_dir_for_CW means: when d=+1 (CW), anim_dir = base * d
    # From reference: "U": (("y",1),"y",-d)  → CW (d=1) gives anim_dir=-1
    "U": (("y",  1), "y", -1),
    "D": (("y", -1), "y",  1),
    "R": (("x",  1), "x", -1),
    "L": (("x", -1), "x",  1),
    "F": (("z",  1), "z", -1),
    "B": (("z", -1), "z",  1),
}

def _apply_one_cw(cubies, face: str):
    """Apply one CW turn of 'face' instantly."""
    layer, axis, base_dir = _MAPPING[face]
    _do_finish(cubies, layer, axis, base_dir)   # base_dir = anim_dir for CW

def _apply_one_ccw(cubies, face: str):
    """Apply one CCW turn of 'face' instantly (= 3x CW)."""
    layer, axis, base_dir = _MAPPING[face]
    _do_finish(cubies, layer, axis, -base_dir)  # flip dir for CCW


def apply_move_instant(cubies, move: str):
    """
    Apply move string like "U", "R'", "F2" instantly to cubies in-place.
    """
    face = move[0]
    if "2" in move:
        _apply_one_cw(cubies, face)
        _apply_one_cw(cubies, face)
    elif "'" in move:
        _apply_one_ccw(cubies, face)
    else:
        _apply_one_cw(cubies, face)


def apply_sequence_instant(cubies, moves):
    for m in moves:
        apply_move_instant(cubies, m)


# ── kociemba state string ─────────────────────────────────────────
# Scan positions EXACTLY from reference get_cube_string() face_map.
_FACE_SCAN = {
    "U": [(x,  1, z) for z in [-1, 0, 1] for x in [-1, 0, 1]],
    "R": [(1,  y, z) for y in [ 1, 0,-1] for z in [ 1, 0,-1]],
    "F": [(x,  y, 1) for y in [ 1, 0,-1] for x in [-1, 0, 1]],
    "D": [(x, -1, z) for z in [ 1, 0,-1] for x in [-1, 0, 1]],
    "L": [(-1, y, z) for y in [ 1, 0,-1] for z in [-1, 0, 1]],
    "B": [(x,  y,-1) for y in [ 1, 0,-1] for x in [ 1, 0,-1]],
}

_INV_FC = {v: k for k, v in FC.items()}


def cubies_to_kociemba(cubies) -> str:
    """Identical to reference get_cube_string()."""
    res = ""
    for f in ["U", "R", "F", "D", "L", "B"]:
        for pos in _FACE_SCAN[f]:
            for c in cubies:
                if [round(p) for p in c.pos] == list(pos):
                    res += _INV_FC.get(c.stickers.get(f), "?")
                    break
    return res
