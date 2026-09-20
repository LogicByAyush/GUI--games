import tkinter as tk
import math

# ══════════════════════════════════════════════════════════════
#  THEMES
# ══════════════════════════════════════════════════════════════
THEMES = {
    "dark": {
        "BG":          "#1E1E2E",
        "DISPLAY_BG":  "#181825",
        "DISPLAY_FG":  "#CDD6F4",
        "EXPR_FG":     "#6C7086",
        "NUM_BG":      "#313244",
        "NUM_FG":      "#CDD6F4",
        "NUM_HOV":     "#45475A",
        "OP_BG":       "#7C3AED",
        "OP_FG":       "#FFFFFF",
        "OP_HOV":      "#6D28D9",
        "SPEC_BG":     "#0E7490",   # teal – special (sqrt, xʸ, 1/x, mod)
        "SPEC_FG":     "#FFFFFF",
        "SPEC_HOV":    "#0C6478",
        "BRACK_BG":    "#475569",   # brackets
        "BRACK_FG":    "#FFFFFF",
        "BRACK_HOV":   "#334155",
        "EQUAL_BG":    "#22C55E",
        "EQUAL_FG":    "#FFFFFF",
        "EQUAL_HOV":   "#16A34A",
        "CLEAR_BG":    "#EF4444",
        "CLEAR_FG":    "#FFFFFF",
        "CLEAR_HOV":   "#DC2626",
        "BACK_BG":     "#F59E0B",
        "BACK_FG":     "#1E1E2E",
        "BACK_HOV":    "#D97706",
        "TOGGLE_BG":   "#334155",
        "TOGGLE_FG":   "#94A3B8",
        "HIST_BG":     "#1E1E2E",
        "HIST_FG":     "#CDD6F4",
        "HIST_ITEM":   "#313244",
        "HIST_HEAD":   "#7C3AED",
        "SCROLLBAR":   "#45475A",
    },
    "light": {
        "BG":          "#F1F5F9",
        "DISPLAY_BG":  "#FFFFFF",
        "DISPLAY_FG":  "#0F172A",
        "EXPR_FG":     "#94A3B8",
        "NUM_BG":      "#E2E8F0",
        "NUM_FG":      "#0F172A",
        "NUM_HOV":     "#CBD5E1",
        "OP_BG":       "#6D28D9",
        "OP_FG":       "#FFFFFF",
        "OP_HOV":      "#5B21B6",
        "SPEC_BG":     "#0E7490",
        "SPEC_FG":     "#FFFFFF",
        "SPEC_HOV":    "#0C6478",
        "BRACK_BG":    "#64748B",
        "BRACK_FG":    "#FFFFFF",
        "BRACK_HOV":   "#475569",
        "EQUAL_BG":    "#16A34A",
        "EQUAL_FG":    "#FFFFFF",
        "EQUAL_HOV":   "#15803D",
        "CLEAR_BG":    "#DC2626",
        "CLEAR_FG":    "#FFFFFF",
        "CLEAR_HOV":   "#B91C1C",
        "BACK_BG":     "#D97706",
        "BACK_FG":     "#FFFFFF",
        "BACK_HOV":    "#B45309",
        "TOGGLE_BG":   "#CBD5E1",
        "TOGGLE_FG":   "#475569",
        "HIST_BG":     "#F1F5F9",
        "HIST_FG":     "#0F172A",
        "HIST_ITEM":   "#E2E8F0",
        "HIST_HEAD":   "#6D28D9",
        "SCROLLBAR":   "#CBD5E1",
    },
}

