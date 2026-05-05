import random
import threading
from typing import Callable
import kociemba
from cube_model import (
    cubies_to_kociemba,
    copy_cubies,
    apply_sequence_instant,
    Cubie,
)

ALL_MOVES = ["U", "U'", "U2", "D", "D'", "D2",
             "L", "L'", "L2", "R", "R'", "R2",
             "F", "F'", "F2", "B", "B'", "B2"]

DIFFICULTY = {
    "Beginner":     (20, 4),
    "Intermediate": (20, 8.0),
    "Advanced":     (20, 22.0),
    "Pro":          (20, 22.0),
    "Impossible":   (20, 60.0),
}

# ───────────────────────────────────────────────────────────────
# NET MILESTONE STATES  (URFDLB order for kociemba target)
# ───────────────────────────────────────────────────────────────

# NET 1 → White Cross
NET_U =  [["R","F","F"], ["U","U","R"], ["R","B","U"]]
NET_R =  [["B","U","U"], ["F","R","L"], ["L","R","B"]]
NET_F =  [["F","U","R"], ["R","F","L"], ["B","F","D"]]
NET_D =  [["L","D","F"], ["D","D","D"], ["U","D","R"]]
NET_L =  [["D","L","U"], ["F","L","B"], ["B","L","D"]]
NET_B =  [["L","R","F"], ["B","B","U"], ["D","B","L"]]

# NET 2 → White Corners filled
NET_U2 = [["L","B","F"], ["B","U","U"], ["B","L","U"]]
NET_F2 = [["R","F","F"], ["B","F","R"], ["F","F","F"]]
NET_R2 = [["R","F","U"], ["F","R","U"], ["R","R","R"]]
NET_B2 = [["L","L","U"], ["R","B","U"], ["B","B","B"]]
NET_L2 = [["B","U","U"], ["L","L","R"], ["L","L","L"]]
NET_D2 = [["D","D","D"], ["D","D","D"], ["D","D","D"]]

# NET 3 → Middle layer edges solved
NET_U3 = [["U","U","B"], ["U","U","F"], ["R","L","U"]]
NET_F3 = [["F","U","R"], ["F","F","F"], ["F","F","F"]]
NET_R3 = [["B","U","L"], ["R","R","R"], ["R","R","R"]]
NET_B3 = [["U","R","L"], ["B","B","B"], ["B","B","B"]]
NET_L3 = [["F","B","U"], ["L","L","L"], ["L","L","L"]]
NET_D3 = [["D","D","D"], ["D","D","D"], ["D","D","D"]]

# NET 4 → Yellow cross on top
NET_U4 = [["L","U","B"], ["U","U","U"], ["U","U","R"]]
NET_F4 = [["F","R","U"], ["F","F","F"], ["F","F","F"]]
NET_R4 = [["F","B","U"], ["R","R","R"], ["R","R","R"]]
NET_B4 = [["L","F","U"], ["B","B","B"], ["B","B","B"]]
NET_L4 = [["B","L","L"], ["L","L","L"], ["L","L","L"]]
NET_D4 = [["D","D","D"], ["D","D","D"], ["D","D","D"]]

# NET 5 → Yellow face fully oriented
NET_U5 = [["U","U","U"], ["U","U","U"], ["U","U","U"]]
NET_F5 = [["F","B","F"], ["F","F","F"], ["F","F","F"]]
NET_R5 = [["R","F","R"], ["R","R","R"], ["R","R","R"]]
NET_B5 = [["B","R","B"], ["B","B","B"], ["B","B","B"]]
NET_L5 = [["L","L","L"], ["L","L","L"], ["L","L","L"]]
NET_D5 = [["D","D","D"], ["D","D","D"], ["D","D","D"]]

# NET 6 → Fully solved
NET_U6 = [["U","U","U"], ["U","U","U"], ["U","U","U"]]
NET_F6 = [["F","F","F"], ["F","F","F"], ["F","F","F"]]
NET_R6 = [["R","R","R"], ["R","R","R"], ["R","R","R"]]
NET_B6 = [["B","B","B"], ["B","B","B"], ["B","B","B"]]
NET_L6 = [["L","L","L"], ["L","L","L"], ["L","L","L"]]
NET_D6 = [["D","D","D"], ["D","D","D"], ["D","D","D"]]

# ───────────────────────────────────────────────────────────────
# BUILD TARGET STRINGS  (kociemba expects URFDLB order)
# ───────────────────────────────────────────────────────────────

def _flatten(face):
    return "".join("".join(row) for row in face)

def _target(u, r, f, d, l, b):
    return _flatten(u) + _flatten(r) + _flatten(f) + _flatten(d) + _flatten(l) + _flatten(b)

