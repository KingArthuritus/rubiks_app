"""
ui_custom_solver.py  —  Tab 2: Custom Cube Solver
"""
import tkinter as tk

from renderer      import CubeGLFrame
from cube_model    import (fresh_cubies, copy_cubies, apply_sequence_instant,
                            _FACE_SCAN)
from solver_engine import solve_async
from validator     import validate_cube_string
from theme         import (BG, SURFACE, SURFACE2, BORDER,
                            ACCENT, ACCENT2, ACCENT3, GREEN,
                            TEXT, TEXT2, TEXT3,
                            FC_HEX, FACE_NAMES, FC)

FACE_ORDER = "URFDLB"
_FACE_IDX  = {f: i for i, f in enumerate(FACE_ORDER)}

_NET_POS = {
    "U": (1, 0), "L": (0, 1), "F": (1, 1),
    "R": (2, 1), "B": (3, 1), "D": (1, 2),
}

def _move_instruction(move: str) -> str:
    face  = move[0]
    is2   = "2" in move
    ccw   = "'" in move and not is2
    label = {"U":"Top","D":"Bottom","F":"Front","B":"Back","R":"Right","L":"Left"}[face]
    if is2: return f"Turn {label} 180°"
    if ccw: return f"Turn {label} CCW"
    return f"Turn {label} CW"

def _default_state():
    return [f for f in FACE_ORDER for _ in range(9)]

def _btn(parent, text, cmd, fg=TEXT, bg=SURFACE2, font=None, **kw):
    f = font or ("Courier", 9, "bold")
    return tk.Button(parent, text=text, command=cmd,
                     font=f, fg=fg, bg=bg,
                     activeforeground=fg, activebackground=SURFACE,
                     relief="flat", cursor="hand2", bd=0, **kw)

