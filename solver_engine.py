import random
import threading
from typing import Callable
import kociemba
from cube_model import (cubies_to_kociemba, copy_cubies, apply_sequence_instant, Cubie)

ALL_MOVES = ["U", "U'", "U2", "D", "D'", "D2", "L", "L'", "L2", "R", "R'", "R2", "F", "F'", "F2", "B", "B2"]

# Calibrated for 20-move scrambles
# Target times: Impossible (2s), Pro (5s), Advanced (20s), Inter (1m), Beginner (2m)
DIFFICULTY = {
    "Beginner":     (20, 7),   # 120 moves @ 1 move/sec = 2:00
    "Intermediate": (20, 10.0),   # 120 moves @ 2 moves/sec = 1:00
    "Advanced":     (20, 22.0),  # 60 moves @ 3 moves/sec = 0:20
    "Pro":          (20, 22.0),  # 20 moves @ 4 moves/sec = 0:05
    "Impossible":   (20, 50.0),  # 20 moves @ 10 moves/sec = 0:02
}

# ── LBL algorithm base fragments ──────────────────────────────────
# Each fragment is played forward then its exact inverse is appended,
# guaranteeing a true no-op on the cube state.
_LBL_BASES = [
    ["R", "U", "R'", "U'"],                          # sexy move
    ["R", "U", "R'", "U", "R", "U2", "R'"],          # Sune
    ["F", "R", "U", "R'", "U'", "F'"],               # OLL edge flip
    ["R", "U2", "R'", "U'", "R", "U'", "R'"],        # anti-Sune
    ["U", "R", "U'", "L'", "U", "R'", "U'", "L"],    # Y-perm setup
    ["R'", "U'", "F'", "U", "F", "R"],               # F2L trigger
]
 
def _invert_move(m: str) -> str:
    """Return the inverse of a single move token."""
    if m.endswith("2"):
        return m          # 180° is its own inverse
    elif m.endswith("'"):
        return m[0]       # CCW → CW
    else:
        return m + "'"    # CW → CCW
 
def _invert_sequence(moves: list[str]) -> list[str]:
    """Return the inverse of a move sequence (reversed + each inverted)."""
    return [_invert_move(m) for m in reversed(moves)]
 
def _make_filler() -> list[str]:
    """Pick a random base alg and append its exact inverse → guaranteed no-op."""
    base = random.choice(_LBL_BASES)
    # Optionally repeat 2-3 times for variety, still cancels
    reps = random.randint(1, 3)
    seq = base * reps
    return seq + _invert_sequence(seq)
 
def _lbl_expand(solution_moves: list[str]) -> list[str]:
    """
    Takes a short Kociemba solution and expands it to look like a
    Layer-By-Layer solve by inserting guaranteed no-op filler fragments
    between every few real moves.  The cube ends up solved identically.
    """
    result = []
    i = 0
    while i < len(solution_moves):
        chunk_size = random.randint(2, 4)
        chunk = solution_moves[i:i + chunk_size]
        result.extend(chunk)
        i += chunk_size
 
        if i < len(solution_moves):
            result.extend(_make_filler())
 
    return result
 
 
def solve_cubies(cubies: list[Cubie], difficulty: str = "Pro") -> list[str]:
    """
    Always produces a correct solution.
    Beginner/Intermediate: real solution expanded with LBL-style filler (~120 moves).
    Advanced/Pro/Impossible: optimal Kociemba solution.
    """
    state = cubies_to_kociemba(cubies)
    optimal = kociemba.solve(state).strip().split()
 
    if difficulty in ["Beginner", "Intermediate", "Advanced"]:
        return _lbl_expand(optimal)
    else:
        return optimal
 
 
def solve_async(cubies: list[Cubie], difficulty: str, on_success: Callable, on_error: Callable):
    # Snapshot the cubies so the background thread isn't racing with the renderer
    snapshot = copy_cubies(cubies)
    def _run():
        try:
            moves = solve_cubies(snapshot, difficulty)
            on_success(moves, 0)
        except Exception as e:
            on_error(str(e))
    threading.Thread(target=_run, daemon=True).start()
 
 
def make_scramble(n: int) -> list[str]:
    seq, last_face = [], ""
    for _ in range(n):
        choices = [m for m in ALL_MOVES if m[0] != last_face]
        m = random.choice(choices)
        last_face, seq = m[0], seq + [m]
    return seq