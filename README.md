# Rubik's Cube Solver — Arthur Lee
## Setup

```bash
pip install PyOpenGL pyopengltk kociemba
python main.py
```

## File Structure

| File | Purpose |
|------|---------|
| `main.py` | Entry point — creates the two-tab window |
| `theme.py` | Shared colours, fonts, ttk style |
| `cube_model.py` | Cubie class, move application, kociemba state string |
| `renderer.py` | Reusable OpenGL 3-D frame (drag to rotate) |
| `solver_engine.py` | kociemba wrapper, scramble generator, difficulty config |
| `validator.py` | Custom cube validation (counts, centres, parity) |
| `ui_speed_solver.py` | Tab 1 — Speed Race UI |
| `ui_custom_solver.py` | Tab 2 — Custom Cube UI |

## Tab 1: Speed Solver Race
1. Select difficulty (Beginner / Medium / Hard / Insane)
2. Press **Start Race** — cube scrambles instantly
3. Memorise the scramble, grab your physical cube, apply it
4. Press **SPACE** — both timers start, computer begins animating
5. When you finish, press **SPACE** (or the Done button)
6. Results screen shows winner + times

## Tab 2: Custom Cube Solver
1. Click a colour swatch (or press **1–6**) to select it
2. Click stickers on the net to paint them
3. Press **Start Solving** — state is validated first
4. Use **Prev / Next** buttons or **arrow keys** to step through
5. **Auto Play** with speed slider animates automatically