TARGET_1 = _target(NET_U,  NET_R,  NET_F,  NET_D,  NET_L,  NET_B)   # cross
TARGET_2 = _target(NET_U2, NET_R2, NET_F2, NET_D2, NET_L2, NET_B2)  # corners
TARGET_3 = _target(NET_U3, NET_R3, NET_F3, NET_D3, NET_L3, NET_B3)  # middle layer
TARGET_4 = _target(NET_U4, NET_R4, NET_F4, NET_D4, NET_L4, NET_B4)  # yellow cross
TARGET_5 = _target(NET_U5, NET_R5, NET_F5, NET_D5, NET_L5, NET_B5)  # yellow face
TARGET_6 = _target(NET_U6, NET_R6, NET_F6, NET_D6, NET_L6, NET_B6)  # fully solved

# ───────────────────────────────────────────────────────────────
# UTILITIES
# ───────────────────────────────────────────────────────────────

def _invert_move(m: str) -> str:
    if m.endswith("2"): return m
    if m.endswith("'"): return m[0]
    return m + "'"

def _cancel_moves(seq: list[str]) -> list[str]:
    out: list[str] = []
    for m in seq:
        if out and _invert_move(m) == out[-1]:
            out.pop()
        else:
            out.append(m)
    return out

# ───────────────────────────────────────────────────────────────
# PHASED BEGINNER SOLVER  — steps through all 6 NET milestones
# ───────────────────────────────────────────────────────────────

STAGES = [
    ("White Cross",        TARGET_1),
    ("White Corners",      TARGET_2),
    ("Middle Layer",       TARGET_3),
    ("Yellow Cross",       TARGET_4),
    ("Yellow Face",        TARGET_5),
    ("Solved",             TARGET_6),
]

def _beginner_solve(cubies: list[Cubie]) -> list[str]:
    working   = copy_cubies(cubies)
    all_moves = []

    for stage_name, target in STAGES:
        current = cubies_to_kociemba(working)
        # Already at this milestone? Skip it.
        if current == target:
            continue
        try:
            path = kociemba.solve(current, target).split()
            all_moves.extend(path)
            apply_sequence_instant(working, path)
        except Exception as e:
            print(f"[Beginner] Stage '{stage_name}' failed: {e}")
            # Fall back: solve directly to fully solved from here
            try:
                fallback = kociemba.solve(cubies_to_kociemba(working)).split()
                all_moves.extend(fallback)
            except Exception as e2:
                print(f"[Beginner] Fallback also failed: {e2}")
            break

    return _cancel_moves(all_moves)

# ───────────────────────────────────────────────────────────────
# LBL PADDING  (Intermediate / Advanced)
# ───────────────────────────────────────────────────────────────

_LBL_BASES = [
    ["R", "U", "R'", "U'"],
    ["R", "U", "R'", "U", "R", "U2", "R'"],
    ["F", "R", "U", "R'", "U'", "F'"],
    ["R", "U2", "R'", "U'", "R", "U'", "R'"],
    ["U", "R", "U'", "L'", "U", "R'", "U'", "L"],
    ["R'", "U'", "F'", "U", "F", "R"],
]

def _invert_seq(moves):
    return [_invert_move(m) for m in reversed(moves)]

def _make_filler():
    base = random.choice(_LBL_BASES)
    seq  = base * random.randint(1, 3)
    return seq + _invert_seq(seq)

def _lbl_expand(solution_moves):
    result, i = [], 0
    while i < len(solution_moves):
        chunk = random.randint(2, 4)
        result.extend(solution_moves[i:i + chunk])
        i += chunk
        if i < len(solution_moves):
            result.extend(_make_filler())
    return result

# ───────────────────────────────────────────────────────────────
# MAIN DISPATCH
# ───────────────────────────────────────────────────────────────

def solve_cubies(cubies: list[Cubie], difficulty: str = "Pro") -> list[str]:
    if difficulty in ("Beginner", "Intermediate", "Advanced"):
        return _beginner_solve(cubies)

    state = cubies_to_kociemba(cubies)
    return kociemba.solve(state).strip().split()   # Pro / Impossible


def solve_async(cubies, difficulty, on_success, on_error):
    snapshot = copy_cubies(cubies)
    def _run():
        try:
            moves = solve_cubies(snapshot, difficulty)
            on_success(moves, 0)
        except Exception as e:
            on_error(str(e))
    threading.Thread(target=_run, daemon=True).start()


def make_scramble(n: int) -> list[str]:
    seq, last = [], ""
    for _ in range(n):
        choices = [m for m in ALL_MOVES if m[0] != last]
        m = random.choice(choices)
        last = m[0]
        seq.append(m)
    return seq