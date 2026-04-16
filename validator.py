"""
validator.py  —  validate a custom cube state before solving

Checks:
  1. Exactly 9 stickers of each colour
  2. Centre stickers match expected colours
  3. Kociemba can parse the string (catches impossible parity)
"""
from typing import Optional

import kociemba

from theme import FC, FC_HEX


# Expected centre sticker for each face (index 4 of each 9-sticker face)
# State string order: U(0-8) R(9-17) F(18-26) D(27-35) L(36-44) B(45-53)
CENTRE_EXPECTED = {
    0*9+4: "U",
    1*9+4: "R",
    2*9+4: "F",
    3*9+4: "D",
    4*9+4: "L",
    5*9+4: "B",
}
FACE_LETTERS = list("URFDLB")


def validate_cube_string(state: str) -> Optional[str]:
    """
    Validate a 54-char kociemba state string.
    Returns None if valid, or an error message string if invalid.
    """
    if len(state) != 54:
        return f"State has {len(state)} chars, expected 54."

    # 1. exactly 9 of each
    from collections import Counter
    counts = Counter(state)
    for face in "URFDLB":
        if counts.get(face, 0) != 9:
            colour = FC_HEX.get(face, face)
            return (f"Face '{face}' has {counts.get(face,0)} stickers "
                    f"(expected 9).  Check your colour assignments.")

    # 2. centres fixed
    for idx, expected in CENTRE_EXPECTED.items():
        if state[idx] != expected:
            return (f"Centre of face '{FACE_LETTERS[idx//9]}' must be "
                    f"'{expected}' but is '{state[idx]}'.  "
                    f"Centres cannot be changed.")

    # 3. kociemba parity check
    try:
        kociemba.solve(state)
    except Exception as exc:
        msg = str(exc).lower()
        if "parity" in msg:
            return ("Parity error — this cube state is physically impossible "
                    "(e.g. two corners swapped or one edge flipped).")
        return f"Invalid cube state: {exc}"

    return None   # all good
