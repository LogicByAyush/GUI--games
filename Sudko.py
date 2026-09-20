import tkinter as tk
from tkinter import ttk, messagebox
import random
import copy
import time

# ---------------------------------------------------------------------------
# Constants / configuration
# ---------------------------------------------------------------------------

# Symbols used for cell values. Index 0 -> value 1, ... index 8 -> value 9,
# index 9 -> value 10 shown as 'A', ... up to value 16 shown as 'G'.
SYMBOLS = "123456789ABCDEFG"

SIZE_CONFIGS = {
    "6 x 6": {"n": 6, "br": 2, "bc": 3},
    "9 x 9": {"n": 9, "br": 3, "bc": 3},
    "16 x 16": {"n": 16, "br": 4, "bc": 4},
}

DIFFICULTY_REMOVE_RATIO = {
    "Easy": 0.40,
    "Medium": 0.55,
    "Hard": 0.68,
}

# ---------------------------------------------------------------------------
# Light / Dark themes
# ---------------------------------------------------------------------------

LIGHT_THEME = {
    "window_bg": "#f2f4f7",
    "panel_bg": "#ffffff",
    "fixed_bg": "#dbe7f5",
    "editable_bg": "#ffffff",
    "solved_bg": "#e3f7e3",
    "selected_bg": "#ffe9a8",
    "unit_bg": "#eaf1fb",
    "same_num_bg": "#bfe0ff",
    "conflict_bg": "#ff9b9b",
    "text_fg": "#1a1a1a",
    "accent": "#2c6fbb",
    "accent_fg": "#ffffff",
    "muted_btn": "#6c757d",
    "border": "#999999",
    "grid_border": "#000000",
    "label_fg": "#555555",
}

DARK_THEME = {
    "window_bg": "#1c1d22",
    "panel_bg": "#26282f",
    "fixed_bg": "#393d49",
    "editable_bg": "#20222a",
    "solved_bg": "#1f3a2c",
    "selected_bg": "#5a4a1a",
    "unit_bg": "#2e313b",
    "same_num_bg": "#2f5170",
    "conflict_bg": "#7a2323",
    "text_fg": "#eaeaea",
    "accent": "#5b9bdc",
    "accent_fg": "#ffffff",
    "muted_btn": "#4a4d58",
    "border": "#5a5d68",
    "grid_border": "#cfcfcf",
    "label_fg": "#a9acb6",
}


def val_to_sym(v):
    """0 -> empty string, else -> display symbol"""
    if not v:
        return ""
    return SYMBOLS[v - 1]


def sym_to_val(s, n):
    """Convert typed text to an integer value 1..n, 0 for empty,
    None if invalid for this grid size."""
    s = s.strip().upper()
    if s == "":
        return 0
    if len(s) != 1:
        return None
    idx = SYMBOLS.find(s)
    if idx == -1 or idx + 1 > n:
        return None
    return idx + 1


# ---------------------------------------------------------------------------
# Core Sudoku logic: works for any (n, box_rows, box_cols) combination
# ---------------------------------------------------------------------------

