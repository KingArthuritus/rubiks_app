import time
import tkinter as tk
from renderer      import CubeGLFrame
from cube_model    import fresh_cubies
from solver_engine import make_scramble, solve_async, DIFFICULTY
from theme         import (BG, SURFACE, SURFACE2, BORDER, ACCENT, ACCENT2,
                            ACCENT3, GREEN, TEXT, TEXT2, TEXT3, ORANGE)

def _fmt(secs: float) -> str:
    m, s = int(secs) // 60, int(secs) % 60
    cs = int((secs % 1) * 100)
    return f"{m:02d}:{s:02d}.{cs:02d}"

class SpeedSolverTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.pack(fill="both", expand=True)

        self._state = "IDLE"
        self._cubies = fresh_cubies()
        self._diff_list = list(DIFFICULTY.keys())
        self._diff_idx = 0
        self._difficulty = tk.StringVar(value=self._diff_list[0])
        self._space_held = False
        
        self._user_done = self._comp_done = False
        self._build_ui()
        
        self._gl.cubies = self._cubies
        self._gl.on_move_done = self._on_comp_move_done
        self._gl.start_loop()

        self.focus_set()
        self.bind_all("<KeyPress-space>",   self._on_space_down)
        self.bind_all("<KeyRelease-space>", self._on_space_up)

    def _build_ui(self):
        self.top_bar = tk.Frame(self, bg=BG, height=30)
        self.top_bar.pack(side="top", fill="x")
        self.top_bar.pack_propagate(False)
        self.give_up_btn = tk.Button(self.top_bar, text="🏳 GIVE UP", command=self._reset_to_main,
                                     font=("Courier", 10, "bold"), bg=BG, fg=ACCENT3,
                                     activebackground=BG, activeforeground=TEXT,
                                     relief="flat", bd=0, cursor="hand2")

        self.top_section = tk.Frame(self, bg=BG, height=45)
        self.top_section.pack(side="top", fill="x")
        self.top_section.pack_propagate(False)

        self.choose_lbl = tk.Label(self.top_section, text="CHOOSE LEVEL", font=("Courier", 9, "bold"), bg=BG, fg=TEXT3)
        self.choose_lbl.pack(side="top")

        self.diff_canvas = tk.Canvas(self.top_section, bg=BG, height=25, highlightthickness=0)
        self.diff_canvas.pack(side="top", fill="x")
        self.text_id = self.diff_canvas.create_text(0, 12, text=self._diff_list[0].upper(),
                                                    fill=GREEN, font=("Courier", 18, "bold"))
        self.diff_canvas.bind("<Configure>", lambda e: self.diff_canvas.coords(self.text_id, e.width//2, 12))

        self.bot_section = tk.Frame(self, bg=BG, height=130)
        self.bot_section.pack(side="bottom", fill="x")
        self.bot_section.pack_propagate(False)

        self.start_btn = tk.Button(self.bot_section, text="START RACE", command=self._start_race,
                                   font=("Courier", 14, "bold"), bg=ACCENT, fg=BG,
                                   padx=40, pady=10, relief="flat", cursor="hand2")
        self.start_btn.pack(expand=True)

        # Scrambling in progress label
        self.scrambling_lbl = tk.Label(self.bot_section, text="⏳  SCRAMBLING IN PROGRESS...",
                                       font=("Courier", 13, "bold"), bg=BG, fg=ORANGE)

        # Hold-space instruction label (shown when READY)
        self.ready_lbl = tk.Label(self.bot_section, text="HOLD  DOWN  SPACE  TO  START",
                                  font=("Courier", 18, "bold"), bg=BG, fg=ACCENT)

        # "Release!" flash label shown while space is held
        self.release_lbl = tk.Label(self.bot_section, text="NOW RELEASE TO GO!",
                                    font=("Courier", 18, "bold"), bg=BG, fg=GREEN)

        # During race: stop-timer instruction
        self.stop_lbl = tk.Label(self.bot_section, text="PRESS  SPACE  WHEN  DONE",
                                 font=("Courier", 11, "bold"), bg=BG, fg=TEXT2)

        self.timer_frame = tk.Frame(self.bot_section, bg=BG)
        self.c_box = tk.Frame(self.timer_frame, bg=BG)
        self.c_box.pack(side="left", expand=True)
        tk.Label(self.c_box, text="COMPUTER TIMER", font=("Courier", 9, "bold"), bg=BG, fg=TEXT3).pack()
        self.comp_timer_lbl = tk.Label(self.c_box, text="00:00.00", font=("Courier", 26), bg=BG, fg=GREEN)
        self.comp_timer_lbl.pack()

        self.u_box = tk.Frame(self.timer_frame, bg=BG)
        self.u_box.pack(side="right", expand=True)
        tk.Label(self.u_box, text="YOUR TIMER", font=("Courier", 9, "bold"), bg=BG, fg=TEXT3).pack()
        self.user_timer_lbl = tk.Label(self.u_box, text="00:00.00", font=("Courier", 26), bg=BG, fg=ACCENT2)
        self.user_timer_lbl.pack()

        self.mid_section = tk.Frame(self, bg=BG)
        self.mid_section.pack(side="top", fill="both", expand=True)
        self.mid_section.columnconfigure((0,2), weight=1)

        self.left_btn = tk.Button(self.mid_section, text="◀", command=lambda: self._cycle_diff(-1),
                                  font=("Courier", 35, "bold"), bg=BG, fg=ACCENT, relief="flat", bd=0)
        self.left_btn.grid(row=0, column=0, sticky="e", padx=20)

        self._gl = CubeGLFrame(self.mid_section, width=450, height=450, bg=BG)
        self._gl.grid(row=0, column=1)

        self.right_btn = tk.Button(self.mid_section, text="▶", command=lambda: self._cycle_diff(1),
                                   font=("Courier", 35, "bold"), bg=BG, fg=ACCENT, relief="flat", bd=0)
        self.right_btn.grid(row=0, column=2, sticky="w", padx=20)

    # ── difficulty picker ─────────────────────────────────────────
    def _cycle_diff(self, delta):
        if self._state != "IDLE": return
        self._diff_idx = (self._diff_idx + delta) % len(self._diff_list)
        val = self._diff_list[self._diff_idx]
        self._difficulty.set(val)
        colors = {"Beginner": GREEN, "Intermediate": ACCENT2, "Advanced": ORANGE, "Pro": ACCENT3, "Impossible": "#aa00ff"}
        self.diff_canvas.itemconfig(self.text_id, text=val.upper(), fill=colors.get(val, TEXT))

    # ── start race ────────────────────────────────────────────────
    def _start_race(self):
        self._state = "SCRAMBLING"
        self.start_btn.pack_forget()
        self.choose_lbl.pack_forget()
        self.diff_canvas.pack_forget()
        self.left_btn.grid_remove()
        self.right_btn.grid_remove()
        self.scrambling_lbl.pack(expand=True)

        n = 20
        self._gl.anim_speed = 60
        self._scramble_moves = make_scramble(n)
        self._cubies[:] = fresh_cubies()
        self._gl.enqueue(self._scramble_moves)
        self._spin_tick()

    def _spin_tick(self):
        target_rx, target_ry = 30.0, -40.0
        if self._state == "SCRAMBLING":
            self._gl.ry += 18
            self._gl.rx += 10
            self.after(10, self._spin_tick)
        elif self._state == "HOMING":
            dx, dy = target_rx - self._gl.rx, target_ry - self._gl.ry
            if abs(dx) < 0.5 and abs(dy) < 0.5:
                self._gl.rx, self._gl.ry = target_rx, target_ry
                self._state = "READY"
                self.scrambling_lbl.pack_forget()
                self.ready_lbl.pack(expand=True)
            else:
                self._gl.rx += dx * 0.2
                self._gl.ry += dy * 0.2
                self.after(10, self._spin_tick)

    # ── space hold/release logic ──────────────────────────────────
    def _on_space_down(self, e=None):
        if self._space_held:
            return  # suppress key-repeat
        self._space_held = True

        if self._state == "READY":
            # Show "release to go" prompt while held
            self.ready_lbl.pack_forget()
            self.release_lbl.pack(expand=True)

        elif self._state == "RACING" and not self._user_done:
            # Stop the user timer on press (same as before)
            self._user_done = True
            self._user_time = time.perf_counter() - self._user_start
            self.user_timer_lbl.config(text=_fmt(self._user_time), fg=TEXT)
            if self._comp_done:
                self._show_post_race_menu()

    def _on_space_up(self, e=None):
        self._space_held = False

        if self._state == "READY":
            # Released — start the race!
            self._state = "RACING"
            self.release_lbl.pack_forget()
            self.give_up_btn.pack(side="left", padx=15)
            self.stop_lbl.pack(side="bottom", pady=6)
            self.timer_frame.pack(fill="both", expand=True)
            n, speed = DIFFICULTY[self._difficulty.get()]
            self._gl.anim_speed = speed
            self._user_start = self._comp_start = time.perf_counter()
            self._user_done = self._comp_done = False
            solve_async(self._cubies, self._difficulty.get(), self._on_solve_found, lambda e: print(e))
            self._tick()

    # ── solve + tick ──────────────────────────────────────────────
    def _on_solve_found(self, moves, _):
        self._solution_moves = moves
        self._gl.enqueue(moves)

    def _tick(self):
        if self._state != "RACING": return
        now = time.perf_counter()
        if not self._user_done: self.user_timer_lbl.config(text=_fmt(now - self._user_start))
        if not self._comp_done: self.comp_timer_lbl.config(text=_fmt(now - self._comp_start))
        self.after(50, self._tick)

    def _on_comp_move_done(self):
        if not self._gl.move_queue and not self._gl.animating:
            if self._state == "SCRAMBLING":
                self._state = "HOMING"
            elif self._state == "RACING" and not self._comp_done:
                self._comp_done = True
                self._comp_time = time.perf_counter() - self._comp_start
                self.comp_timer_lbl.config(text=_fmt(self._comp_time))
                if self._user_done:
                    self._show_post_race_menu()

    # ── post race ─────────────────────────────────────────────────
    def _show_post_race_menu(self):
        self._state = "POST_GAME"
        self.give_up_btn.pack_forget()
        self.stop_lbl.pack_forget()
        self.overlay = tk.Frame(self.mid_section, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        self.overlay.place(relx=0.5, rely=0.18, anchor="center")
        winner = "HUMAN" if self._user_time < self._comp_time else "MACHINE"
        color = ACCENT2 if winner == "HUMAN" else GREEN
        tk.Label(self.overlay, text=f"{winner} WINS!", font=("Courier", 24, "bold"),
                 bg=BG, fg=color, padx=20, pady=10).pack()
        btn_f = tk.Frame(self.overlay, bg=BG)
        btn_f.pack(pady=(0, 15))
        tk.Button(btn_f, text="AI STEPS", command=self._see_steps, font=("Courier", 10, "bold"),
                  bg=SURFACE2, fg=TEXT, padx=15, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_f, text="🔄 RETRY", command=self._retry, font=("Courier", 10, "bold"),
                  bg=ACCENT2, fg=BG, padx=15, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)
        tk.Button(btn_f, text="MAIN MENU", command=self._reset_to_main, font=("Courier", 10, "bold"),
                  bg=ACCENT3, fg=BG, padx=15, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)

    def _see_steps(self):
        msg = f"SCRAMBLE:\n{' '.join(self._scramble_moves)}\n\nAI SOLUTION:\n{' '.join(self._solution_moves)}"
        top = tk.Toplevel(self); top.title("Race Info"); top.configure(bg=BG)
        txt = tk.Text(top, bg=SURFACE, fg=TEXT, font=("Courier", 10), padx=10, pady=10, relief="flat")
        txt.insert("1.0", msg); txt.config(state="disabled"); txt.pack(fill="both", expand=True, padx=10, pady=10)

    def _retry(self):
        """Same difficulty, new scramble — skips main menu."""
        if hasattr(self, 'overlay'): self.overlay.destroy()
        self.give_up_btn.pack_forget()
        self.timer_frame.pack_forget()
        self.stop_lbl.pack_forget()
        self._gl.clear_queue()
        self._gl.rx, self._gl.ry = 30.0, -40.0
        self._cubies[:] = fresh_cubies()
        self._user_done = self._comp_done = False
        self.user_timer_lbl.config(text="00:00.00", fg=ACCENT2)
        self.comp_timer_lbl.config(text="00:00.00", fg=GREEN)
        self._start_race()

    def _reset_to_main(self):
        if hasattr(self, 'overlay'): self.overlay.destroy()
        self.give_up_btn.pack_forget()
        self.timer_frame.pack_forget()
        self.scrambling_lbl.pack_forget()
        self.ready_lbl.pack_forget()
        self.release_lbl.pack_forget()
        self.stop_lbl.pack_forget()
        self.choose_lbl.pack()
        self.diff_canvas.pack(fill="x")
        self.left_btn.grid(); self.right_btn.grid()
        self.start_btn.pack(expand=True)
        self._gl.clear_queue()
        self._gl.rx, self._gl.ry = 30.0, -40.0
        self._cubies[:] = fresh_cubies()
        self._state = "IDLE"
        self._space_held = False
        self._user_done = self._comp_done = False
        self.user_timer_lbl.config(text="00:00.00", fg=ACCENT2)
        self.comp_timer_lbl.config(text="00:00.00", fg=GREEN)