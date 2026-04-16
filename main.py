import tkinter as tk
from tkinter import ttk
from ui_speed_solver import SpeedSolverTab
from ui_custom_solver import CustomSolverTab
from theme import (BG, SURFACE, SURFACE2, ACCENT, TEXT, TEXT2, apply_ttk_theme)

class RubiksApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rubik's Cube Solver")
        
        # --- Window Placement Logic (Top Middle) ---
        win_w, win_h = 900, 600
        screen_w = self.winfo_screenwidth()
        
        # Calculate horizontal center
        center_x = int((screen_w / 2) - (win_w / 2))
        
        # Set Y to 0 for the very top, or 20 for a small gap
        top_y = 10 
        
        # Set geometry: Width x Height + X + Y
        self.geometry(f"{win_w}x{win_h}+{center_x}+{top_y}")
        self.minsize(900, 600)
        
        # App Styling
        self.configure(bg=BG)
        apply_ttk_theme(self)

        self._build_header()
        self._build_tabs()

    def _build_header(self):
        # Header bar
        bar = tk.Frame(self, bg=SURFACE, height=40)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="⬛  Rubik's Cube Solver",
                 font=("Courier", 13, "bold"), bg=SURFACE, fg=TEXT
                 ).pack(side="left", padx=15)

        tk.Label(bar, text="Kociemba Algorithm",
                 font=("Courier", 9, "bold"), bg=SURFACE2, fg=ACCENT,
                 padx=10, pady=5
                 ).pack(side="right", padx=15)

    def _build_tabs(self):
        # Custom style for the Notebook tabs
        style = ttk.Style()
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=SURFACE, foreground=TEXT2, padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", BG)], foreground=[("selected", ACCENT)])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        # Tab instances
        t1 = SpeedSolverTab(nb)
        t2 = CustomSolverTab(nb)

        nb.add(t1, text="  SPEED RACE  ")
        nb.add(t2, text="  CUSTOM SOLVER  ")

if __name__ == "__main__":
    app = RubiksApp()
    app.mainloop()