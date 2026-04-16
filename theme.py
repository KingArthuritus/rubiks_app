"""
theme.py  —  shared colours, fonts, ttk styles
"""
import tkinter as tk
from tkinter import ttk

# ── palette ───────────────────────────────────────────────────────
# Matches glClearColor(0.06, 0.09, 0.16) in renderer.py exactly
BG       = "#0f1729" 
SURFACE  = "#161622"
SURFACE2 = "#1e1e2e"
BORDER   = "#2a2a42"
ACCENT   = "#e8ff47"      # yellow-green  (computer / solve)
ACCENT2  = "#47b8ff"      # sky blue      (user / info)
ACCENT3  = "#ff6b6b"      # coral-red     (warnings / reset)
GREEN    = "#44dd88"
ORANGE   = "#ff9933"
TEXT     = "#f0f0f8"
TEXT2    = "#7777aa"
TEXT3    = "#4a4a70"

# ── sticker colours ────────────────────────────────────────────────
FC = {
    "U": (1.0, 1.0, 0.0),   # yellow   (Up)
    "D": (1.0, 1.0, 1.0),   # white    (Down)
    "F": (1.0, 0.0, 0.1),   # red      (Front)
    "B": (1.0, 0.5, 0.0),   # orange   (Back)
    "R": (0.0, 0.9, 0.2),   # green    (Right)
    "L": (0.0, 0.4, 1.0),   # blue     (Left)
}

# hex versions of the same colours (for tkinter widgets)
FC_HEX = {
    "U": "#ffdd00",
    "D": "#f5f5f5",
    "F": "#ee1a1a",
    "B": "#ff8800",
    "R": "#22dd33",
    "L": "#1166ff",
}

FACE_NAMES = {
    "U": "Up  (Yellow)",
    "D": "Down  (White)",
    "F": "Front  (Red)",
    "B": "Back  (Orange)",
    "R": "Right  (Green)",
    "L": "Left  (Blue)",
}

def apply_ttk_theme(root: tk.Tk):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("TNotebook",
                background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
    s.configure("TNotebook.Tab",
                background=SURFACE2, foreground=TEXT2,
                padding=[20, 9], font=("Courier", 11, "bold"),
                focuscolor=BG)
    s.map("TNotebook.Tab",
          background=[("selected", BG)],
          foreground=[("selected", ACCENT)])
    s.configure("TFrame", background=BG)