# ══════════════════════════════════════════════════════════════
#  CALCULATOR
# ══════════════════════════════════════════════════════════════
class Calculator:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Calculator")
        self.root.resizable(False, False)

        self.theme_name = "dark"
        self.T = THEMES[self.theme_name]

        self.expression    = ""
        self.result_shown  = False
        self.history       = []          # list of "expr = result" strings
        self.all_widgets   = []          # (widget, role) for re-theming
        self.btn_meta      = []          # (btn, role) for re-theming buttons

        self._build_ui()
        self._bind_keyboard()
        self._apply_theme()

    # ─────────────────────────────────────────────────────────
    #  UI BUILD
    # ─────────────────────────────────────────────────────────
    def _build_ui(self):
        T = self.T
        self.root.configure(bg=T["BG"])

        # ── top bar (theme toggle) ──────────────────────────
        topbar = tk.Frame(self.root, bg=T["BG"])
        topbar.pack(fill="x", padx=10, pady=(8, 0))

        self.toggle_btn = tk.Button(
            topbar, text="☀ Light Mode",
            font=("Segoe UI", 10), bd=0, relief="flat",
            cursor="hand2", padx=8, pady=3,
            command=self._toggle_theme
        )
        self.toggle_btn.pack(side="right")

        # ── display ─────────────────────────────────────────
        disp_frame = tk.Frame(self.root, bg=T["BG"], padx=10, pady=4)
        disp_frame.pack(fill="x")

        self.expr_var = tk.StringVar(value="")
        self.expr_label = tk.Label(
            disp_frame, textvariable=self.expr_var,
            font=("Segoe UI", 12), anchor="e",
            padx=12, pady=4, width=28
        )
        self.expr_label.pack(fill="x")

        self.disp_var = tk.StringVar(value="0")
        self.disp_label = tk.Label(
            disp_frame, textvariable=self.disp_var,
            font=("Segoe UI", 30, "bold"), anchor="e",
            padx=12, pady=6, width=28
        )
        self.disp_label.pack(fill="x")

        # ── main area (buttons + history side panel) ────────
        main = tk.Frame(self.root, bg=T["BG"])
        main.pack(padx=10, pady=(0, 10))

        self._build_buttons(main)
        self._build_history(main)

    def _build_buttons(self, parent):
        frame = tk.Frame(parent, bg=self.T["BG"])
        frame.pack(side="left", padx=(0, 8))
        self.btn_frame = frame

        # ── layout ──────────────────────────────────────────
        # (label, row, col, colspan, role)
        layout = [
            # Row 0 – clear / back / mod / divide
            ("C",    0, 0, 1, "clear"),
            ("⌫",   0, 1, 1, "back"),
            ("mod",  0, 2, 1, "spec"),
            ("÷",    0, 3, 1, "op"),
            # Row 1 – special functions
            ("xʸ",   1, 0, 1, "spec"),
            ("√",    1, 1, 1, "spec"),
            ("1/x",  1, 2, 1, "spec"),
            ("×",    1, 3, 1, "op"),
            # Row 2 – brackets row + minus
            ("(",    2, 0, 1, "brack"),
            (")",    2, 1, 1, "brack"),
            ("+/−",  2, 2, 1, "num"),
            ("−",    2, 3, 1, "op"),
            # Row 3 – 7 8 9 +
            ("7",    3, 0, 1, "num"),
            ("8",    3, 1, 1, "num"),
            ("9",    3, 2, 1, "num"),
            ("+",    3, 3, 1, "op"),
            # Row 4 – 4 5 6
            ("4",    4, 0, 1, "num"),
            ("5",    4, 1, 1, "num"),
            ("6",    4, 2, 1, "num"),
            # Row 5 – 1 2 3
            ("1",    5, 0, 1, "num"),
            ("2",    5, 1, 1, "num"),
            ("3",    5, 2, 1, "num"),
            # Row 6 – 0 . =
            ("0",    6, 0, 1, "num"),
            (".",    6, 1, 1, "num"),
            ("=",    6, 2, 2, "equal"),   # spans cols 2-3
        ]

        self.buttons = []
        for (text, row, col, span, role) in layout:
            btn = tk.Button(
                frame, text=text,
                font=("Segoe UI", 15, "bold"),
                width=4, height=2,
                bd=0, relief="flat", cursor="hand2",
                command=lambda t=text: self._on_button(t)
            )
            btn.grid(row=row, column=col, columnspan=span,
                     padx=4, pady=4, sticky="nsew")
            self.buttons.append((btn, role))

    def _build_history(self, parent):
        T = self.T
        self.hist_frame = tk.Frame(parent, bg=T["HIST_BG"], width=200)
        self.hist_frame.pack(side="left", fill="y")
        self.hist_frame.pack_propagate(False)

        head = tk.Label(
            self.hist_frame, text="History",
            font=("Segoe UI", 13, "bold"), anchor="w",
            padx=10, pady=6
        )
        head.pack(fill="x")
        self.hist_head_label = head

        # scrollable list
        canvas = tk.Canvas(self.hist_frame, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.hist_frame, orient="vertical",
                                  command=canvas.yview)
        self.hist_inner = tk.Frame(canvas)

        self.hist_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.hist_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.hist_canvas = canvas
        self.hist_scrollbar = scrollbar

        # clear history button
        self.hist_clear_btn = tk.Button(
            self.hist_frame, text="Clear History",
            font=("Segoe UI", 9), bd=0, relief="flat",
            cursor="hand2", pady=4,
            command=self._clear_history
        )
        self.hist_clear_btn.pack(fill="x", padx=6, pady=(2, 6))

    # ─────────────────────────────────────────────────────────
    #  THEME
    # ─────────────────────────────────────────────────────────
    def _toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.T = THEMES[self.theme_name]
        self._apply_theme()

    def _apply_theme(self):
        T = self.T
        self.root.configure(bg=T["BG"])
        self.toggle_btn.config(
            text="☀ Light Mode" if self.theme_name == "dark" else "🌙 Dark Mode",
            bg=T["TOGGLE_BG"], fg=T["TOGGLE_FG"],
            activebackground=T["TOGGLE_BG"], activeforeground=T["TOGGLE_FG"]
        )
        # display
        self.expr_label.config(bg=T["DISPLAY_BG"], fg=T["EXPR_FG"])
        self.disp_label.config(bg=T["DISPLAY_BG"], fg=T["DISPLAY_FG"])
        # frames
        for frame in [self.btn_frame, self.hist_frame, self.hist_inner,
                      self.root.winfo_children()[1]]:   # topbar
            try: frame.config(bg=T["BG"])
            except: pass
        self.hist_canvas.config(bg=T["HIST_BG"])
        self.hist_scrollbar.config(bg=T["SCROLLBAR"])
        self.hist_head_label.config(bg=T["HIST_BG"], fg=T["HIST_HEAD"])
        self.hist_clear_btn.config(
            bg=T["HIST_BG"], fg=T["EXPR_FG"],
            activebackground=T["HIST_ITEM"], activeforeground=T["HIST_FG"]
        )
        # buttons
        role_colors = {
            "num":   (T["NUM_BG"],   T["NUM_FG"],   T["NUM_HOV"]),
            "op":    (T["OP_BG"],    T["OP_FG"],    T["OP_HOV"]),
            "spec":  (T["SPEC_BG"],  T["SPEC_FG"],  T["SPEC_HOV"]),
            "brack": (T["BRACK_BG"], T["BRACK_FG"], T["BRACK_HOV"]),
            "equal": (T["EQUAL_BG"], T["EQUAL_FG"], T["EQUAL_HOV"]),
            "clear": (T["CLEAR_BG"], T["CLEAR_FG"], T["CLEAR_HOV"]),
            "back":  (T["BACK_BG"],  T["BACK_FG"],  T["BACK_HOV"]),
        }
        for btn, role in self.buttons:
            bg, fg, hov = role_colors[role]
            btn.config(bg=bg, fg=fg,
                       activebackground=hov, activeforeground=fg)
            btn.bind("<Enter>", lambda e, b=btn, h=hov: b.config(bg=h))
            btn.bind("<Leave>", lambda e, b=btn, c=bg:  b.config(bg=c))
        # refresh history items
        self._redraw_history()

    # ─────────────────────────────────────────────────────────
    #  HISTORY
    # ─────────────────────────────────────────────────────────
    def _add_history(self, entry: str):
        self.history.insert(0, entry)
        if len(self.history) > 10:
            self.history = self.history[:10]
        self._redraw_history()

    def _redraw_history(self):
        T = self.T
        for w in self.hist_inner.winfo_children():
            w.destroy()
        if not self.history:
            lbl = tk.Label(self.hist_inner, text="No history yet",
                           font=("Segoe UI", 10), fg=T["EXPR_FG"],
                           bg=T["HIST_BG"], padx=10, pady=8)
            lbl.pack(anchor="w")
            return
        for entry in self.history:
            item = tk.Frame(self.hist_inner, bg=T["HIST_ITEM"],
                            pady=6, padx=8)
            item.pack(fill="x", pady=2, padx=4)
            lbl = tk.Label(item, text=entry, font=("Segoe UI", 10),
                           fg=T["HIST_FG"], bg=T["HIST_ITEM"],
                           anchor="w", justify="left", wraplength=170)
            lbl.pack(anchor="w")
            # click to restore expression
            result = entry.split("=")[-1].strip()
            for w in (item, lbl):
                w.bind("<Button-1>", lambda e, r=result: self._restore(r))
                w.config(cursor="hand2")

    def _clear_history(self):
        self.history.clear()
        self._redraw_history()

    def _restore(self, value: str):
        self.expression = value
        self.result_shown = True
        self.disp_var.set(value)
        self.expr_var.set("")

    # ─────────────────────────────────────────────────────────
    #  KEYBOARD
    # ─────────────────────────────────────────────────────────
    def _bind_keyboard(self):
        named = {
            "Return":    "=",
            "KP_Enter":  "=",
            "BackSpace": "⌫",
            "Escape":    "C",
            "parenleft": "(",
            "parenright":")",
        }
        for key, action in named.items():
            self.root.bind(f"<{key}>",
                           lambda e, a=action: self._on_button(a))

        char_map = {
            "0":"0","1":"1","2":"2","3":"3","4":"4",
            "5":"5","6":"6","7":"7","8":"8","9":"9",
            ".":".",
            "+":"+",
            "-":"−",
            "*":"×",
            "/":"÷",
            "%":"mod",
            "^":"xʸ",
            "r":"√",
        }
        for ch, action in char_map.items():
            self.root.bind(ch, lambda e, a=action: self._on_button(a))

    # ─────────────────────────────────────────────────────────
    #  CORE LOGIC
    # ─────────────────────────────────────────────────────────
    def _on_button(self, label: str):
        op_chars = set("×÷+−")

        # ── Clear ──────────────────────────────────────────
        if label == "C":
            self.expression    = ""
            self.result_shown  = False
            self.disp_var.set("0")
            self.expr_var.set("")
            return

        # ── Backspace ──────────────────────────────────────
        if label == "⌫":
            if self.result_shown:
                self.expression   = ""
                self.result_shown = False
                self.disp_var.set("0")
                self.expr_var.set("")
            else:
                self.expression = self.expression[:-1]
                self._refresh_display()
            return

        # ── Evaluate ───────────────────────────────────────
        if label == "=":
            if not self.expression:
                return
            try:
                raw = self._prepare(self.expression)
                result = eval(raw, {"__builtins__": {}},
                              {"sqrt": math.sqrt, "pow": pow})
                result = self._tidy(result)
                entry = f"{self.expression} = {result}"
                self._add_history(entry)
                self.expr_var.set(self.expression + "  =")
                self.disp_var.set(str(result))
                self.expression   = str(result)
                self.result_shown = True
            except ZeroDivisionError:
                self._show_error("÷ 0 Error")
            except Exception:
                self._show_error("Error")
            return

        # ── Sign toggle ────────────────────────────────────
        if label == "+/−":
            if not self.expression:
                self.expression = "-"
            elif self.expression.startswith("-"):
                self.expression = self.expression[1:]
            else:
                self.expression = "-" + self.expression
            self._refresh_display()
            return

        # ── mod ────────────────────────────────────────────
        if label == "mod":
            if self.result_shown:
                self.result_shown = False
            self.expression += "%"
            self._refresh_display()
            return

        # ── Power (xʸ) ─────────────────────────────────────
        if label == "xʸ":
            if self.result_shown:
                self.result_shown = False
            self.expression += "**"
            self._refresh_display()
            return

        # ── Square root ────────────────────────────────────
        if label == "√":
            try:
                if self.result_shown or self.expression:
                    val = eval(self._prepare(self.expression),
                               {"__builtins__": {}}, {"sqrt": math.sqrt})
                    result = self._tidy(math.sqrt(float(val)))
                    entry = f"√({self.expression}) = {result}"
                    self._add_history(entry)
                    self.expr_var.set(f"√({self.expression})")
                    self.disp_var.set(str(result))
                    self.expression   = str(result)
                    self.result_shown = True
                else:
                    # prefix √ so user can type number after
                    self.expression = "sqrt("
                    self._refresh_display()
            except Exception:
                self._show_error("Error")
            return

        # ── 1/x ────────────────────────────────────────────
        if label == "1/x":
            try:
                val = float(eval(self._prepare(self.expression),
                                 {"__builtins__": {}}, {"sqrt": math.sqrt}))
                result = self._tidy(1 / val)
                entry = f"1/({self.expression}) = {result}"
                self._add_history(entry)
                self.expr_var.set(f"1/({self.expression})")
                self.disp_var.set(str(result))
                self.expression   = str(result)
                self.result_shown = True
            except ZeroDivisionError:
                self._show_error("÷ 0 Error")
            except Exception:
                self._show_error("Error")
            return

        # ── Brackets ───────────────────────────────────────
        if label in ("(", ")"):
            if self.result_shown and label == "(":
                self.expression   = ""
                self.result_shown = False
            self.expression += label
            self._refresh_display()
            return

        # ── Digits / operators / dot ───────────────────────
        is_op = label in op_chars

        if self.result_shown and not is_op:
            self.expression   = ""
            self.result_shown = False

        if self.result_shown and is_op:
            self.result_shown = False

        # prevent double operators
        if is_op and self.expression and self.expression[-1] in op_chars:
            self.expression = self.expression[:-1]

        if is_op and not self.expression and label != "−":
            return

        self.expression += label
        self._refresh_display()

    # ─────────────────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────────────────
    def _prepare(self, expr: str) -> str:
        """Convert display symbols to Python-evaluable string."""
        return (expr
                .replace("×", "*")
                .replace("÷", "/")
                .replace("−", "-")
                .replace("√(", "sqrt("))

    def _tidy(self, value):
        """Remove unnecessary .0 from floats."""
        if isinstance(value, float):
            if value == int(value) and not math.isinf(value):
                return int(value)
            return round(value, 10)
        return value

    def _show_error(self, msg: str):
        self.disp_var.set(msg)
        self.expression   = ""
        self.expr_var.set("")
        self.result_shown = False

    def _refresh_display(self):
        self.disp_var.set(self.expression if self.expression else "0")
        self.expr_var.set("")


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    Calculator(root)
    root.mainloop()