class SudokuLogic:
    def __init__(self, n, br, bc):
        self.n = n
        self.br = br
        self.bc = bc

    def is_valid(self, grid, r, c, v):
        n = self.n
        for i in range(n):
            if i != c and grid[r][i] == v:
                return False
            if i != r and grid[i][c] == v:
                return False
        br, bc = self.br, self.bc
        box_r = (r // br) * br
        box_c = (c // bc) * bc
        for i in range(box_r, box_r + br):
            for j in range(box_c, box_c + bc):
                if (i != r or j != c) and grid[i][j] == v:
                    return False
        return True

    def find_empty(self, grid):
        for r in range(self.n):
            for c in range(self.n):
                if grid[r][c] == 0:
                    return r, c
        return None

    def solve(self, grid, randomize=False):
        """In-place backtracking solver. Returns True if solved."""
        empty = self.find_empty(grid)
        if not empty:
            return True
        r, c = empty
        candidates = list(range(1, self.n + 1))
        if randomize:
            random.shuffle(candidates)
        for v in candidates:
            if self.is_valid(grid, r, c, v):
                grid[r][c] = v
                if self.solve(grid, randomize=randomize):
                    return True
                grid[r][c] = 0
        return False

    def generate_full(self):
        grid = [[0] * self.n for _ in range(self.n)]
        self.solve(grid, randomize=True)
        return grid

    def count_solutions(self, grid, limit=2):
        """Counts solutions up to `limit` (early stop) - used to keep
        puzzles uniquely solvable for smaller grids."""
        empty = self.find_empty(grid)
        if not empty:
            return 1
        r, c = empty
        count = 0
        for v in range(1, self.n + 1):
            if self.is_valid(grid, r, c, v):
                grid[r][c] = v
                count += self.count_solutions(grid, limit - count)
                grid[r][c] = 0
                if count >= limit:
                    break
        return count

    def make_puzzle(self, difficulty):
        full = self.generate_full()
        puzzle = copy.deepcopy(full)
        n = self.n
        cells = [(r, c) for r in range(n) for c in range(n)]
        random.shuffle(cells)
        remove_ratio = DIFFICULTY_REMOVE_RATIO.get(difficulty, 0.5)
        remove_target = int(n * n * remove_ratio)
        removed = 0
        # Uniqueness checking is expensive; only do it for smaller grids
        # (9x9 and 6x6). For 16x16 we skip it for speed.
        check_unique = n <= 9

        for (r, c) in cells:
            if removed >= remove_target:
                break
            backup = puzzle[r][c]
            if backup == 0:
                continue
            puzzle[r][c] = 0
            if check_unique:
                test = copy.deepcopy(puzzle)
                sols = self.count_solutions(test, limit=2)
                if sols != 1:
                    puzzle[r][c] = backup
                    continue
            removed += 1
        return puzzle, full

    def is_complete_and_valid(self, grid):
        for r in range(self.n):
            for c in range(self.n):
                v = grid[r][c]
                if v == 0:
                    return False
                if not self.is_valid(grid, r, c, v):
                    return False
        return True

    def has_conflicts(self, grid):
        """Check current (possibly incomplete) grid for rule violations."""
        for r in range(self.n):
            for c in range(self.n):
                v = grid[r][c]
                if v != 0 and not self.is_valid(grid, r, c, v):
                    return True
        return False


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class SudokuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku - Play & Solve")
        self.root.configure(bg="#f2f4f7")
        self.root.geometry("960x720")

        self.container = tk.Frame(self.root, bg="#f2f4f7")
        self.container.pack(fill="both", expand=True)

        # ---- core game state ----
        self.logic = None
        self.n = 0
        self.entries = {}
        self.string_vars = {}
        self.fixed_cells = set()          # currently non-editable cells
        self.solved_fill_cells = set()    # cells auto-filled by solver (solve mode)
        self.solution_grid = None
        self.puzzle = None
        self.mode = None                  # "play" or "solve"

        # ---- UX / extra-feature state ----
        self.dark_mode = False
        self.selected_cell = None
        self.size_key = None
        self.difficulty = None
        self.start_time = None
        self.timer_after_id = None
        self.win_shown = False
        self._last_screen = "menu"

        self.show_menu()

    # ------------------------------------------------------------------
    # Theme helpers
    # ------------------------------------------------------------------
    def theme(self):
        return DARK_THEME if self.dark_mode else LIGHT_THEME

    def apply_ttk_style(self):
        th = self.theme()
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TCombobox",
                         fieldbackground=th["editable_bg"],
                         background=th["panel_bg"],
                         foreground=th["text_fg"],
                         arrowcolor=th["text_fg"])
        style.map("TCombobox",
                   fieldbackground=[("readonly", th["editable_bg"])],
                   foreground=[("readonly", th["text_fg"])])

    def add_dark_toggle(self, parent):
        th = self.theme()
        text = "\u2600 Light Mode" if self.dark_mode else "\U0001F319 Dark Mode"
        btn = tk.Button(parent, text=text, font=("Segoe UI", 10),
                         bg=th["muted_btn"], fg="white", bd=0, cursor="hand2",
                         command=self.toggle_dark_mode)
        btn.pack(side="right", padx=6, pady=6)
        return btn

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        screen = self._last_screen
        if screen == "play_grid":
            display = self.read_grid_values()
            self.build_play_grid_screen(self.size_key, self.difficulty,
                                         display_override=display)
        elif screen == "solve_grid":
            display = self.read_grid_values()
            self.build_solve_grid_screen(self.size_key, display,
                                          fixed_mask=set(self.fixed_cells),
                                          solved_mask=set(self.solved_fill_cells))
        elif screen == "play_setup":
            self.show_play_setup()
        elif screen == "solve_setup":
            self.show_solve_setup()
        else:
            self.show_menu()

    # ------------------------------------------------------------------
    def clear_container(self):
        self.stop_timer()
        for widget in self.container.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------
    def start_timer(self, reset=True):
        if reset or self.start_time is None:
            self.start_time = time.time()
        self.timer_tick()

    def stop_timer(self):
        if self.timer_after_id is not None:
            try:
                self.root.after_cancel(self.timer_after_id)
            except Exception:
                pass
            self.timer_after_id = None

    def timer_tick(self):
        if self.start_time is None:
            return
        elapsed = int(time.time() - self.start_time)
        mm, ss = divmod(elapsed, 60)
        if hasattr(self, "timer_label") and self.timer_label.winfo_exists():
            self.timer_label.config(text=f"\u23F1 {mm:02d}:{ss:02d}")
            self.timer_after_id = self.root.after(1000, self.timer_tick)

    def elapsed_str(self):
        if self.start_time is None:
            return "00:00"
        elapsed = int(time.time() - self.start_time)
        mm, ss = divmod(elapsed, 60)
        return f"{mm:02d}:{ss:02d}"

    # ------------------------------------------------------------------
    # MENU
    # ------------------------------------------------------------------
    def show_menu(self):
        self._last_screen = "menu"
        self.clear_container()
        th = self.theme()
        self.apply_ttk_style()
        self.root.configure(bg=th["window_bg"])
        self.container.configure(bg=th["window_bg"])

        top = tk.Frame(self.container, bg=th["window_bg"])
        top.pack(fill="x")
        self.add_dark_toggle(top)

        frame = tk.Frame(self.container, bg=th["window_bg"])
        frame.pack(expand=True)

        tk.Label(frame, text="SUDOKU", font=("Segoe UI", 36, "bold"),
                 bg=th["window_bg"], fg=th["accent"]).pack(pady=(40, 10))
        tk.Label(frame, text="Kya karna chahte ho?", font=("Segoe UI", 14),
                 bg=th["window_bg"], fg=th["text_fg"]).pack(pady=(0, 30))

        btn_style = {"font": ("Segoe UI", 14), "width": 22, "height": 2,
                     "bg": th["accent"], "fg": "white", "activebackground": "#1f5390",
                     "bd": 0, "cursor": "hand2"}

        tk.Button(frame, text="\U0001F3AE  Play Game",
                  command=self.show_play_setup, **btn_style).pack(pady=10)
        tk.Button(frame, text="\U0001F9E9  Solve Game",
                  command=self.show_solve_setup, **btn_style).pack(pady=10)

    # ------------------------------------------------------------------
    # PLAY SETUP
    # ------------------------------------------------------------------
    def show_play_setup(self):
        self._last_screen = "play_setup"
        self.clear_container()
        th = self.theme()
        self.apply_ttk_style()
        self.root.configure(bg=th["window_bg"])
        self.container.configure(bg=th["window_bg"])

        top = tk.Frame(self.container, bg=th["window_bg"])
        top.pack(fill="x")
        self.add_dark_toggle(top)

        frame = tk.Frame(self.container, bg=th["window_bg"])
        frame.pack(expand=True)

        tk.Label(frame, text="Play Game - Setup", font=("Segoe UI", 22, "bold"),
                 bg=th["window_bg"], fg=th["accent"]).pack(pady=(20, 20))

        tk.Label(frame, text="Sudoku Size:", font=("Segoe UI", 13),
                 bg=th["window_bg"], fg=th["text_fg"]).pack(pady=(10, 4))
        if not hasattr(self, "play_size_var"):
            self.play_size_var = tk.StringVar(value="9 x 9")
        size_box = ttk.Combobox(frame, textvariable=self.play_size_var,
                                 values=list(SIZE_CONFIGS.keys()),
                                 state="readonly", width=15, justify="center")
        size_box.pack()

        tk.Label(frame, text="Difficulty:", font=("Segoe UI", 13),
                 bg=th["window_bg"], fg=th["text_fg"]).pack(pady=(20, 4))
        if not hasattr(self, "play_diff_var"):
            self.play_diff_var = tk.StringVar(value="Easy")
        diff_box = ttk.Combobox(frame, textvariable=self.play_diff_var,
                                 values=list(DIFFICULTY_REMOVE_RATIO.keys()),
                                 state="readonly", width=15, justify="center")
        diff_box.pack()

        tk.Button(frame, text="Start Game", font=("Segoe UI", 13, "bold"),
                  bg=th["accent"], fg="white", bd=0, width=18, height=2,
                  cursor="hand2",
                  command=self.start_play).pack(pady=30)

        tk.Button(frame, text="\u2190 Back to Menu", font=("Segoe UI", 11),
                  bg=th["window_bg"], fg=th["accent"], bd=0, cursor="hand2",
                  command=self.show_menu).pack()

    def start_play(self):
        size_key = self.play_size_var.get()
        difficulty = self.play_diff_var.get()
        cfg = SIZE_CONFIGS[size_key]
        self.n = cfg["n"]
        self.logic = SudokuLogic(cfg["n"], cfg["br"], cfg["bc"])
        self.mode = "play"

        if self.n == 16:
            self.root.config(cursor="wait")
            self.root.update()

        puzzle, full = self.logic.make_puzzle(difficulty)
        self.root.config(cursor="")
        self.puzzle = puzzle
        self.solution_grid = full
        self.build_play_grid_screen(size_key, difficulty)

    # ------------------------------------------------------------------
    # PLAY GRID SCREEN
    # ------------------------------------------------------------------
    def build_play_grid_screen(self, size_key, difficulty, display_override=None):
        self._last_screen = "play_grid"
        self.size_key = size_key
        self.difficulty = difficulty
        self.mode = "play"
        self.clear_container()
        th = self.theme()
        self.apply_ttk_style()
        self.root.configure(bg=th["window_bg"])
        self.container.configure(bg=th["window_bg"])

        self.entries = {}
        self.string_vars = {}
        self.selected_cell = None

        if display_override is None:
            display_grid = self.puzzle
            self.fixed_cells = {(r, c) for r in range(self.n) for c in range(self.n)
                                 if self.puzzle[r][c] != 0}
            self.win_shown = False
            reset_timer = True
        else:
            display_grid = display_override
            reset_timer = False
        self.solved_fill_cells = set()

        top = tk.Frame(self.container, bg=th["window_bg"])
        top.pack(fill="x", pady=(10, 0))
        tk.Label(top, text=f"Play Mode - {size_key} - {difficulty}",
                 font=("Segoe UI", 16, "bold"), bg=th["window_bg"],
                 fg=th["accent"]).pack(side="left", padx=20)

        self.timer_label = tk.Label(top, text="\u23F1 00:00", font=("Segoe UI", 12, "bold"),
                                     bg=th["window_bg"], fg=th["text_fg"])
        self.timer_label.pack(side="left", padx=10)

        self.add_dark_toggle(top)

        btn_frame = tk.Frame(top, bg=th["window_bg"])
        btn_frame.pack(side="right", padx=20)
        tk.Button(btn_frame, text="\U0001F4A1 Hint", bg=th["accent"], fg="white",
                  bd=0, cursor="hand2",
                  command=self.use_hint).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Check Solution", bg=th["accent"], fg="white",
                  bd=0, cursor="hand2",
                  command=self.check_play_solution).pack(side="left", padx=4)
        tk.Button(btn_frame, text="New Game", bg=th["muted_btn"], fg="white",
                  bd=0, cursor="hand2",
                  command=self.show_play_setup).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Menu", bg=th["muted_btn"], fg="white",
                  bd=0, cursor="hand2",
                  command=self.show_menu).pack(side="left", padx=4)

        hint_lbl = tk.Label(self.container,
                             text="Tip: Cell select karke SPACE dabao -> agle khaali cell par jaoge. "
                                  "Arrow keys se bhi ghoom sakte ho.",
                             font=("Segoe UI", 9), bg=th["window_bg"], fg=th["label_fg"])
        hint_lbl.pack(fill="x", padx=20)

        body = tk.Frame(self.container, bg=th["window_bg"])
        body.pack(fill="both", expand=True, pady=10)

        grid_holder = tk.Frame(body, bg=th["window_bg"])
        grid_holder.pack(side="left", padx=20, anchor="n")
        self.draw_grid(grid_holder, display_grid, self.fixed_cells, set())

        # Side panel: remaining numbers tracker
        side = tk.Frame(body, bg=th["panel_bg"], bd=1, relief="solid")
        side.pack(side="left", padx=20, anchor="n", fill="y")
        tk.Label(side, text="Numbers Remaining", font=("Segoe UI", 12, "bold"),
                 bg=th["panel_bg"], fg=th["accent"]).pack(pady=(10, 6), padx=16)
        self.remaining_labels = {}
        rem_frame = tk.Frame(side, bg=th["panel_bg"])
        rem_frame.pack(padx=16, pady=(0, 16))
        cols = 4
        for idx in range(self.n):
            v = idx + 1
            r, c = divmod(idx, cols)
            lbl = tk.Label(rem_frame, text="", font=("Consolas", 12),
                            bg=th["unit_bg"], fg=th["text_fg"], width=6, height=1, relief="ridge")
            lbl.grid(row=r, column=c, padx=3, pady=3)
            self.remaining_labels[v] = lbl

        self.update_remaining_panel()
        self.start_timer(reset=reset_timer)

    # ------------------------------------------------------------------
    # Grid drawing (shared by play & solve modes)
    # ------------------------------------------------------------------
    def draw_grid(self, parent, display_grid, fixed_mask, solved_mask=frozenset()):
        n = self.n
        th = self.theme()
        font_size = 16 if n <= 9 else (10 if n == 16 else 14)

        grid_frame = tk.Frame(parent, bg=th["grid_border"])
        grid_frame.pack()

        for r in range(n):
            for c in range(n):
                val = display_grid[r][c]
                is_fixed = (r, c) in fixed_mask
                rc = (r, c)

                sv = tk.StringVar(value=val_to_sym(val))
                self.string_vars[rc] = sv

                # thicker border around box boundaries
                top_b = 2 if r % self.logic.br == 0 else 1
                left_b = 2 if c % self.logic.bc == 0 else 1
                bottom_b = 2 if (r + 1) % self.logic.br == 0 else 0
                right_b = 2 if (c + 1) % self.logic.bc == 0 else 0

                cell_wrap = tk.Frame(grid_frame, bg=th["grid_border"])
                cell_wrap.grid(row=r, column=c,
                               padx=(left_b, right_b), pady=(top_b, bottom_b))

                vcmd = (self.root.register(self._make_validator(n)), "%P")

                ent = tk.Entry(cell_wrap, textvariable=sv, width=2,
                                font=("Consolas", font_size, "bold"),
                                justify="center", relief="flat",
                                validate="key", validatecommand=vcmd)
                ent.config(highlightthickness=1, highlightbackground=th["border"])
                ent.pack(ipady=6, ipadx=2)

                if is_fixed:
                    ent.config(state="disabled")
                    ent.bind("<Button-1>", lambda e, rc=rc: self.select_cell(rc, focus=False))
                else:
                    ent.bind("<FocusIn>", lambda e, rc=rc: self.select_cell(rc, focus=False))
                    ent.bind("<Button-1>", lambda e, rc=rc: self.select_cell(rc))
                    ent.bind("<Left>", lambda e: self.move_selection(0, -1))
                    ent.bind("<Right>", lambda e: self.move_selection(0, 1))
                    ent.bind("<Up>", lambda e: self.move_selection(-1, 0))
                    ent.bind("<Down>", lambda e: self.move_selection(1, 0))
                    ent.bind("<space>", lambda e: self.jump_next_blank())
                    sv.trace_add("write", lambda *a: self.on_value_change())

                self.entries[rc] = ent

        self.fixed_cells = set(fixed_mask)
        self.solved_fill_cells = set(solved_mask)
        self.recompute_colors()

    def _make_validator(self, n):
        allowed = set(SYMBOLS[:n])

        def validate(proposed):
            if proposed == "":
                return True
            if len(proposed) > 1:
                return False
            return proposed.upper() in allowed
        return validate

    # ------------------------------------------------------------------
    # Selection / navigation helpers (new features)
    # ------------------------------------------------------------------
    def select_cell(self, rc, focus=True):
        self.selected_cell = rc
        ent = self.entries.get(rc)
        if focus and ent is not None:
            try:
                if str(ent.cget("state")) == "normal":
                    ent.focus_set()
            except tk.TclError:
                pass
        self.recompute_colors()

    def move_selection(self, dr, dc):
        if self.selected_cell is None:
            self.select_cell((0, 0))
            return "break"
        r, c = self.selected_cell
        nr = max(0, min(self.n - 1, r + dr))
        nc = max(0, min(self.n - 1, c + dc))
        self.select_cell((nr, nc))
        return "break"

    def find_next_blank(self, start):
        grid = self.read_grid_values()
        n = self.n
        total = n * n
        sr, sc = start
        start_idx = sr * n + sc
        for step in range(1, total + 1):
            idx = (start_idx + step) % total
            r, c = divmod(idx, n)
            if grid[r][c] == 0 and (r, c) not in self.fixed_cells:
                return (r, c)
        return None

    def jump_next_blank(self):
        start = self.selected_cell if self.selected_cell is not None else (0, 0)
        nxt = self.find_next_blank(start)
        if nxt:
            self.select_cell(nxt)
        return "break"

    # ------------------------------------------------------------------
    # Value reading / coloring
    # ------------------------------------------------------------------
    def read_grid_values(self):
        n = self.n
        grid = [[0] * n for _ in range(n)]
        for (r, c), sv in self.string_vars.items():
            v = sym_to_val(sv.get(), n)
            grid[r][c] = v if v else 0
        return grid

    def same_unit(self, a, b):
        if a == b:
            return False
        ar, ac = a
        br_, bc_ = b
        if ar == br_ or ac == bc_:
            return True
        br, bc = self.logic.br, self.logic.bc
        return (ar // br == br_ // br) and (ac // bc == bc_ // bc)

    def get_conflict_cells(self, grid):
        n = self.n
        conflict = set()

        for r in range(n):
            seen = {}
            for c in range(n):
                v = grid[r][c]
                if v:
                    seen.setdefault(v, []).append((r, c))
            for cells in seen.values():
                if len(cells) > 1:
                    conflict.update(cells)

        for c in range(n):
            seen = {}
            for r in range(n):
                v = grid[r][c]
                if v:
                    seen.setdefault(v, []).append((r, c))
            for cells in seen.values():
                if len(cells) > 1:
                    conflict.update(cells)

        br, bc = self.logic.br, self.logic.bc
        for br0 in range(0, n, br):
            for bc0 in range(0, n, bc):
                seen = {}
                for i in range(br0, br0 + br):
                    for j in range(bc0, bc0 + bc):
                        v = grid[i][j]
                        if v:
                            seen.setdefault(v, []).append((i, j))
                for cells in seen.values():
                    if len(cells) > 1:
                        conflict.update(cells)

        return conflict

    def recompute_colors(self):
        if not self.entries:
            return
        th = self.theme()
        grid = self.read_grid_values()
        sel = self.selected_cell
        sel_val = grid[sel[0]][sel[1]] if sel else 0
        conflicts = self.get_conflict_cells(grid)

        for rc, ent in self.entries.items():
            r, c = rc
            val = grid[r][c]
            is_fixed = rc in self.fixed_cells
            is_solved_fill = rc in self.solved_fill_cells

            color = th["fixed_bg"] if is_fixed else th["editable_bg"]
            if is_solved_fill:
                color = th["solved_bg"]

            if sel and self.same_unit(sel, rc):
                color = th["unit_bg"]
            if sel_val and val == sel_val:
                color = th["same_num_bg"]
            if sel == rc:
                color = th["selected_bg"]
            if rc in conflicts:
                color = th["conflict_bg"]

            if is_fixed:
                ent.config(disabledbackground=color, disabledforeground=th["text_fg"])
            else:
                ent.config(bg=color, fg=th["text_fg"], insertbackground=th["text_fg"])

    def on_value_change(self):
        self.update_remaining_panel()
        self.recompute_colors()
        if self.mode == "play":
            self.maybe_auto_win()

    def maybe_auto_win(self):
        if self.win_shown:
            return
        grid = self.read_grid_values()
        if self.logic.is_complete_and_valid(grid):
            self.win_shown = True
            elapsed = self.elapsed_str()
            self.stop_timer()
            messagebox.showinfo(
                "Sudoku",
                f"Bahut badhiya! Puzzle sahi se solve ho gaya! \U0001F389\nTime: {elapsed}")

    def update_remaining_panel(self):
        if not hasattr(self, "remaining_labels"):
            return
        th = self.theme()
        grid = self.read_grid_values()
        n = self.n
        counts = {v: 0 for v in range(1, n + 1)}
        for row in grid:
            for v in row:
                if v:
                    counts[v] += 1
        for v, lbl in self.remaining_labels.items():
            remaining = n - counts[v]
            symbol = val_to_sym(v)
            lbl.config(text=f"{symbol} : {remaining}")
            if remaining == 0:
                lbl.config(bg=th["solved_bg"], fg=th["text_fg"])
            else:
                lbl.config(bg=th["unit_bg"], fg=th["text_fg"])

    def check_play_solution(self):
        grid = self.read_grid_values()
        if self.logic.is_complete_and_valid(grid):
            self.win_shown = True
            elapsed = self.elapsed_str()
            self.stop_timer()
            messagebox.showinfo(
                "Sudoku",
                f"Bahut badhiya! Puzzle sahi se solve ho gaya! \U0001F389\nTime: {elapsed}")
        else:
            if any(0 in row for row in grid):
                messagebox.showwarning("Sudoku", "Abhi kuch cells khaali hain, pehle sabhi bharo.")
            else:
                messagebox.showerror("Sudoku", "Kahin galti hai - koi rule violate ho raha hai. Dobara check karo.")

    def use_hint(self):
        grid = self.read_grid_values()
        empties = [(r, c) for r in range(self.n) for c in range(self.n)
                   if grid[r][c] == 0 and (r, c) not in self.fixed_cells]
        if not empties:
            messagebox.showinfo("Sudoku", "Koi khaali cell nahi hai jise hint diya ja sake.")
            return
        rc = random.choice(empties)
        correct = self.solution_grid[rc[0]][rc[1]]
        self.string_vars[rc].set(val_to_sym(correct))
        self.select_cell(rc)

    # ------------------------------------------------------------------
    # SOLVE SETUP
    # ------------------------------------------------------------------
    def show_solve_setup(self):
        self._last_screen = "solve_setup"
        self.clear_container()
        th = self.theme()
        self.apply_ttk_style()
        self.root.configure(bg=th["window_bg"])
        self.container.configure(bg=th["window_bg"])

        top = tk.Frame(self.container, bg=th["window_bg"])
        top.pack(fill="x")
        self.add_dark_toggle(top)

        frame = tk.Frame(self.container, bg=th["window_bg"])
        frame.pack(expand=True)

        tk.Label(frame, text="Solve Game - Setup", font=("Segoe UI", 22, "bold"),
                 bg=th["window_bg"], fg=th["accent"]).pack(pady=(20, 20))

        tk.Label(frame, text="Sudoku Size:", font=("Segoe UI", 13),
                 bg=th["window_bg"], fg=th["text_fg"]).pack(pady=(10, 4))
        if not hasattr(self, "solve_size_var"):
            self.solve_size_var = tk.StringVar(value="9 x 9")
        size_box = ttk.Combobox(frame, textvariable=self.solve_size_var,
                                 values=list(SIZE_CONFIGS.keys()),
                                 state="readonly", width=15, justify="center")
        size_box.pack()

        tk.Label(frame, text="Jitne bhi numbers pata hain unhe grid me bhar dena,\n"
                              "baaki khaali chodo. Fir 'Solve' dabao.",
                 font=("Segoe UI", 11), bg=th["window_bg"], fg=th["label_fg"]).pack(pady=20)

        tk.Button(frame, text="Continue", font=("Segoe UI", 13, "bold"),
                  bg=th["accent"], fg="white", bd=0, width=18, height=2,
                  cursor="hand2",
                  command=self.start_solve).pack(pady=20)

        tk.Button(frame, text="\u2190 Back to Menu", font=("Segoe UI", 11),
                  bg=th["window_bg"], fg=th["accent"], bd=0, cursor="hand2",
                  command=self.show_menu).pack()

    def start_solve(self):
        size_key = self.solve_size_var.get()
        cfg = SIZE_CONFIGS[size_key]
        self.n = cfg["n"]
        self.logic = SudokuLogic(cfg["n"], cfg["br"], cfg["bc"])
        self.mode = "solve"
        empty_grid = [[0] * self.n for _ in range(self.n)]
        self.build_solve_grid_screen(size_key, empty_grid, fixed_mask=set(), solved_mask=set())

    # ------------------------------------------------------------------
    # SOLVE GRID SCREEN
    # ------------------------------------------------------------------
    def build_solve_grid_screen(self, size_key, grid, fixed_mask=None, solved_mask=None):
        self._last_screen = "solve_grid"
        self.size_key = size_key
        self.mode = "solve"
        self.clear_container()
        th = self.theme()
        self.apply_ttk_style()
        self.root.configure(bg=th["window_bg"])
        self.container.configure(bg=th["window_bg"])

        self.entries = {}
        self.string_vars = {}
        self.selected_cell = None
        self.fixed_cells = fixed_mask if fixed_mask is not None else set()
        self.solved_fill_cells = solved_mask if solved_mask is not None else set()

        top = tk.Frame(self.container, bg=th["window_bg"])
        top.pack(fill="x", pady=(10, 0))
        tk.Label(top, text=f"Solve Mode - {size_key}",
                 font=("Segoe UI", 16, "bold"), bg=th["window_bg"],
                 fg=th["accent"]).pack(side="left", padx=20)

        self.add_dark_toggle(top)

        btn_frame = tk.Frame(top, bg=th["window_bg"])
        btn_frame.pack(side="right", padx=20)
        tk.Button(btn_frame, text="Solve", bg=th["accent"], fg="white",
                  bd=0, cursor="hand2",
                  command=self.run_solver).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Clear", bg=th["muted_btn"], fg="white",
                  bd=0, cursor="hand2",
                  command=self.show_solve_setup).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Menu", bg=th["muted_btn"], fg="white",
                  bd=0, cursor="hand2",
                  command=self.show_menu).pack(side="left", padx=4)

        hint_lbl = tk.Label(self.container,
                             text="Tip: Cell select karke SPACE dabao -> agle khaali cell par jaoge. "
                                  "Galat number daalne par cell laal ho jayega.",
                             font=("Segoe UI", 9), bg=th["window_bg"], fg=th["label_fg"])
        hint_lbl.pack(fill="x", padx=20)

        body = tk.Frame(self.container, bg=th["window_bg"])
        body.pack(fill="both", expand=True, pady=10)

        grid_holder = tk.Frame(body, bg=th["window_bg"])
        grid_holder.pack(padx=20, anchor="n")
        self.draw_grid(grid_holder, grid, self.fixed_cells, self.solved_fill_cells)

    def run_solver(self):
        n = self.n
        grid = self.read_grid_values()

        if self.logic.has_conflicts(grid):
            messagebox.showerror("Sudoku",
                                  "Yeh grid already invalid hai - kisi row/column/box "
                                  "me ek hi number repeat ho raha hai. Solve possible nahi hai.")
            return

        if n == 16:
            self.root.config(cursor="wait")
            self.root.update()

        solved = copy.deepcopy(grid)
        success = self.logic.solve(solved, randomize=False)
        self.root.config(cursor="")

        if not success:
            messagebox.showerror("Sudoku", "Is grid ka koi solution possible nahi hai. (Not Possible)")
            return

        self.solved_fill_cells = {(r, c) for r in range(n) for c in range(n) if grid[r][c] == 0}
        self.fixed_cells = {(r, c) for r in range(n) for c in range(n)}

        for rc, sv in self.string_vars.items():
            sv.set(val_to_sym(solved[rc[0]][rc[1]]))
            self.entries[rc].config(state="disabled")

        self.recompute_colors()
        messagebox.showinfo("Sudoku", "Solved! \u2705")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()