class CustomSolverTab(tk.Frame):
    # Ultra-compact to prevent any cutoff
    SZ = 13   
    G  = 2    

    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)

        self._state         = "INPUT"
        self._cubies        = fresh_cubies()
        self._stickers      = _default_state()
        self._solution      : list[str] = []
        self._step          = 0
        self._auto_job      = None
        self._auto_speed    = tk.IntVar(value=5)
        self._anim_speed_gl = tk.IntVar(value=8)
        self._sel_colour    = tk.StringVar(value="U")
        self._net_rects     : dict[int, int] = {}
        self._anim_pending  = False

        self._build_ui()

        self._gl.cubies       = self._cubies
        self._gl.on_move_done = self._on_move_done
        self._gl.start_loop()

        for i, face in enumerate(FACE_ORDER):
            self.bind_all(str(i + 1), lambda e, f=face: self._pick(f))
        self.bind_all("<Left>",  self._on_left)
        self.bind_all("<Right>", self._on_right)

    def _build_ui(self):
        self._bot_bar = tk.Frame(self, bg=BG, height=70)
        self._bot_bar.pack(side="bottom", fill="x")
        self._bot_bar.pack_propagate(False)
        self._build_bottom_bar(self._bot_bar)

        body = tk.Frame(self, bg=BG)
        body.pack(side="top", fill="both", expand=True)

        left_wrap = tk.Frame(body, bg=SURFACE, width=180)
        left_wrap.pack(side="left", fill="y")
        left_wrap.pack_propagate(False)
        self._build_left_panel(left_wrap)

        right_wrap = tk.Frame(body, bg=BG)
        right_wrap.pack(side="left", fill="both", expand=True)
        self._build_right_panel(right_wrap)

    def _build_bottom_bar(self, parent):
        self._err_lbl = tk.Label(parent, text="", font=("Courier", 8), bg=BG, fg=ACCENT3)
        self._err_lbl.pack()
        row = tk.Frame(parent, bg=BG)
        row.pack(expand=True)
        self._start_btn = _btn(row, "⚡ START SOLVING", self._start_solving, 
                               fg="#0c0c14", bg=ACCENT, font=("Courier", 10, "bold"), padx=20, pady=5)
        self._start_btn.pack(side="left", padx=5)
        _btn(row, "↺ RESET", self._reset_cube, fg=ACCENT3, padx=10).pack(side="left")

    def _build_left_panel(self, parent):
        inner = tk.Frame(parent, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(inner, text="🧩 COLOURS", font=("Courier", 10, "bold"), bg=SURFACE, fg=ACCENT2).pack(pady=(0,10))
        
        self._colour_btns = {}
        # Added explicit [Key] labels to make the shortcuts obvious
        for i, face in enumerate(FACE_ORDER):
            r = tk.Frame(inner, bg=SURFACE)
            r.pack(fill="x", pady=2)
            
            # Key Indicator
            tk.Label(r, text=f"[{i+1}]", font=("Courier", 8, "bold"), bg=SURFACE, fg=ACCENT).pack(side="left", padx=(0,5))
            
            btn = tk.Button(r, bg=FC_HEX[face], width=2, height=1, relief="flat", command=lambda f=face: self._pick(f))
            btn.pack(side="left")
            self._colour_btns[face] = btn
            
            tk.Label(r, text=FACE_NAMES[face], font=("Courier", 8), bg=SURFACE, fg=TEXT2).pack(side="left", padx=5)

        self._pick("U")
        tk.Label(inner, text="\nPress 1-6 to Select\nClick Net to Paint\nArrows to Step", 
                 font=("Courier", 7), bg=SURFACE, fg=TEXT3, justify="left").pack(side="bottom", anchor="w")

    def _build_right_panel(self, parent):
        gl_wrap = tk.Frame(parent, bg=BG)
        gl_wrap.pack(side="top", fill="x")
        self._gl = CubeGLFrame(gl_wrap, width=400, height=280, bg=BG)
        self._gl.pack()

        self._lower = tk.Frame(parent, bg=BG)
        self._lower.pack(side="top", fill="both", expand=True)

        self._net_frame = tk.Frame(self._lower, bg=BG)
        tk.Label(self._net_frame, text="CLICK STICKERS TO PAINT", font=("Courier", 8, "bold"), bg=BG, fg=TEXT3).pack(pady=(2,0))
        
        sz, g = self.SZ, self.G
        fb = sz * 3 + g * 4
        self._net_canvas = tk.Canvas(self._net_frame, bg=BG, width=4*fb+10, height=3*fb+10, highlightthickness=0)
        self._net_canvas.pack(pady=2)
        self._net_canvas.bind("<Button-1>", self._net_click)
        self._draw_net()

        self._solve_frame = tk.Frame(self._lower, bg=SURFACE)
        self._build_solve_section(self._solve_frame)
        self._net_frame.pack()

    def _build_solve_section(self, p):
        mid = tk.Frame(p, bg=SURFACE2)
        mid.pack(fill="x", padx=10, pady=5)
        self._move_big = tk.Label(mid, text="—", font=("Courier", 28, "bold"), bg=SURFACE2, fg=ACCENT, width=3)
        self._move_big.pack(side="left")
        
        info = tk.Frame(mid, bg=SURFACE2)
        info.pack(side="left", fill="both", expand=True)
        self._step_var = tk.StringVar()
        tk.Label(info, textvariable=self._step_var, font=("Courier", 7), bg=SURFACE2, fg=TEXT2).pack(anchor="w")
        self._instr_var = tk.StringVar(value="Ready")
        tk.Label(info, textvariable=self._instr_var, font=("Helvetica", 8, "bold"), bg=SURFACE2, fg=ACCENT2).pack(anchor="w")

        ctrl = tk.Frame(p, bg=SURFACE)
        ctrl.pack(fill="x", pady=2)
        _btn(ctrl, "←", self._prev_step, width=5).pack(side="left", padx=5)
        _btn(ctrl, "→", self._next_step, width=5).pack(side="left")
        _btn(ctrl, "▶ AUTO", self._auto_play, bg=ACCENT2, fg="#000", padx=10).pack(side="right", padx=5)
        _btn(p, "BACK TO EDITOR", self._back_to_input, font=("Courier", 7, "bold")).pack(pady=2)

    def _solving_visible(self, show: bool):
        if show:
            self._net_frame.pack_forget()
            self._bot_bar.pack_forget()
            self._solve_frame.pack(fill="both", expand=True)
        else:
            self._solve_frame.pack_forget()
            self._bot_bar.pack(side="bottom", fill="x")
            self._net_frame.pack()

    def _draw_net(self):
        c = self._net_canvas
        c.delete("all")
        self._net_rects.clear()
        sz, g = self.SZ, self.G
        fo = sz * 3 + g * 4
        for face, (col, row) in _NET_POS.items():
            ox, oy = col * (fo + g) + 5, row * (fo + g) + 5
            fi = _FACE_IDX[face]
            c.create_text(ox + fo/2, oy + fo/2, text=face, font=("Courier", 6), fill=TEXT3)
            for pos in range(9):
                r, cl = divmod(pos, 3)
                rid = c.create_rectangle(ox+cl*(sz+g), oy+r*(sz+g), ox+cl*(sz+g)+sz, oy+r*(sz+g)+sz, 
                                       fill=FC_HEX[self._stickers[fi*9+pos]], outline=BORDER)
                self._net_rects[fi*9+pos] = rid

    def _net_click(self, e):
        for idx, rid in self._net_rects.items():
            x1, y1, x2, y2 = self._net_canvas.bbox(rid)
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                if idx % 9 != 4: self._paint(idx, self._sel_colour.get())
                return

    def _paint(self, idx, color_letter):
        self._stickers[idx] = color_letter
        self._net_canvas.itemconfig(self._net_rects[idx], fill=FC_HEX[color_letter])
        face, pos = FACE_ORDER[idx//9], idx%9
        tgt = list(_FACE_SCAN[face][pos])
        for c in self._cubies:
            if [round(p) for p in c.pos] == tgt:
                c.stickers[face] = FC[color_letter]
                break

    def _pick(self, face):
        self._sel_colour.set(face)
        for f, b in self._colour_btns.items():
            b.config(relief="sunken" if f==face else "flat", bd=2 if f==face else 0)

    def _reset_cube(self):
        self._stickers = _default_state(); self._cubies = fresh_cubies()
        self._gl.cubies = self._cubies; self._gl.clear_queue(); self._draw_net()
        self._solving_visible(False); self._err_lbl.config(text="")

    def _back_to_input(self):
        self._stop_auto(); self._state = "INPUT"; self._solving_visible(False)

    def _start_solving(self):
        state = "".join(self._stickers)
        err = validate_cube_string(state)
        if err: self._err_lbl.config(text=f"⚠ {err}"); return
        self._err_lbl.config(text="Solving..."); self._base_state = [c.copy() for c in self._cubies]
        solve_async(self._cubies, "Pro", self._on_solution, lambda m: self._err_lbl.config(text=f"⚠ {m}"))

    def _on_solution(self, moves, t):
        self._solution = moves; self._step = 0; self._state = "SOLVING"
        self._gl.cubies = copy_cubies(self._base_state); self._gl.clear_queue()
        self._solving_visible(True); self._update_display()

    def _next_step(self):
        if self._step < len(self._solution) and not self._anim_pending:
            move = self._solution[self._step]; self._step += 1; self._anim_pending = True
            self._gl.enqueue([move]); self._update_display()

    def _prev_step(self):
        if self._step > 0 and not self._anim_pending:
            self._step -= 1; self._cubies = copy_cubies(self._base_state)
            apply_sequence_instant(self._cubies, self._solution[:self._step])
            self._gl.cubies = self._cubies; self._update_display()

    def _on_move_done(self):
        self._anim_pending = False
        if self._auto_job: self._schedule_auto()
        if self._step >= len(self._solution): self._move_big.config(text="✔", fg=GREEN)

    def _update_display(self):
        total = len(self._solution)
        cur = self._solution[self._step-1] if self._step > 0 else "—"
        self._move_big.config(text=cur)
        self._step_var.set(f"Step {self._step}/{total}")
        self._instr_var.set(_move_instruction(cur) if self._step > 0 else "Ready")

    def _auto_play(self): 
        if not self._auto_job: self._auto_job = "pending"; self._next_step()
    def _schedule_auto(self):
        if self._step < len(self._solution): self._auto_job = self.after(500, self._next_step)
        else: self._auto_job = None
    def _stop_auto(self):
        if isinstance(self._auto_job, int): self.after_cancel(self._auto_job)
        self._auto_job = None

    def _on_left(self, e=None): self._prev_step()
    def _on_right(self, e=None): self._next_step()