import tkinter as tk
import random
import time
import json
import os
import math
import hashlib

# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------
THEMES = {
    "dark": dict(
        BG="#121212", BG_CARD="#1e1e1e", BG_ROW="#232323",
        FG="#e8e8e8", FG_MUTED="#9a9a9a", ACCENT="#4f8dfd",
        GREEN="#3ddc84", RED="#ff5c5c", YELLOW="#ffcc4d",
        PURPLE="#c792ea", ENTRY_BG="#2a2a2a", BTN_FG="#0a0a0a",
    ),
    "light": dict(
        BG="#f4f5f7", BG_CARD="#ffffff", BG_ROW="#eceef2",
        FG="#1c1c1e", FG_MUTED="#6b6b70", ACCENT="#3366cc",
        GREEN="#1f9254", RED="#d93025", YELLOW="#a9750c",
        PURPLE="#7b3fb5", ENTRY_BG="#e7e8ec", BTN_FG="#ffffff",
    ),
}

FONT_MAIN   = ("Segoe UI", 15)
FONT_TITLE  = ("Segoe UI", 27, "bold")
FONT_BIG    = ("Segoe UI", 84, "bold")
FONT_MCQ_Q  = ("Segoe UI", 46, "bold")
FONT_PARA_WORD = ("Segoe UI", 44, "bold")
FONT_SMALL  = ("Segoe UI", 11)
FONT_MONO   = ("Consolas", 13)

BASE_TIME_MS   = 5000
TIME_STEP_MS   = 100
QUESTIONS_PER_LEVEL = 5
MIN_TIME_MS    = 400
MAX_MISTAKES   = 3
TICK_MS        = 33

DURATION_OPTIONS = [1, 2, 5, 10, 15]     # minutes

SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_scores.json")

MODE_LABELS = {
    "L2N": "Letter -> Number",
    "N2L": "Number -> Letter",
    "PARA_N2L": "Paragraph: Number -> Word",
    "PARA_L2N": "Paragraph: Word -> Number",
    "MCQ": "MCQ Challenge",
    "CLOUD": "Cloud Master",
    "BLOCKS": "Wordtris",
    "BUBBLES": "Bubble Pop",
}
MODE_ICONS = {
    "L2N": "L2N", "N2L": "N2L", "PARA_N2L": "P:N2L", "PARA_L2N": "P:L2N",
    "MCQ": "MCQ", "CLOUD": "CLD", "BLOCKS": "BLK", "BUBBLES": "BUB",
}
GAME_META = {
    "CLOUD": "Cloud Master",
    "BLOCKS": "Wordtris (Block Master)",
    "BUBBLES": "Bubble Pop",
}

WORD_BANK = [
    "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG",
    "PYTHON IS FUN AND POWERFUL TO LEARN",
    "GOOD THINGS TAKE TIME AND PATIENCE",
    "LIFE IS SHORT SO ENJOY EVERY MOMENT",
    "PRACTICE MAKES A PERSON PERFECT EVERY DAY",
    "NEVER STOP LEARNING NEW THINGS",
    "HARD WORK ALWAYS PAYS OFF LATER",
    "BE KIND TO EVERYONE YOU MEET",
    "DREAM BIG AND WORK HARD",
    "EVERY EXPERT WAS ONCE A BEGINNER",
    "SMALL STEPS LEAD TO BIG CHANGES",
    "STAY CURIOUS AND KEEP EXPLORING",
    "AYUSH LOVES TO SOLVE PUZZLES DAILY",
    "READING BOOKS OPENS THE MIND",
    "SIMPLE IDEAS OFTEN WIN THE RACE",
]

TYPING_WORDS = [
    "APPLE", "TIGER", "HOUSE", "GARDEN", "WINDOW", "PENCIL", "MOUNTAIN", "RIVER",
    "GUITAR", "PLANET", "ROCKET", "CANDLE", "BASKET", "JACKET", "SILVER", "GOLDEN",
    "BRIDGE", "CASTLE", "DRAGON", "FOREST", "ISLAND", "JUNGLE", "KNIGHT", "LANTERN",
    "MIRROR", "NOODLE", "ORANGE", "PUZZLE", "QUEEN", "RABBIT", "SPIDER", "TUNNEL",
    "UMBRELLA", "VELVET", "WIZARD", "YELLOW", "ZEBRA", "CLOUD", "STORM", "OCEAN",
]


def load_scores():
    try:
        with open(SCORE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"players": {}}


def save_scores(data):
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def hash_password(pw):
    return hashlib.sha256((pw or "").encode("utf-8")).hexdigest()


def letter_to_code(ch):
    return str(ord(ch.upper()) - ord('A') + 1)


def wrap_letter_add(base_num, add_num):
    """base_num aur add_num dono 1-based (A=1...Z=26). Wraparound modulo 26."""
    return ((base_num + add_num - 1) % 26) + 1


class LetterNumberGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Letter <-> Number Game")
        self.geometry("700x800")
        self.minsize(580, 660)

        self.dark_mode = True
        self.colors = THEMES["dark"]
        self.configure(bg=self.colors["BG"])

        self.player_name = None
        self.scores_data = load_scores()

        self.mode = None
        self.score = 0
        self.mistakes = 0
        self.streak = 0
        self.questions_done = 0
        self.current_time_ms = BASE_TIME_MS
        self.current_answer = None
        self.timer_job = None
        self.deadline = None
        self.accepting_input = False
        self.q_start_time = None
        self.paused = False
        self.pause_saved_remaining = None
        self.pause_btn = None
        self.next_question_fn = None

        self.mcq_variant = "LETTER"        # "LETTER" ya "DIGIT"
        self.mcq_option_buttons = []

        self.para_direction = "PARA_N2L"
        self.para_duration_min = 2

        self.typing_direction = "W2N"      # "W2N" = word/letter dikhega -> number likho
        self.typing_duration_min = 2
        self.typing_anim_job = None
        self.typing_spawn_job = None
        self.typing_items = []
        self.wordtris_current = None

        self.history = []           # current player's games (in-memory, this run)
        self.session_id = 0

        self.container = tk.Frame(self, bg=self.colors["BG"])
        self.container.pack(fill="both", expand=True)

        self.show_login_screen()

    # -------------------------------------------------------------------
    def C(self, key):
        return self.colors[key]

    def clear_container(self):
        for job_attr in ("timer_job", "typing_anim_job", "typing_spawn_job"):
            job = getattr(self, job_attr, None)
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                setattr(self, job_attr, None)
        for w in self.container.winfo_children():
            w.destroy()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.colors = THEMES["dark"] if self.dark_mode else THEMES["light"]
        self.configure(bg=self.C("BG"))
        self.container.configure(bg=self.C("BG"))
        self.show_start_screen()

    def level_number(self):
        return (self.questions_done // QUESTIONS_PER_LEVEL) + 1

    def _btn(self, parent, text, cmd):
        return tk.Button(parent, text=text, font=FONT_MAIN, command=cmd,
                          bg=self.C("BG_CARD"), fg=self.C("FG"),
                          activebackground=self.C("ACCENT"), activeforeground="#ffffff",
                          relief="flat", cursor="hand2", bd=0)

    def _toolbtn(self, parent, text, cmd, fg=None):
        return tk.Button(parent, text=text, font=FONT_SMALL, command=cmd,
                          bg=self.C("BG_CARD"), fg=fg or self.C("FG"),
                          activebackground=self.C("ACCENT"), activeforeground="#ffffff",
                          relief="flat", cursor="hand2", bd=0)

    def _safe_focus(self, widget):
        try:
            widget.focus_set()
        except Exception:
            pass

    # =====================================================================
    # PER-PLAYER HIGH SCORES
    # =====================================================================
    def get_player_high(self, mode, player=None):
        player = player or self.player_name
        return self.scores_data.get("players", {}).get(player, {}).get("high_scores", {}).get(mode, 0)

    def update_player_high(self, mode, value):
        players = self.scores_data.setdefault("players", {})
        p = players.setdefault(self.player_name, {"high_scores": {}})
        hs = p.setdefault("high_scores", {})
        if value > hs.get(mode, 0):
            hs[mode] = value
            save_scores(self.scores_data)
            return True
        return False

    # =====================================================================
    # LOGIN SCREEN (naam + password, ek naam = ek hi user)
    # =====================================================================
    def show_login_screen(self):
        self.clear_container()
        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        tk.Label(wrap, text="Letter <-> Number", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(pady=(20, 4))
        tk.Label(wrap, text="Naam aur password daalo (naya naam ho toh nayi id ban jaayegi)",
                 font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED"), wraplength=380,
                 justify="center").pack(pady=(0, 18))

        name_var = tk.StringVar(value=self.player_name or "")
        tk.Label(wrap, text="Naam", font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack()
        name_entry = tk.Entry(wrap, textvariable=name_var, font=("Segoe UI", 18), justify="center",
                               bg=self.C("ENTRY_BG"), fg=self.C("FG"), insertbackground=self.C("FG"),
                               relief="flat", width=18)
        name_entry.pack(pady=(2, 10), ipady=6)

        pw_var = tk.StringVar(value="")
        tk.Label(wrap, text="Password", font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack()
        pw_entry = tk.Entry(wrap, textvariable=pw_var, font=("Segoe UI", 18), justify="center",
                             bg=self.C("ENTRY_BG"), fg=self.C("FG"), insertbackground=self.C("FG"),
                             relief="flat", width=18, show="*")
        pw_entry.pack(pady=(2, 6), ipady=6)

        error_lbl = tk.Label(wrap, text=" ", font=FONT_SMALL, bg=self.C("BG"), fg=self.C("RED"))
        error_lbl.pack(pady=(2, 6))

        self._safe_focus(name_entry)

        def do_login(event=None):
            name = name_var.get().strip()
            pw = pw_var.get()
            if not name:
                error_lbl.config(text="Naam likhna zaroori hai.")
                return
            if not pw:
                error_lbl.config(text="Password likhna zaroori hai.")
                return
            players = self.scores_data.setdefault("players", {})
            if name in players:
                stored = players[name].get("password")
                if stored is None:
                    players[name]["password"] = hash_password(pw)
                    save_scores(self.scores_data)
                elif hash_password(pw) != stored:
                    error_lbl.config(text="Galat password! Ye naam kisi aur ka hai.")
                    return
            else:
                players[name] = {"password": hash_password(pw), "high_scores": {}}
                save_scores(self.scores_data)
            self.player_name = name
            self.show_start_screen()

        name_entry.bind("<Return>", lambda e: pw_entry.focus_set())
        pw_entry.bind("<Return>", do_login)
        self._btn(wrap, "Login / Shuru Karo", do_login).pack(pady=10, ipadx=20, ipady=10)

    # =====================================================================
    # START SCREEN
    # =====================================================================
    def show_start_screen(self):
        self.clear_container()
        self.paused = False

        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        top_bar = tk.Frame(wrap, bg=self.C("BG"))
        top_bar.pack(fill="x", pady=(6, 0))
        theme_txt = "Dark: ON" if self.dark_mode else "Dark: OFF"
        tk.Button(top_bar, text=theme_txt, font=FONT_SMALL, command=self.toggle_theme,
                  bg=self.C("BG_CARD"), fg=self.C("FG"), relief="flat", cursor="hand2",
                  bd=0).pack(side="right", padx=10, ipadx=6, ipady=3)
        tk.Button(top_bar, text="Switch User", font=FONT_SMALL, command=self.show_login_screen,
                  bg=self.C("BG_CARD"), fg=self.C("FG"), relief="flat", cursor="hand2",
                  bd=0).pack(side="right", padx=4, ipadx=6, ipady=3)

        tk.Label(wrap, text="Letter <-> Number", font=FONT_TITLE,
                 bg=self.C("BG"), fg=self.C("FG")).pack(pady=(14, 2))
        tk.Label(wrap, text=f"Player: {self.player_name}", font=FONT_MAIN,
                 bg=self.C("BG"), fg=self.C("ACCENT")).pack(pady=(0, 2))
        tk.Label(wrap, text="A = a = 1   B = b = 2   ...   Z = z = 26",
                 font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=(0, 10))

        hs_frame = tk.Frame(wrap, bg=self.C("BG_CARD"))
        hs_frame.pack(pady=(0, 16), padx=30, fill="x")
        tk.Label(hs_frame, text="Tumhare Best Scores", font=FONT_SMALL,
                 bg=self.C("BG_CARD"), fg=self.C("YELLOW")).pack(pady=(8, 2))
        hs_line = "   ".join(f"{MODE_ICONS[m]}:{self.get_player_high(m)}" for m in MODE_ICONS)
        tk.Label(hs_frame, text=hs_line, font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED")).pack(pady=(0, 8))

        self._btn(wrap, "Conversion  (Letter <-> Number)",
                  self.show_conversion_menu).pack(pady=5, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "Paragraph Conversion",
                  self.show_paragraph_menu).pack(pady=5, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "MCQ Challenge  (A + 3 = ?)",
                  self.show_mcq_variant_setup).pack(pady=5, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "Typing Games  (Cloud / Wordtris / Bubbles)",
                  self.show_typing_direction_setup).pack(pady=5, ipadx=10, ipady=10, fill="x", padx=40)

        self._btn(wrap, "History dekho (mera)", self.show_history).pack(
            pady=(14, 4), ipadx=10, ipady=8, fill="x", padx=40)

        tk.Label(wrap,
                 text=("Har option ke andar jaake pehle direction/type chuno, phir shuru karo.\n"
                       "Kisi bhi game ke andar Hint button se step-by-step rules padho."),
                 font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED"), justify="center").pack(pady=14)

    # =====================================================================
    # CONVERSION (L2N / N2L) MENU
    # =====================================================================
    def show_conversion_menu(self):
        self.clear_container()
        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        tk.Label(wrap, text="Conversion", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(pady=(20, 6))
        tk.Label(wrap, text="Kaunsa tarah khelna chahte ho?", font=FONT_MAIN,
                 bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=(0, 18))

        self._btn(wrap, "Letter dikhega, Number likho",
                  lambda: self.start_game("L2N")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "Number dikhega, Letter likho",
                  lambda: self.start_game("N2L")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)

        self._btn(wrap, "Wapas", self.show_start_screen).pack(pady=(20, 6), ipadx=10, ipady=6)

    # =====================================================================
    # PARAGRAPH CONVERSION MENU -> duration setup
    # =====================================================================
    def show_paragraph_menu(self):
        self.clear_container()
        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        tk.Label(wrap, text="Paragraph Conversion", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(pady=(20, 6))
        tk.Label(wrap, text="Kaunsa tarah khelna chahte ho?", font=FONT_MAIN,
                 bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=(0, 18))

        self._btn(wrap, "Number se Word decode karo",
                  lambda: self.show_paragraph_setup("PARA_N2L")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "Word ko Number mein likho",
                  lambda: self.show_paragraph_setup("PARA_L2N")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)

        self._btn(wrap, "Wapas", self.show_start_screen).pack(pady=(20, 6), ipadx=10, ipady=6)

    def show_paragraph_setup(self, direction):
        self.clear_container()
        self.para_direction = direction

        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        title = "Number se Word Decode" if direction == "PARA_N2L" else "Word ko Number mein Likho"
        tk.Label(wrap, text=title, font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(pady=(20, 18))

        tk.Label(wrap, text="Kitne der khelna chahte ho?", font=FONT_MAIN,
                 bg=self.C("BG"), fg=self.C("FG")).pack(pady=(0, 10))

        btn_row = tk.Frame(wrap, bg=self.C("BG"))
        btn_row.pack(pady=6)
        self.duration_buttons = {}
        for m in DURATION_OPTIONS:
            b = tk.Button(btn_row, text=f"{m} min", font=FONT_MAIN,
                          command=lambda m=m: self.select_duration(m, "para"),
                          bg=self.C("ACCENT") if m == self.para_duration_min else self.C("BG_CARD"),
                          fg="#ffffff" if m == self.para_duration_min else self.C("FG"),
                          relief="flat", cursor="hand2", bd=0)
            b.pack(side="left", padx=6, ipadx=10, ipady=8)
            self.duration_buttons[m] = b

        hint = ("Har shabd ek-ek karke aayega. Jawab likhkar SPACE (ya Enter) dabao -\n"
                "agla shabd apne aap aa jaayega.")
        tk.Label(wrap, text=hint, font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED"),
                 justify="center").pack(pady=(10, 22))

        self._btn(wrap, "Shuru Karo", lambda: self.start_game(direction)).pack(
            pady=6, ipadx=20, ipady=10)
        self._btn(wrap, "Wapas", self.show_paragraph_menu).pack(pady=6, ipadx=10, ipady=6)

    # =====================================================================
    # MCQ CHALLENGE SETUP
    # =====================================================================
    def show_mcq_variant_setup(self):
        self.clear_container()
        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        tk.Label(wrap, text="MCQ Challenge", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(pady=(20, 6))
        tk.Label(wrap, text="Kaunsa tarah khelna chahte ho?", font=FONT_MAIN,
                 bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=(0, 6))
        tk.Label(wrap, text="Jaise: A + 3 = 4 = D   |   Z + 5 = 31 -> 5 = E",
                 font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=(0, 18))

        self._btn(wrap, "Letter Challenge   (A + 3 = ?)",
                  lambda: self._start_mcq("LETTER")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "Digit Challenge   (26 + 5 = ?)",
                  lambda: self._start_mcq("DIGIT")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)

        self._btn(wrap, "Wapas", self.show_start_screen).pack(pady=(20, 6), ipadx=10, ipady=6)

    def _start_mcq(self, variant):
        self.mcq_variant = variant
        self.start_game("MCQ")

    # =====================================================================
    # TYPING GAMES: direction -> game -> duration
    # =====================================================================
    def show_typing_direction_setup(self):
        self.clear_container()
        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        tk.Label(wrap, text="Typing Games", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(pady=(20, 18))
        tk.Label(wrap, text="Pehle direction chuno:", font=FONT_MAIN,
                 bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=(0, 14))

        self._btn(wrap, "Word/Letter dikhega, Number likho",
                  lambda: self._set_typing_direction("W2N")).pack(
            pady=6, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "Number dikhega, Word/Letter likho",
                  lambda: self._set_typing_direction("N2W")).pack(
            pady=6, ipadx=10, ipady=10, fill="x", padx=40)

        self._btn(wrap, "Wapas", self.show_start_screen).pack(pady=(20, 6), ipadx=10, ipady=6)

    def _set_typing_direction(self, direction):
        self.typing_direction = direction
        self.show_typing_games_menu()

    def show_typing_games_menu(self):
        self.clear_container()
        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        dir_txt = "Word/Letter se Number" if self.typing_direction == "W2N" else "Number se Word/Letter"
        tk.Label(wrap, text="Typing Games", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(pady=(20, 4))
        tk.Label(wrap, text=dir_txt, font=FONT_SMALL, bg=self.C("BG"), fg=self.C("ACCENT")).pack(pady=(0, 14))
        tk.Label(wrap, text="Koi bhi ek game chuno:", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=(0, 18))

        self._btn(wrap, "Cloud Master - words/codes upar se niche aate hain",
                  lambda: self.show_typing_duration_setup("CLOUD")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "Wordtris - ek time par sirf ek block girta hai",
                  lambda: self.show_typing_duration_setup("BLOCKS")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)
        self._btn(wrap, "Bubble Pop - ek letter/digit, sahi type karo pop ho jaaye",
                  lambda: self.show_typing_duration_setup("BUBBLES")).pack(pady=6, ipadx=10, ipady=10, fill="x", padx=40)

        self._btn(wrap, "Wapas", self.show_typing_direction_setup).pack(pady=(20, 6), ipadx=10, ipady=6)

    def show_typing_duration_setup(self, game_key):
        self.clear_container()
        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        tk.Label(wrap, text=GAME_META[game_key], font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(pady=(20, 6))
        dir_txt = "Word/Letter se Number" if self.typing_direction == "W2N" else "Number se Word/Letter"
        tk.Label(wrap, text=dir_txt, font=FONT_SMALL, bg=self.C("BG"), fg=self.C("ACCENT")).pack(pady=(0, 16))

        tk.Label(wrap, text="Kitne der khelna chahte ho?", font=FONT_MAIN,
                 bg=self.C("BG"), fg=self.C("FG")).pack(pady=(0, 10))

        btn_row = tk.Frame(wrap, bg=self.C("BG"))
        btn_row.pack(pady=6)
        self.duration_buttons = {}
        for m in DURATION_OPTIONS:
            b = tk.Button(btn_row, text=f"{m} min", font=FONT_MAIN,
                          command=lambda m=m: self.select_duration(m, "typing"),
                          bg=self.C("ACCENT") if m == self.typing_duration_min else self.C("BG_CARD"),
                          fg="#ffffff" if m == self.typing_duration_min else self.C("FG"),
                          relief="flat", cursor="hand2", bd=0)
            b.pack(side="left", padx=6, ipadx=10, ipady=8)
            self.duration_buttons[m] = b

        tk.Label(wrap, text="Speed shuru mein slow rehti hai, time ke saath thodi badhti hai.\n3 miss = game over.",
                 font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED"), justify="center").pack(pady=(14, 22))

        self._btn(wrap, "Shuru Karo", lambda: self.start_game(game_key)).pack(pady=6, ipadx=20, ipady=10)
        self._btn(wrap, "Wapas", self.show_typing_games_menu).pack(pady=6, ipadx=10, ipady=6)

    def select_duration(self, m, kind):
        if kind == "para":
            self.para_duration_min = m
        else:
            self.typing_duration_min = m
        for val, b in self.duration_buttons.items():
            b.configure(bg=self.C("ACCENT") if val == m else self.C("BG_CARD"),
                        fg="#ffffff" if val == m else self.C("FG"))

    # =====================================================================
    # SHARED GAME START
    # =====================================================================
    def start_game(self, mode):
        self._start_game_actual(mode)

    def _start_game_actual(self, mode):
        self.mode = mode
        self.score = 0
        self.mistakes = 0
        self.streak = 0
        self.questions_done = 0
        self.current_time_ms = BASE_TIME_MS
        self.paused = False
        self.pause_saved_remaining = None
        self.session_id += 1

        if mode in ("PARA_N2L", "PARA_L2N"):
            self.para_direction = mode
            self.build_paragraph_screen()
        elif mode == "MCQ":
            self.build_mcq_screen()
            self.next_mcq_question()
        elif mode == "CLOUD":
            self.build_cloud_screen()
        elif mode == "BLOCKS":
            self.build_wordtris_screen()
        elif mode == "BUBBLES":
            self.build_bubbles_screen()
        else:
            self.next_question_fn = self.next_question
            self.build_game_screen()
            self.next_question()

    # =====================================================================
    # Toolbar (har game screen par)
    # =====================================================================
    def add_game_toolbar(self, help_text):
        bar = tk.Frame(self.container, bg=self.C("BG"))
        bar.pack(fill="x", padx=16, pady=(10, 0))

        self._toolbtn(bar, "Hint", lambda: self.show_help_popup(help_text)).pack(
            side="left", padx=3, ipadx=8, ipady=4)
        self.pause_btn = self._toolbtn(bar, "Pause", self.toggle_pause)
        self.pause_btn.pack(side="left", padx=3, ipadx=8, ipady=4)
        self._toolbtn(bar, "Restart", self.restart_current).pack(side="left", padx=3, ipadx=8, ipady=4)
        self._toolbtn(bar, "Exit", self.exit_to_menu, fg=self.C("RED")).pack(side="left", padx=3, ipadx=8, ipady=4)

    def show_help_popup(self, text):
        win = tk.Toplevel(self)
        win.title("Hint / Help")
        win.configure(bg=self.C("BG_CARD"))
        win.geometry("460x460")
        win.transient(self)
        tk.Label(win, text=text, font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG"),
                 justify="left", wraplength=420).pack(padx=18, pady=18, fill="both", expand=True)
        tk.Button(win, text="Theek Hai", font=FONT_MAIN, command=win.destroy,
                  bg=self.C("ACCENT"), fg=self.C("BTN_FG"), relief="flat", cursor="hand2",
                  bd=0).pack(pady=(0, 16), ipadx=16, ipady=6)

    def restart_current(self):
        self.start_game(self.mode)

    def exit_to_menu(self):
        self.paused = False
        self.show_start_screen()

    def _l2n_n2l_help_text(self):
        if self.mode == "L2N":
            steps = [
                "1. Ek letter dikhega (chota ya bada, A-Z).",
                "2. Uska number likho (A=1, B=2 ... Z=26).",
                "3. Sahi type hote hi apne aap check ho jaata hai.",
                "4. Har 5 sawaal ke baad time 0.1 sec kam ho jaata hai - level badhta hai.",
                "5. 3 galtiyon ke baad game over ho jaata hai.",
            ]
        else:
            steps = [
                "1. Ek number dikhega (1-26).",
                "2. Uska letter likho - chota ya bada dono chalega.",
                "3. Sahi type hote hi apne aap check ho jaata hai.",
                "4. Har 5 sawaal ke baad time 0.1 sec kam ho jaata hai - level badhta hai.",
                "5. 3 galtiyon ke baad game over ho jaata hai.",
            ]
        steps += ["", "Pause se timer ruk jaata hai.", "Restart se naya game shuru hota hai.",
                  "Exit se home screen par chale jaate ho."]
        return "\n".join(steps)

    def _mcq_help_text(self):
        if self.mcq_variant == "LETTER":
            steps = [
                "1. Ek sawaal dikhega jaise 'A + 3 = ?'.",
                "2. Letter ko pehle number mein socho (A=1...Z=26), phir add karo.",
                "3. Agar total 26 se zyada ho jaaye, toh 26 ghata kar wraparound karo",
                "   (jaise Z+5 = 31, 31-26 = 5 = E).",
                "4. 4 options mein se sahi letter par click karo.",
            ]
        else:
            steps = [
                "1. Ek sawaal dikhega jaise '26 + 5 = ?'.",
                "2. Dono number add karo. Agar total 26 se zyada ho jaaye,",
                "   toh 26 ghata kar wraparound karo (jaise 26+5=31, 31-26=5).",
                "3. 4 options mein se sahi number par click karo.",
            ]
        steps += [
            "5. Har 5 sawaal ke baad time 0.1 sec kam ho jaata hai - level badhta hai.",
            "6. 3 galtiyon ke baad game over ho jaata hai.",
            "", "Pause se timer ruk jaata hai.", "Restart se naya game shuru hota hai.",
            "Exit se home screen par chale jaate ho.",
        ]
        return "\n".join(steps)

    def _paragraph_help_text(self):
        if self.para_direction == "PARA_N2L":
            first = "1. Har shabd number-code mein dikhega (A=1...Z=26, '-' se letters judte hain)."
            second = "2. Uska sahi word likho."
        else:
            first = "1. Har shabd plain likha dikhega."
            second = "2. Uska number-code likho (letters ke beech '-', jaise THE = 20-8-5)."
        steps = [
            first, second,
            "3. Jawab likhkar SPACE ya Enter dabao - agla shabd apne aap aa jaayega.",
            "4. Poora sahi na ho tab bhi jitne letters/codes sahi jagah par sahi\n   honge utne partial points milenge.",
            "", "Pause se timer ruk jaata hai.", "Restart se naya paragraph milta hai.",
            "Exit se home screen par chale jaate ho.",
        ]
        return "\n".join(steps)

    def _typing_help_text(self, mode):
        if mode == "BUBBLES":
            direction_line = ("Letter dikhega (A-Z), uska NUMBER type karna hai (A=1...Z=26)."
                               if self.typing_direction == "W2N" else
                               "Number dikhega (1-26), uska LETTER type karna hai.")
        else:
            direction_line = ("Word dikhega, uska NUMBER-CODE type karna hai (jaise THE = 20-8-5)."
                               if self.typing_direction == "W2N" else
                               "Number-code dikhega (jaise 20-8-5), uska WORD type karna hai.")
        if mode == "CLOUD":
            steps = [
                "1. Screen par clouds upar se niche aate rahenge, unpar text likha hoga.",
                f"2. {direction_line}",
                "3. Niche box mein wahi jawab likho, phir SPACE ya Enter dabao.",
                "4. Sahi hua toh cloud pop ho jaayega aur score milega.",
                "5. Chaho toh seedha cloud par click/tap karke bhi use hata sakte ho.",
                "6. Kabhi-kabhi ek khaali (empty) cloud bhi aayega - usme kuch\n   type karne ki zaroorat nahi, wo bina nuksan ke chala jaayega.",
                "7. Agar (khaali nahi wala) cloud zameen tak pahunch gaya, 1 galti gin jaayegi.",
                "8. 3 galtiyon ya time khatam hone par game over ho jaata hai.",
                "9. Time ke saath speed aur naye clouds aane ki raftaar dono thodi badhti hai\n   (shuru mein dono slow rehte hain).",
            ]
        elif mode == "BLOCKS":
            steps = [
                "1. Ek block upar se seedha niche girega, usmein text likha hoga.",
                f"2. {direction_line}",
                "3. Jawab likho, phir SPACE ya Enter dabao - ya seedha block par click/tap karo.",
                "4. Sahi hua toh block toot jaayega aur turant agla block aa jaayega.",
                "5. Agar block zameen tak pahunch gaya (miss), 1 galti gin jaayegi,\n   lekin agla block thoda SLOW speed se aayega.",
                "6. Naya block tabhi aata hai jab pehla wala khatam (sahi ya miss) ho jaaye -\n   ek time par sirf ek hi block hota hai.",
                "7. 3 galtiyon ya time khatam hone par game over ho jaata hai.",
            ]
        else:
            steps = [
                "1. Screen par ek ya zyada bubbles dikhenge, unpar ek LETTER ya NUMBER likha hoga.",
                f"2. {direction_line}",
                "3. Jawab type karo - poora sahi hote hi bubble apne aap pop ho jaayega\n   (SPACE ya Enter dabane ki zaroorat nahi).",
                "4. Chaho toh seedha bubble par click/tap karke bhi use pop kar sakte ho.",
                "5. Har bubble ki apni ek limited zindagi hoti hai - time khatam hone par\n   bina pop hue gayab ho jaayega aur 1 galti gin jaayegi.",
                "6. 3 galtiyon ya time khatam hone par game over ho jaata hai.",
            ]
        steps += ["", "Pause se sab ruk jaata hai.", "Restart se naya round milta hai.",
                  "Exit se home screen par chale jaate ho."]
        return "\n".join(steps)

    # =====================================================================
    # PAUSE / RESUME
    # =====================================================================
    def toggle_pause(self):
        is_para = self.mode in ("PARA_N2L", "PARA_L2N")
        is_typing = self.mode in ("CLOUD", "BLOCKS", "BUBBLES")
        is_mcq = self.mode == "MCQ"

        if not self.paused:
            if self.timer_job:
                self.after_cancel(self.timer_job)
                self.timer_job = None
            if self.typing_anim_job:
                self.after_cancel(self.typing_anim_job)
                self.typing_anim_job = None
            if self.typing_spawn_job:
                self.after_cancel(self.typing_spawn_job)
                self.typing_spawn_job = None
            self.paused = True

            if is_para:
                self.pause_saved_remaining = max(0, self.para_deadline - time.time())
                self._set_widget_state(self.para_entry, "disabled")
            elif is_typing:
                self.pause_saved_remaining = max(0, self.typing_deadline - time.time())
                self._set_widget_state(self.typing_entry, "disabled")
            elif is_mcq:
                self.pause_saved_remaining = max(0, self.deadline - time.time()) if self.deadline else None
                self.accepting_input = False
                for b in self.mcq_option_buttons:
                    self._set_widget_state(b, "disabled")
            else:
                self.pause_saved_remaining = max(0, self.deadline - time.time()) if self.deadline else None
                self.accepting_input = False
                self._set_widget_state(self.entry, "disabled")
            if self.pause_btn:
                self.pause_btn.config(text="Resume")
        else:
            self.paused = False
            if is_para:
                self.para_deadline = time.time() + (self.pause_saved_remaining or 0)
                self._set_widget_state(self.para_entry, "normal")
                self._safe_focus(self.para_entry)
                self.tick_paragraph_timer()
            elif is_typing:
                self.typing_deadline = time.time() + (self.pause_saved_remaining or 0)
                self._set_widget_state(self.typing_entry, "normal")
                self._safe_focus(self.typing_entry)
                if self.mode == "CLOUD":
                    self._typing_tick_cloud()
                    self._cloud_schedule_spawn()
                elif self.mode == "BLOCKS":
                    self._typing_tick_wordtris()
                else:
                    self._typing_tick_bubbles()
                    self._bubbles_schedule_spawn()
            elif is_mcq:
                self.deadline = time.time() + (self.pause_saved_remaining or 0)
                self.accepting_input = True
                for b in self.mcq_option_buttons:
                    self._set_widget_state(b, "normal")
                self.tick_timer()
            else:
                self.deadline = time.time() + (self.pause_saved_remaining or 0)
                self.accepting_input = True
                self._set_widget_state(self.entry, "normal")
                self._safe_focus(self.entry)
                self.tick_timer()
            if self.pause_btn:
                self.pause_btn.config(text="Pause")

    def _set_widget_state(self, widget, state):
        try:
            widget.config(state=state)
        except Exception:
            pass

    # =====================================================================
    # LETTER <-> NUMBER SCREEN  (mode 1 & 2)
    # =====================================================================
    def build_game_screen(self):
        self.clear_container()
        self.add_game_toolbar(self._l2n_n2l_help_text())

        top = tk.Frame(self.container, bg=self.C("BG"))
        top.pack(fill="x", pady=(12, 0), padx=20)

        self.score_lbl = tk.Label(top, text="Score: 0", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("GREEN"))
        self.score_lbl.pack(side="left")

        self.level_lbl = tk.Label(top, text="Level 1", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("PURPLE"))
        self.level_lbl.pack(side="left", padx=20)

        self.lives_lbl = tk.Label(top, text="XXX", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("RED"))
        self.lives_lbl.pack(side="right")

        self.streak_lbl = tk.Label(self.container, text=" ", font=FONT_SMALL, bg=self.C("BG"), fg=self.C("YELLOW"))
        self.streak_lbl.pack(pady=(4, 0))

        bar_wrap = tk.Frame(self.container, bg=self.C("BG_CARD"), height=10)
        bar_wrap.pack(fill="x", padx=20, pady=(10, 0))
        bar_wrap.pack_propagate(False)
        self.timer_bar = tk.Frame(bar_wrap, bg=self.C("ACCENT"), height=10)
        self.timer_bar.place(x=0, y=0, relheight=1, relwidth=1)

        card = tk.Frame(self.container, bg=self.C("BG_CARD"))
        card.pack(expand=True, fill="both", padx=20, pady=20)

        self.prompt_lbl = tk.Label(card, text="", font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED"))
        self.prompt_lbl.pack(pady=(30, 0))

        self.question_lbl = tk.Label(card, text="", font=FONT_BIG, bg=self.C("BG_CARD"), fg=self.C("FG"))
        self.question_lbl.pack(pady=10)

        self.feedback_lbl = tk.Label(card, text=" ", font=FONT_MAIN, bg=self.C("BG_CARD"), fg=self.C("YELLOW"))
        self.feedback_lbl.pack(pady=(0, 6))

        self.answer_var = tk.StringVar()
        self.entry = tk.Entry(card, textvariable=self.answer_var, font=("Segoe UI", 28),
                               justify="center", bg=self.C("ENTRY_BG"), fg=self.C("FG"),
                               insertbackground=self.C("FG"), relief="flat", width=8)
        self.entry.pack(pady=10, ipady=8)
        self.entry.bind("<Return>", lambda e: self.submit_answer())
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self._safe_focus(self.entry)

        tk.Label(card, text="Bas type karo - apne aap check ho jaayega",
                 font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED")).pack(pady=(0, 20))

    def _lives_text(self):
        return "X " * (MAX_MISTAKES - self.mistakes) + ". " * self.mistakes

    def next_question(self):
        self.current_time_ms = max(
            MIN_TIME_MS,
            BASE_TIME_MS - TIME_STEP_MS * (self.questions_done // QUESTIONS_PER_LEVEL)
        )
        self.level_lbl.config(text=f"Level {self.level_number()}  -  {self.current_time_ms/1000:.1f}s")

        n = random.randint(1, 26)
        self.answer_var.set("")
        self.feedback_lbl.config(text=" ", fg=self.C("YELLOW"))
        self.accepting_input = True

        if self.mode == "L2N":
            letter = chr(ord('A') + n - 1) if random.random() < 0.5 else chr(ord('a') + n - 1)
            self.current_answer = str(n)
            self.prompt_lbl.config(text="Iska number likho")
            self.question_lbl.config(text=letter)
            self.current_question_text = letter
            self.current_q_type = "letter"
        else:
            letter_upper = chr(ord('A') + n - 1)
            letter_lower = chr(ord('a') + n - 1)
            self.current_answer = {letter_upper, letter_lower}
            self.prompt_lbl.config(text="Iska letter likho (chota ya bada dono chalega)")
            self.question_lbl.config(text=str(n))
            self.current_question_text = str(n)
            self.current_q_type = "digit"

        self.score_lbl.config(text=f"Score: {self.score}")
        self.lives_lbl.config(text=self._lives_text())
        self.streak_lbl.config(text=f"Combo x{self.streak}" if self.streak >= 2 else " ")

        self._safe_focus(self.entry)
        self.q_start_time = time.time()
        self.start_timer(self.current_time_ms)

    def start_timer(self, duration_ms):
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.deadline = time.time() + duration_ms / 1000
        self.duration_s = duration_ms / 1000
        self.tick_timer()

    def tick_timer(self):
        if self.paused:
            return
        remaining = self.deadline - time.time()
        frac = max(0.0, remaining / self.duration_s) if self.duration_s else 0
        self.timer_bar.place(relwidth=frac)

        if frac > 0.5:
            self.timer_bar.config(bg=self.C("ACCENT"))
        elif frac > 0.2:
            self.timer_bar.config(bg=self.C("YELLOW"))
        else:
            self.timer_bar.config(bg=self.C("RED"))

        if remaining <= 0:
            self.handle_timeout()
            return
        self.timer_job = self.after(TICK_MS, self.tick_timer)

    def on_key_release(self, event):
        if self.paused:
            return
        val = self.answer_var.get().strip()
        if not self.accepting_input or not val:
            return
        if self.mode == "L2N":
            if val.isdigit() and val == self.current_answer:
                self.submit_answer()
        else:
            if len(val) == 1 and val in self.current_answer:
                self.submit_answer()

    def submit_answer(self):
        if not self.accepting_input or self.paused:
            return
        val = self.answer_var.get().strip()
        if val == "":
            return
        if self.mode == "L2N":
            correct = (val == self.current_answer)
        else:
            correct = (len(val) == 1 and val in self.current_answer)

        if correct:
            self.register_correct(val)
        else:
            self.register_wrong(val, timeout=False)

    def handle_timeout(self):
        if not self.accepting_input:
            return
        self.register_wrong("", timeout=True)

    def register_correct(self, given):
        self.accepting_input = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
        if self.mode == "MCQ":
            for b in self.mcq_option_buttons:
                self._set_widget_state(b, "disabled")
        elapsed = round(time.time() - self.q_start_time, 2)

        self.streak += 1
        bonus = self.streak // 3
        self.score += 1 + bonus
        self.questions_done += 1

        self._log_history(self.current_q_type, self.current_question_text, given,
                           self._answer_display(), True, elapsed, self.current_time_ms / 1000)

        msg = "Sahi jawab!" + (f"  (+{1+bonus} combo)" if bonus else "")
        self.feedback_lbl.config(text=msg, fg=self.C("GREEN"))
        self.after(450, self.next_question_fn)

    def register_wrong(self, given, timeout):
        self.accepting_input = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
        if self.mode == "MCQ":
            for b in self.mcq_option_buttons:
                self._set_widget_state(b, "disabled")
        elapsed = round(time.time() - self.q_start_time, 2)

        self.streak = 0
        self.mistakes += 1
        self.questions_done += 1

        correct_txt = self._answer_display()
        self._log_history(self.current_q_type, self.current_question_text,
                           given if not timeout else "(time khatam)",
                           correct_txt, False, elapsed, self.current_time_ms / 1000)

        msg = "Time khatam!" if timeout else "Galat jawab!"
        self.feedback_lbl.config(text=f"{msg} Sahi tha: {correct_txt}", fg=self.C("RED"))
        self.lives_lbl.config(text=self._lives_text())

        if self.mistakes >= MAX_MISTAKES:
            self.after(900, self.show_game_over)
        else:
            self.after(900, self.next_question_fn)

    def _answer_display(self):
        if self.mode in ("L2N", "MCQ"):
            return self.current_answer
        return "/".join(sorted(self.current_answer))

    def _log_history(self, q_type, question, given, correct_answer, correct, elapsed,
                      limit=None, points=None, max_points=None):
        self.history.append({
            "serial": len(self.history) + 1,
            "player": self.player_name,
            "session": self.session_id,
            "mode": self.mode,
            "q_type": q_type,
            "question": question,
            "given": given if given else "-",
            "correct_answer": correct_answer,
            "correct": correct,
            "time": elapsed,
            "limit": limit,
            "points": points,
            "max_points": max_points,
        })

    # =====================================================================
    # MCQ CHALLENGE SCREEN
    # =====================================================================
    def build_mcq_screen(self):
        self.clear_container()
        self.next_question_fn = self.next_mcq_question
        self.add_game_toolbar(self._mcq_help_text())

        top = tk.Frame(self.container, bg=self.C("BG"))
        top.pack(fill="x", pady=(12, 0), padx=20)

        self.score_lbl = tk.Label(top, text="Score: 0", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("GREEN"))
        self.score_lbl.pack(side="left")
        self.level_lbl = tk.Label(top, text="Level 1", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("PURPLE"))
        self.level_lbl.pack(side="left", padx=20)
        self.lives_lbl = tk.Label(top, text="XXX", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("RED"))
        self.lives_lbl.pack(side="right")

        self.streak_lbl = tk.Label(self.container, text=" ", font=FONT_SMALL, bg=self.C("BG"), fg=self.C("YELLOW"))
        self.streak_lbl.pack(pady=(4, 0))

        bar_wrap = tk.Frame(self.container, bg=self.C("BG_CARD"), height=10)
        bar_wrap.pack(fill="x", padx=20, pady=(10, 0))
        bar_wrap.pack_propagate(False)
        self.timer_bar = tk.Frame(bar_wrap, bg=self.C("ACCENT"), height=10)
        self.timer_bar.place(x=0, y=0, relheight=1, relwidth=1)

        card = tk.Frame(self.container, bg=self.C("BG_CARD"))
        card.pack(expand=True, fill="both", padx=20, pady=20)

        self.prompt_lbl = tk.Label(card, text="Sahi jawab chuno", font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED"))
        self.prompt_lbl.pack(pady=(24, 0))

        self.question_lbl = tk.Label(card, text="", font=FONT_MCQ_Q, bg=self.C("BG_CARD"), fg=self.C("FG"))
        self.question_lbl.pack(pady=14)

        self.feedback_lbl = tk.Label(card, text=" ", font=FONT_MAIN, bg=self.C("BG_CARD"), fg=self.C("YELLOW"))
        self.feedback_lbl.pack(pady=(0, 10))

        options_grid = tk.Frame(card, bg=self.C("BG_CARD"))
        options_grid.pack(pady=10)
        self.mcq_option_buttons = []
        for i in range(4):
            b = tk.Button(options_grid, text="", font=("Segoe UI", 22, "bold"), width=6,
                          bg=self.C("BG_CARD"), fg=self.C("FG"), activebackground=self.C("ACCENT"),
                          activeforeground="#ffffff", relief="flat", cursor="hand2", bd=2)
            b.grid(row=i // 2, column=i % 2, padx=10, pady=10, ipadx=10, ipady=14)
            self.mcq_option_buttons.append(b)

        tk.Label(card, text="Sahi option par click karo",
                 font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED")).pack(pady=(6, 20))

    def next_mcq_question(self):
        self.current_time_ms = max(
            MIN_TIME_MS,
            BASE_TIME_MS - TIME_STEP_MS * (self.questions_done // QUESTIONS_PER_LEVEL)
        )
        self.level_lbl.config(text=f"Level {self.level_number()}  -  {self.current_time_ms/1000:.1f}s")
        self.feedback_lbl.config(text=" ", fg=self.C("YELLOW"))

        add_num = random.randint(1, 20)

        if self.mcq_variant == "LETTER":
            base_num = random.randint(1, 26)
            display_letter = chr(64 + base_num) if random.random() < 0.5 else chr(96 + base_num)
            result_num = wrap_letter_add(base_num, add_num)
            correct = chr(64 + result_num)
            question_text = f"{display_letter} + {add_num}"
            options = {correct}
            while len(options) < 4:
                options.add(chr(64 + random.randint(1, 26)))
            self.current_q_type = "letter"
        else:
            base_num = random.randint(1, 26)
            result_num = wrap_letter_add(base_num, add_num)
            correct = str(result_num)
            question_text = f"{base_num} + {add_num}"
            options = {correct}
            while len(options) < 4:
                options.add(str(random.randint(1, 26)))
            self.current_q_type = "digit"

        options = list(options)
        random.shuffle(options)
        self.current_answer = correct
        self.current_question_text = question_text
        self.question_lbl.config(text=f"{question_text} = ?")

        for i, btn in enumerate(self.mcq_option_buttons):
            opt = options[i]
            btn.config(text=opt, state="normal", command=lambda o=opt: self._mcq_choose(o),
                       bg=self.C("BG_CARD"), fg=self.C("FG"))

        self.score_lbl.config(text=f"Score: {self.score}")
        self.lives_lbl.config(text=self._lives_text())
        self.streak_lbl.config(text=f"Combo x{self.streak}" if self.streak >= 2 else " ")

        self.accepting_input = True
        self.q_start_time = time.time()
        self.start_timer(self.current_time_ms)

    def _mcq_choose(self, option):
        if not self.accepting_input or self.paused:
            return
        if option == self.current_answer:
            self.register_correct(option)
        else:
            self.register_wrong(option, timeout=False)

    # =====================================================================
    # PARAGRAPH MODE - ek shabd ek baar mein
    # =====================================================================
    def generate_paragraph(self, minutes):
        n_sentences = max(1, min(len(WORD_BANK), minutes * 2))
        if n_sentences <= len(WORD_BANK):
            chosen = random.sample(WORD_BANK, n_sentences)
        else:
            chosen = random.choices(WORD_BANK, k=n_sentences)
        return " ".join(chosen)

    def build_paragraph_screen(self):
        self.clear_container()

        sentence = self.generate_paragraph(self.para_duration_min)
        self.para_words = sentence.split()
        self.para_total_seconds = self.para_duration_min * 60
        self.para_index = 0
        self.para_total_points = 0
        self.para_max_points_total = 0
        self.para_full_correct = 0
        self.para_results = {}

        direction = self.para_direction
        if direction == "PARA_N2L":
            self.para_display_tokens = ["-".join(letter_to_code(c) for c in w) for w in self.para_words]
            self.para_target = [list(w.upper()) for w in self.para_words]
        else:
            self.para_display_tokens = list(self.para_words)
            self.para_target = [[letter_to_code(c) for c in w] for w in self.para_words]

        self.add_game_toolbar(self._paragraph_help_text())

        top = tk.Frame(self.container, bg=self.C("BG"))
        top.pack(fill="x", pady=(8, 0), padx=20)
        title = "Number -> Word Decode" if direction == "PARA_N2L" else "Word -> Number"
        tk.Label(top, text=title, font=FONT_MAIN, bg=self.C("BG"), fg=self.C("ACCENT")).pack(side="left")
        self.para_timer_lbl = tk.Label(top, text="", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("YELLOW"))
        self.para_timer_lbl.pack(side="right")

        bar_wrap = tk.Frame(self.container, bg=self.C("BG_CARD"), height=10)
        bar_wrap.pack(fill="x", padx=20, pady=(10, 0))
        bar_wrap.pack_propagate(False)
        self.para_bar = tk.Frame(bar_wrap, bg=self.C("ACCENT"), height=10)
        self.para_bar.place(x=0, y=0, relheight=1, relwidth=1)

        self.para_progress_text = tk.Text(self.container, height=5, wrap="word", bg=self.C("BG_CARD"),
                                           fg=self.C("FG_MUTED"), relief="flat", font=FONT_MONO,
                                           state="disabled", padx=12, pady=10)
        self.para_progress_text.pack(fill="x", padx=20, pady=(10, 10))

        card = tk.Frame(self.container, bg=self.C("BG_CARD"))
        card.pack(expand=True, fill="both", padx=20, pady=10)

        self.para_word_counter_lbl = tk.Label(card, text="", font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED"))
        self.para_word_counter_lbl.pack(pady=(18, 0))

        prompt_text = "Iska word likho, phir SPACE dabao" if direction == "PARA_N2L" else "Iska number-code likho (jaise THE = 20-8-5), phir SPACE dabao"
        self.para_prompt_lbl = tk.Label(card, text=prompt_text, font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED"))
        self.para_prompt_lbl.pack(pady=(4, 0))

        self.para_current_lbl = tk.Label(card, text="", font=FONT_PARA_WORD, bg=self.C("BG_CARD"), fg=self.C("FG"))
        self.para_current_lbl.pack(pady=14)

        self.para_feedback_lbl = tk.Label(card, text=" ", font=FONT_MAIN, bg=self.C("BG_CARD"), fg=self.C("YELLOW"))
        self.para_feedback_lbl.pack(pady=(0, 6))

        self.para_answer_var = tk.StringVar()
        self.para_entry = tk.Entry(card, textvariable=self.para_answer_var, font=("Segoe UI", 22),
                                    justify="center", bg=self.C("ENTRY_BG"), fg=self.C("FG"),
                                    insertbackground=self.C("FG"), relief="flat")
        self.para_entry.pack(pady=10, ipady=8, padx=60, fill="x")
        self.para_entry.bind("<KeyRelease>", self.on_para_key_release)
        self.para_entry.bind("<Return>", lambda e: self.submit_para_word())
        self._safe_focus(self.para_entry)

        tk.Label(card, text="Space dabate hi agla shabd apne aap check hoga",
                 font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED")).pack(pady=(0, 16))

        self.para_score_lbl = tk.Label(self.container, text="", font=FONT_SMALL, bg=self.C("BG"), fg=self.C("GREEN"))
        self.para_score_lbl.pack(pady=(0, 10))

        self.para_deadline = time.time() + self.para_total_seconds
        self.load_para_word()
        self.tick_paragraph_timer()

    def _render_para_progress(self):
        self.para_progress_text.config(state="normal")
        self.para_progress_text.delete("1.0", "end")
        sep = "   "
        text_content = ""
        offsets = []
        for i, token in enumerate(self.para_display_tokens):
            start = len(text_content)
            text_content += token
            end = len(text_content)
            offsets.append((start, end))
            if i != len(self.para_display_tokens) - 1:
                text_content += sep
        self.para_progress_text.insert("1.0", text_content)

        for i, (s, e) in enumerate(offsets):
            tagname = f"w{i}"
            self.para_progress_text.tag_add(tagname, f"1.0+{s}c", f"1.0+{e}c")
            if i in self.para_results:
                color = self.C("GREEN") if self.para_results[i] else self.C("RED")
                weight = "normal"
            elif i == self.para_index:
                color = self.C("ACCENT")
                weight = "bold"
            else:
                color = self.C("FG_MUTED")
                weight = "normal"
            self.para_progress_text.tag_configure(tagname, foreground=color,
                                                   font=(FONT_MONO[0], FONT_MONO[1], weight))
        self.para_progress_text.config(state="disabled")

    def load_para_word(self):
        if self.para_index >= len(self.para_words):
            self.finish_paragraph(timeout=False)
            return
        self.para_current_lbl.config(text=self.para_display_tokens[self.para_index])
        self.para_word_counter_lbl.config(text=f"Shabd {self.para_index + 1} / {len(self.para_words)}")
        self.para_answer_var.set("")
        self.para_feedback_lbl.config(text=" ", fg=self.C("YELLOW"))
        self.para_score_lbl.config(
            text=f"Score: {self.para_total_points} pts  -  {self.para_full_correct}/{self.para_index} shabd sahi")
        self._render_para_progress()
        self.para_word_start_time = time.time()
        if not self.paused:
            self._safe_focus(self.para_entry)

    def tick_paragraph_timer(self):
        if self.paused:
            return
        remaining = self.para_deadline - time.time()
        frac = max(0.0, remaining / self.para_total_seconds)
        self.para_bar.place(relwidth=frac)
        mins, secs = divmod(max(0, int(remaining)), 60)
        self.para_timer_lbl.config(text=f"{mins}:{secs:02d}")

        if frac > 0.5:
            self.para_bar.config(bg=self.C("ACCENT"))
        elif frac > 0.2:
            self.para_bar.config(bg=self.C("YELLOW"))
        else:
            self.para_bar.config(bg=self.C("RED"))

        if remaining <= 0:
            self.finish_paragraph(timeout=True)
            return
        self.timer_job = self.after(TICK_MS, self.tick_paragraph_timer)

    def _tokenize_guess(self, guess_word, direction):
        guess_word = guess_word.strip()
        if direction == "PARA_N2L":
            return list(guess_word.strip(".,!?").upper())
        else:
            return [c.strip() for c in guess_word.split("-") if c.strip() != ""]

    def on_para_key_release(self, event):
        if self.paused:
            return
        val = self.para_answer_var.get()
        if val.endswith(" ") and val.strip():
            self.submit_para_word()

    def submit_para_word(self):
        if self.paused:
            return
        given = self.para_answer_var.get().strip()
        if given == "":
            return
        self.evaluate_para_word(given)

    def evaluate_para_word(self, given):
        idx = self.para_index
        target = self.para_target[idx]
        given_tokens = self._tokenize_guess(given, self.para_direction)

        matched = sum(1 for a, b in zip(target, given_tokens) if a == b)
        word_len = len(target)
        is_full = (matched == word_len and len(given_tokens) == word_len)
        elapsed = round(time.time() - self.para_word_start_time, 2)

        self.para_total_points += matched
        self.para_max_points_total += word_len
        if is_full:
            self.para_full_correct += 1
        self.para_results[idx] = is_full

        display_q = self.para_display_tokens[idx]
        correct_answer_disp = self.para_words[idx].upper() if self.para_direction == "PARA_N2L" else "-".join(target)
        q_type = "digit" if self.para_direction == "PARA_N2L" else "word"
        self._log_history(q_type, display_q, given, correct_answer_disp, is_full, elapsed,
                           None, matched, word_len)

        if is_full:
            self.para_feedback_lbl.config(text=f"Sahi! (+{matched})", fg=self.C("GREEN"))
        else:
            self.para_feedback_lbl.config(
                text=f"Sahi tha: {correct_answer_disp}   (+{matched}/{word_len} points)", fg=self.C("RED"))

        self.para_index += 1
        self.after(500, self.load_para_word)

    def finish_paragraph(self, timeout):
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

        elapsed = round(self.para_total_seconds - max(0, self.para_deadline - time.time()), 1)
        total = len(self.para_words)
        pct = round((self.para_total_points / self.para_max_points_total) * 100) if self.para_max_points_total else 0
        remaining = max(0, self.para_deadline - time.time())
        speed_bonus = int(remaining / 10) if not timeout else 0
        points = self.para_total_points + speed_bonus
        self.score += points

        if pct >= 90:
            rating = "Excellent!"
        elif pct >= 70:
            rating = "Good!"
        elif pct >= 40:
            rating = "Average"
        else:
            rating = "Practice more"

        self.show_paragraph_result(self.para_full_correct, total, pct, points, elapsed,
                                    rating, timeout, self.para_total_points, self.para_max_points_total)

    def show_paragraph_result(self, full_correct, total, pct, points, elapsed, rating, timeout, total_points, max_points):
        self.clear_container()
        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        is_new_high = self.update_player_high(self.mode, self.score)

        title = "Time Khatam!" if timeout else "Paragraph Poora Hua!"
        tk.Label(wrap, text=title, font=FONT_TITLE, bg=self.C("BG"), fg=self.C("ACCENT")).pack(pady=(26, 8))
        if is_new_high:
            tk.Label(wrap, text="Naya High Score!", font=("Segoe UI", 16, "bold"),
                     bg=self.C("BG"), fg=self.C("YELLOW")).pack(pady=2)
        tk.Label(wrap, text=rating, font=("Segoe UI", 20, "bold"), bg=self.C("BG"), fg=self.C("GREEN")).pack(pady=4)
        tk.Label(wrap, text=f"{full_correct}/{total} shabd pura sahi   |   {total_points}/{max_points} letter-points ({pct}%)",
                 font=FONT_MAIN, bg=self.C("BG"), fg=self.C("FG")).pack(pady=4)
        tk.Label(wrap, text=f"Samay laga: {elapsed}s   |   Score mila: +{points}",
                 font=FONT_MAIN, bg=self.C("BG"), fg=self.C("YELLOW")).pack(pady=4)
        tk.Label(wrap, text=f"Best ({self.player_name}): {self.get_player_high(self.mode)}",
                 font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=(2, 4))

        btn_wrap = tk.Frame(wrap, bg=self.C("BG"))
        btn_wrap.pack(pady=20)
        self._btn(btn_wrap, "Naya Paragraph", lambda: self.start_game(self.para_direction)).pack(
            pady=6, ipadx=10, ipady=8, fill="x")
        self._btn(btn_wrap, "Analysis (isi game ka)", self.show_analysis).pack(
            pady=6, ipadx=10, ipady=8, fill="x")
        self._btn(btn_wrap, "History dekho (mera)", self.show_history).pack(
            pady=6, ipadx=10, ipady=8, fill="x")
        self._btn(btn_wrap, "Mode Badlo", self.show_start_screen).pack(
            pady=6, ipadx=10, ipady=8, fill="x")

    # =====================================================================
    # TYPING GAMES - SHARED HELPERS
    # =====================================================================
    def _typing_pair(self, word):
        code = "-".join(letter_to_code(c) for c in word)
        if self.typing_direction == "W2N":
            return word, code
        return code, word

    def _typing_common_setup(self, help_text, title):
        self.typing_start_time = time.time()
        self.typing_duration_seconds = self.typing_duration_min * 60
        self.typing_deadline = time.time() + self.typing_duration_seconds
        self.typing_canvas_w = 620
        self.typing_canvas_h = 380

        self.add_game_toolbar(help_text)

        top = tk.Frame(self.container, bg=self.C("BG"))
        top.pack(fill="x", pady=(8, 0), padx=20)
        tk.Label(top, text=title, font=FONT_MAIN, bg=self.C("BG"), fg=self.C("ACCENT")).pack(side="left")
        self.typing_score_lbl = tk.Label(top, text="Score: 0", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("GREEN"))
        self.typing_score_lbl.pack(side="left", padx=20)
        self.typing_lives_lbl = tk.Label(top, text="XXX", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("RED"))
        self.typing_lives_lbl.pack(side="right")
        self.typing_timer_lbl = tk.Label(top, text="", font=FONT_MAIN, bg=self.C("BG"), fg=self.C("YELLOW"))
        self.typing_timer_lbl.pack(side="right", padx=16)

        bar_wrap = tk.Frame(self.container, bg=self.C("BG_CARD"), height=10)
        bar_wrap.pack(fill="x", padx=20, pady=(10, 0))
        bar_wrap.pack_propagate(False)
        self.typing_bar = tk.Frame(bar_wrap, bg=self.C("ACCENT"), height=10)
        self.typing_bar.place(x=0, y=0, relheight=1, relwidth=1)

        self.typing_canvas = tk.Canvas(self.container, bg=self.C("BG_CARD"), highlightthickness=0, height=380)
        self.typing_canvas.pack(fill="both", expand=True, padx=20, pady=12)
        self.typing_canvas.bind("<Configure>", self._on_typing_canvas_resize)

        entry_row = tk.Frame(self.container, bg=self.C("BG"))
        entry_row.pack(fill="x", padx=40, pady=(0, 16))
        self.typing_answer_var = tk.StringVar()
        self.typing_entry = tk.Entry(entry_row, textvariable=self.typing_answer_var, font=("Segoe UI", 20),
                                      justify="center", bg=self.C("ENTRY_BG"), fg=self.C("FG"),
                                      insertbackground=self.C("FG"), relief="flat")
        self.typing_entry.pack(fill="x", ipady=8)
        self._safe_focus(self.typing_entry)

    def _on_typing_canvas_resize(self, event):
        if event.width > 10:
            self.typing_canvas_w = event.width
        if event.height > 10:
            self.typing_canvas_h = event.height

    def _update_typing_timer_ui(self, remaining_total):
        if remaining_total is None:
            return
        frac = max(0.0, remaining_total / self.typing_duration_seconds) if self.typing_duration_seconds else 0
        self.typing_bar.place(relwidth=frac)
        mins, secs = divmod(max(0, int(remaining_total)), 60)
        self.typing_timer_lbl.config(text=f"{mins}:{secs:02d}")
        if frac > 0.5:
            self.typing_bar.config(bg=self.C("ACCENT"))
        elif frac > 0.2:
            self.typing_bar.config(bg=self.C("YELLOW"))
        else:
            self.typing_bar.config(bg=self.C("RED"))

    def _update_typing_hud(self):
        self.typing_score_lbl.config(text=f"Score: {self.score}")
        self.typing_lives_lbl.config(text=self._lives_text())

    def _typing_remove_shapes(self, item):
        try:
            for sid in item["ids"]["body"]:
                self.typing_canvas.delete(sid)
            self.typing_canvas.delete(item["ids"]["text"])
        except Exception:
            pass

    def _typing_register_hit(self, item, given):
        self._typing_remove_shapes(item)
        if item in self.typing_items:
            self.typing_items.remove(item)
        if item.get("decoy"):
            self._safe_focus(self.typing_entry)
            return
        elapsed = round(time.time() - item.get("spawn_time", time.time()), 2)
        self.streak += 1
        bonus = self.streak // 5
        base_points = item.get("base_points")
        if base_points is None:
            base_points = len(item["word"]) if item.get("word") else 1
        pts = base_points + bonus
        self.score += pts
        q_type = "word" if self.typing_direction == "W2N" else "digit"
        wlen = len(item["word"]) if item.get("word") else 0
        pts_log = wlen if wlen > 1 else None
        self._log_history(q_type, item["display"], given, item["answer"], True, elapsed,
                           None, pts_log, pts_log)
        self._update_typing_hud()
        self._safe_focus(self.typing_entry)

    def _typing_register_miss(self, item):
        self._typing_remove_shapes(item)
        if item in self.typing_items:
            self.typing_items.remove(item)
        if item.get("decoy"):
            return
        self.mistakes += 1
        self.streak = 0
        q_type = "word" if self.typing_direction == "W2N" else "digit"
        wlen = len(item["word"]) if item.get("word") else 0
        pts_log = wlen if wlen > 1 else None
        self._log_history(q_type, item["display"], "(chuk gaya)", item["answer"], False, None,
                           None, 0 if pts_log else None, pts_log)
        self._update_typing_hud()

    def _typing_finish(self, timeout):
        if self.typing_anim_job:
            self.after_cancel(self.typing_anim_job)
            self.typing_anim_job = None
        if self.typing_spawn_job:
            self.after_cancel(self.typing_spawn_job)
            self.typing_spawn_job = None
        self.show_typing_result(timeout)

    def show_typing_result(self, timeout):
        self.clear_container()
        is_new_high = self.update_player_high(self.mode, self.score)

        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        reason = "Time Khatam!" if timeout else "Saari Jaanein Khatam!"
        tk.Label(wrap, text=reason, font=FONT_TITLE, bg=self.C("BG"), fg=self.C("RED")).pack(pady=(30, 6))
        if is_new_high:
            tk.Label(wrap, text="Naya High Score!", font=("Segoe UI", 16, "bold"),
                     bg=self.C("BG"), fg=self.C("YELLOW")).pack(pady=2)
        tk.Label(wrap, text=f"Final Score: {self.score}",
                 font=("Segoe UI", 24, "bold"), bg=self.C("BG"), fg=self.C("GREEN")).pack(pady=8)
        tk.Label(wrap, text=f"Best ({self.player_name}) - {MODE_LABELS.get(self.mode, self.mode)}: {self.get_player_high(self.mode)}",
                 font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=4)

        btn_wrap = tk.Frame(wrap, bg=self.C("BG"))
        btn_wrap.pack(pady=24)
        self._btn(btn_wrap, "Dobara Khelo", lambda: self.start_game(self.mode)).pack(
            pady=6, ipadx=10, ipady=10, fill="x")
        self._btn(btn_wrap, "Analysis (isi game ka)", self.show_analysis).pack(
            pady=6, ipadx=10, ipady=10, fill="x")
        self._btn(btn_wrap, "History dekho (mera)", self.show_history).pack(
            pady=6, ipadx=10, ipady=10, fill="x")
        self._btn(btn_wrap, "Mode Badlo", self.show_start_screen).pack(
            pady=6, ipadx=10, ipady=10, fill="x")

    # =====================================================================
    # CLOUD MASTER
    # =====================================================================
    def build_cloud_screen(self):
        self.clear_container()
        self.typing_items = []
        self._typing_common_setup(self._typing_help_text("CLOUD"), "Cloud Master")

        self.typing_entry.bind("<KeyRelease>", self.on_cloud_key_release)
        self.typing_entry.bind("<Return>", lambda e: self._submit_cloud())

        self._typing_tick_cloud()
        self._cloud_schedule_spawn()

    def _cloud_schedule_spawn(self):
        if self.paused:
            return
        if time.time() >= self.typing_deadline:
            return
        self._spawn_cloud_item()
        elapsed = time.time() - self.typing_start_time
        interval = max(1100, int(2800 - elapsed * 4))
        self.typing_spawn_job = self.after(interval, self._cloud_schedule_spawn)

    def _spawn_cloud_item(self):
        decoy = (random.random() < 0.15)
        if decoy:
            word, display, answer = None, "", None
        else:
            word = random.choice(TYPING_WORDS)
            display, answer = self._typing_pair(word)
        w = self.typing_canvas_w or 620
        x = random.randint(60, max(70, w - 60))
        tag = f"cloud{random.randint(0, 9999999)}"
        ids = self._draw_cloud_shape(x, -25, display, tag)
        item = {"word": word, "display": display, "answer": answer, "ids": ids, "x": x,
                "y": -25.0, "phase": random.random() * 6.28, "decoy": decoy,
                "spawn_time": time.time(), "tag": tag}
        self.typing_items.append(item)
        self.typing_canvas.tag_bind(tag, "<Button-1>", lambda e, t=tag: self._cloud_click_pop(t))

    def _draw_cloud_shape(self, x, y, text, tag):
        c = self.typing_canvas
        body = [
            c.create_oval(x - 42, y - 12, x - 6, y + 16, fill=self.C("BG_ROW"), outline="", tags=(tag,)),
            c.create_oval(x - 15, y - 22, x + 25, y + 12, fill=self.C("BG_ROW"), outline="", tags=(tag,)),
            c.create_oval(x + 6, y - 10, x + 44, y + 16, fill=self.C("BG_ROW"), outline="", tags=(tag,)),
        ]
        text_id = c.create_text(x, y + 2, text=text, fill=self.C("FG"), font=("Segoe UI", 11, "bold"), tags=(tag,))
        return {"body": body, "text": text_id}

    def _typing_tick_cloud(self):
        if self.paused:
            return
        remaining_total = None
        try:
            now = time.time()
            elapsed = now - self.typing_start_time
            remaining_total = self.typing_deadline - now
            self._update_typing_timer_ui(remaining_total)

            speed_mult = min(2.5, 1 + elapsed / 90)
            base_speed = 15
            dy = base_speed * speed_mult * (TICK_MS / 1000)
            canvas_h = self.typing_canvas_h or 380

            to_remove = []
            for item in list(self.typing_items):
                dx = math.sin(now * 2 + item["phase"]) * 0.5
                for sid in item["ids"]["body"]:
                    self.typing_canvas.move(sid, dx, dy)
                self.typing_canvas.move(item["ids"]["text"], dx, dy)
                item["y"] += dy
                if item["y"] > canvas_h:
                    to_remove.append(item)
            for item in to_remove:
                self._typing_register_miss(item)
        except Exception as e:
            print("Cloud tick error:", e)

        finished = (remaining_total is not None and remaining_total <= 0) or self.mistakes >= MAX_MISTAKES
        if finished:
            self._typing_finish(timeout=(remaining_total is not None and remaining_total <= 0))
            return
        self.typing_anim_job = self.after(TICK_MS, self._typing_tick_cloud)

    def on_cloud_key_release(self, event):
        if self.paused:
            return
        val = self.typing_answer_var.get()
        if val.endswith(" ") and val.strip():
            self._submit_cloud()

    def _submit_cloud(self):
        if self.paused:
            return
        val = self.typing_answer_var.get().strip()
        self.typing_answer_var.set("")
        if not val:
            return
        for item in list(self.typing_items):
            if not item.get("decoy") and item.get("answer") and val.upper() == item["answer"].upper():
                self._typing_register_hit(item, val)
                return

    def _cloud_click_pop(self, tag):
        for item in list(self.typing_items):
            if item.get("tag") == tag:
                if item.get("decoy"):
                    self._typing_register_miss(item)
                else:
                    self._typing_register_hit(item, "(tap)")
                return

    # =====================================================================
    # WORDTRIS  (ek time par sirf ek block)
    # =====================================================================
    def build_wordtris_screen(self):
        self.clear_container()
        self.wordtris_current = None
        self.wordtris_speed_mult = 1.0
        self._typing_common_setup(self._typing_help_text("BLOCKS"), "Wordtris")

        self.typing_entry.bind("<KeyRelease>", self.on_wordtris_key_release)
        self.typing_entry.bind("<Return>", lambda e: self._submit_wordtris())

        self._wordtris_spawn_next()
        self._typing_tick_wordtris()

    def _wordtris_spawn_next(self):
        if self.paused:
            return
        if time.time() >= self.typing_deadline or self.mistakes >= MAX_MISTAKES:
            return
        word = random.choice(TYPING_WORDS)
        display, answer = self._typing_pair(word)
        w = self.typing_canvas_w or 620
        x = w // 2
        tag = f"block{random.randint(0, 9999999)}"
        ids = self._draw_block_shape(x, -25, display, tag)
        self.wordtris_current = {"word": word, "display": display, "answer": answer, "ids": ids,
                                  "x": x, "y": -25.0, "tag": tag, "spawn_time": time.time(), "decoy": False}
        self.typing_canvas.tag_bind(tag, "<Button-1>", lambda e, t=tag: self._wordtris_click_pop(t))

    def _draw_block_shape(self, x, y, text, tag):
        c = self.typing_canvas
        pad = max(34, 7 * len(str(text)))
        rect = c.create_rectangle(x - pad, y - 18, x + pad, y + 18, fill=self.C("PURPLE"), outline="", tags=(tag,))
        txt = c.create_text(x, y, text=text, fill="#0a0a0a", font=("Segoe UI", 12, "bold"), tags=(tag,))
        return {"body": [rect], "text": txt}

    def _typing_tick_wordtris(self):
        if self.paused:
            return
        remaining_total = None
        try:
            now = time.time()
            elapsed = now - self.typing_start_time
            remaining_total = self.typing_deadline - now
            self._update_typing_timer_ui(remaining_total)

            base_speed = 13
            speed_mult = min(2.5, self.wordtris_speed_mult * (1 + elapsed / 120))
            dy = base_speed * speed_mult * (TICK_MS / 1000)
            canvas_h = self.typing_canvas_h or 380

            item = self.wordtris_current
            if item is not None:
                self.typing_canvas.move(item["ids"]["body"][0], 0, dy)
                self.typing_canvas.move(item["ids"]["text"], 0, dy)
                item["y"] += dy
                if item["y"] > canvas_h:
                    self._wordtris_handle_miss(item)
        except Exception as e:
            print("Wordtris tick error:", e)

        finished = (remaining_total is not None and remaining_total <= 0) or self.mistakes >= MAX_MISTAKES
        if finished:
            self._typing_finish(timeout=(remaining_total is not None and remaining_total <= 0))
            return
        self.typing_anim_job = self.after(TICK_MS, self._typing_tick_wordtris)

    def _wordtris_handle_miss(self, item):
        self._typing_register_miss(item)
        self.wordtris_speed_mult = max(0.6, self.wordtris_speed_mult * 0.85)
        self.wordtris_current = None
        self._wordtris_spawn_next()

    def _wordtris_handle_hit(self, item, given):
        self._typing_register_hit(item, given)
        self.wordtris_speed_mult = min(2.5, self.wordtris_speed_mult * 1.05)
        self.wordtris_current = None
        self._wordtris_spawn_next()

    def on_wordtris_key_release(self, event):
        if self.paused:
            return
        val = self.typing_answer_var.get()
        if val.endswith(" ") and val.strip():
            self._submit_wordtris()

    def _submit_wordtris(self):
        if self.paused:
            return
        val = self.typing_answer_var.get().strip()
        self.typing_answer_var.set("")
        if not val:
            return
        item = self.wordtris_current
        if item and val.upper() == item["answer"].upper():
            self._wordtris_handle_hit(item, val)

    def _wordtris_click_pop(self, tag):
        item = self.wordtris_current
        if item and item.get("tag") == tag:
            self._wordtris_handle_hit(item, "(tap)")

    # =====================================================================
    # BUBBLE POP  (single letter/digit, jaisa L2N/N2L)
    # =====================================================================
    def build_bubbles_screen(self):
        self.clear_container()
        self.typing_items = []
        self._typing_common_setup(self._typing_help_text("BUBBLES"), "Bubble Pop")

        self.typing_entry.bind("<KeyRelease>", self.on_bubble_key_release)
        self.typing_entry.bind("<Return>", lambda e: self._try_match_bubble())

        self._typing_tick_bubbles()
        self._bubbles_schedule_spawn()

    def _bubbles_schedule_spawn(self):
        if self.paused:
            return
        if time.time() >= self.typing_deadline:
            return
        self._spawn_bubble()
        elapsed = time.time() - self.typing_start_time
        interval = max(1300, int(3200 - elapsed * 4))
        self.typing_spawn_job = self.after(interval, self._bubbles_schedule_spawn)

    def _spawn_bubble(self):
        n = random.randint(1, 26)
        letter = chr(64 + n) if random.random() < 0.5 else chr(96 + n)
        if self.typing_direction == "W2N":
            display, answer = letter, str(n)
        else:
            display, answer = str(n), chr(64 + n)
        w = self.typing_canvas_w or 620
        h = self.typing_canvas_h or 380
        radius = 34
        x = random.randint(60 + radius, max(70 + radius, w - 60 - radius))
        y = random.randint(50 + radius, max(70 + radius, h - 50 - radius))
        tag = f"bubble{random.randint(0, 9999999)}"
        ids = self._draw_bubble_shape(x, y, radius, display, tag)
        elapsed = time.time() - self.typing_start_time
        lifespan = max(5.0, 9.0 - elapsed / 60)
        item = {"word": letter, "display": display, "answer": answer, "ids": ids, "x": x, "y": y,
                "radius": radius, "born_time": time.time(), "lifespan": lifespan, "tag": tag,
                "decoy": False, "base_points": 4}
        self.typing_items.append(item)
        self.typing_canvas.tag_bind(tag, "<Button-1>", lambda e, t=tag: self._bubble_click_pop(t))

    def _draw_bubble_shape(self, x, y, r, text, tag):
        c = self.typing_canvas
        oval = c.create_oval(x - r, y - r, x + r, y + r, fill=self.C("ACCENT"), outline="", tags=(tag,))
        txt = c.create_text(x, y, text=text, fill="#ffffff", font=("Segoe UI", 14, "bold"), tags=(tag,))
        return {"body": [oval], "text": txt}

    def _typing_tick_bubbles(self):
        if self.paused:
            return
        remaining_total = None
        try:
            now = time.time()
            remaining_total = self.typing_deadline - now
            self._update_typing_timer_ui(remaining_total)

            to_remove = []
            for item in list(self.typing_items):
                dy = math.sin(now * 3 + item["x"]) * 0.3
                for sid in item["ids"]["body"]:
                    self.typing_canvas.move(sid, 0, dy)
                self.typing_canvas.move(item["ids"]["text"], 0, dy)
                if now - item["born_time"] >= item["lifespan"]:
                    to_remove.append(item)
            for item in to_remove:
                self._typing_register_miss(item)
        except Exception as e:
            print("Bubble tick error:", e)

        finished = (remaining_total is not None and remaining_total <= 0) or self.mistakes >= MAX_MISTAKES
        if finished:
            self._typing_finish(timeout=(remaining_total is not None and remaining_total <= 0))
            return
        self.typing_anim_job = self.after(TICK_MS, self._typing_tick_bubbles)

    def on_bubble_key_release(self, event):
        if self.paused:
            return
        self._try_match_bubble()

    def _try_match_bubble(self):
        val = self.typing_answer_var.get().strip()
        if not val:
            return
        for item in list(self.typing_items):
            if val.upper() == item["answer"].upper():
                self.typing_answer_var.set("")
                self._typing_register_hit(item, val)
                return

    def _bubble_click_pop(self, tag):
        for item in list(self.typing_items):
            if item.get("tag") == tag:
                self._typing_register_hit(item, "(tap)")
                return

    # =====================================================================
    # GAME OVER (mode 1 & 2 & MCQ)
    # =====================================================================
    def show_game_over(self):
        self.clear_container()
        is_new_high = self.update_player_high(self.mode, self.score)

        wrap = tk.Frame(self.container, bg=self.C("BG"))
        wrap.pack(expand=True)

        tk.Label(wrap, text="Game Over", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("RED")).pack(pady=(30, 6))
        if is_new_high:
            tk.Label(wrap, text="Naya High Score!", font=("Segoe UI", 16, "bold"),
                     bg=self.C("BG"), fg=self.C("YELLOW")).pack(pady=2)
        tk.Label(wrap, text=f"Final Score: {self.score}",
                 font=("Segoe UI", 24, "bold"), bg=self.C("BG"), fg=self.C("GREEN")).pack(pady=8)
        tk.Label(wrap, text=f"Pahuncha: Level {self.level_number()}   |   Best: {self.get_player_high(self.mode)}",
                 font=FONT_SMALL, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(pady=4)

        btn_wrap = tk.Frame(wrap, bg=self.C("BG"))
        btn_wrap.pack(pady=24)

        self._btn(btn_wrap, "Dobara Khelo (Same Mode)", lambda: self.start_game(self.mode)).pack(
            pady=6, ipadx=10, ipady=10, fill="x")
        self._btn(btn_wrap, "Analysis (isi game ka)", self.show_analysis).pack(
            pady=6, ipadx=10, ipady=10, fill="x")
        self._btn(btn_wrap, "History dekho (mera)", self.show_history).pack(
            pady=6, ipadx=10, ipady=10, fill="x")
        self._btn(btn_wrap, "Mode Badlo", self.show_start_screen).pack(
            pady=6, ipadx=10, ipady=10, fill="x")

    # =====================================================================
    # SPEED RATING helper (History & Analysis ke liye)
    # =====================================================================
    def _speed_rating(self, entry):
        if not entry["correct"]:
            return "Improve karo", self.C("RED")
        if entry["time"] is None:
            return "Theek", self.C("YELLOW")
        if entry["limit"]:
            baseline = entry["limit"]
        else:
            wlen = entry.get("max_points") or 5
            baseline = max(2.0, wlen * 1.3)
        frac = entry["time"] / baseline
        if frac <= 0.4:
            return "Achha", self.C("GREEN")
        elif frac <= 0.85:
            return "Theek", self.C("YELLOW")
        else:
            return "Improve karo", self.C("RED")

    # =====================================================================
    # SCROLLABLE ROW LIST (History & Analysis dono ke liye)
    # =====================================================================
    def _build_scroll_list(self, parent, entries, show_rating):
        list_wrap = tk.Frame(parent, bg=self.C("BG"))
        list_wrap.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        canvas = tk.Canvas(list_wrap, bg=self.C("BG"), highlightthickness=0)
        scrollbar = tk.Scrollbar(list_wrap, orient="vertical", command=canvas.yview)
        rows_frame = tk.Frame(canvas, bg=self.C("BG"))

        rows_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=rows_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        for h in reversed(entries):
            row = tk.Frame(rows_frame, bg=self.C("BG_ROW"))
            row.pack(fill="x", pady=3)

            status_color = self.C("GREEN") if h["correct"] else self.C("RED")
            status_icon = "OK" if h["correct"] else "X"
            q_tag = {"letter": "L", "digit": "N", "word": "W"}.get(h.get("q_type"), "")

            left = tk.Label(row, text=f"#{h['serial']} {status_icon} {MODE_ICONS.get(h['mode'], '')} {q_tag} {h['question']}",
                             font=FONT_SMALL, bg=self.C("BG_ROW"), fg=status_color, anchor="w", width=32)
            left.pack(side="left", padx=8, pady=6)

            pts_txt = f"  ({h['points']}/{h['max_points']} pts)" if h.get("max_points") else ""
            mid = tk.Label(row, text=f"Tumne: {h['given']}   Sahi: {h['correct_answer']}{pts_txt}",
                            font=FONT_SMALL, bg=self.C("BG_ROW"), fg=self.C("FG_MUTED"), anchor="w")
            mid.pack(side="left", padx=8, pady=6, fill="x", expand=True)

            time_txt = f"{h['time']}s" if h["time"] is not None else "-"
            if show_rating:
                rating_txt, rating_color = self._speed_rating(h)
                combined = f"{time_txt}  {rating_txt}"
                tk.Label(row, text=combined, font=FONT_SMALL, bg=self.C("BG_ROW"),
                         fg=rating_color, width=20).pack(side="right", padx=8, pady=6)
            else:
                tk.Label(row, text=time_txt, font=FONT_SMALL, bg=self.C("BG_ROW"),
                         fg=self.C("YELLOW"), width=8).pack(side="right", padx=8, pady=6)

    # =====================================================================
    # HISTORY SCREEN (sirf current player, sab games)
    # =====================================================================
    def show_history(self):
        self.clear_container()

        header = tk.Frame(self.container, bg=self.C("BG"))
        header.pack(fill="x", padx=16, pady=(16, 6))
        tk.Label(header, text=f"History - {self.player_name}", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(side="left")
        tk.Button(header, text="Wapas", font=FONT_SMALL, command=self.show_start_screen,
                  bg=self.C("BG_CARD"), fg=self.C("FG"), relief="flat", cursor="hand2", bd=0).pack(
            side="right", ipadx=8, ipady=4)

        entries = [h for h in self.history if h.get("player") == self.player_name]
        if not entries:
            tk.Label(self.container, text="Abhi tak koi history nahi hai.\nPehle koi game khelo!",
                     font=FONT_MAIN, bg=self.C("BG"), fg=self.C("FG_MUTED"), justify="center").pack(expand=True)
            return

        correct_n = sum(1 for h in entries if h["correct"])
        total_n = len(entries)
        timed = [h["time"] for h in entries if h["time"] is not None]
        avg_time = round(sum(timed) / len(timed), 2) if timed else 0

        stats = tk.Frame(self.container, bg=self.C("BG_CARD"))
        stats.pack(fill="x", padx=16, pady=(4, 10))
        tk.Label(stats, text=f"Sahi: {correct_n}/{total_n}   |   Average time: {avg_time}s",
                 font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED")).pack(pady=8)

        self._build_scroll_list(self.container, entries, show_rating=False)

    # =====================================================================
    # ANALYSIS SCREEN (sirf abhi khatam hua game)
    # =====================================================================
    
    def show_analysis(self):
        self.clear_container()

        header = tk.Frame(self.container, bg=self.C("BG"))
        header.pack(fill="x", padx=16, pady=(16, 6))
        tk.Label(header, text="Analysis (Is Game Ka)", font=FONT_TITLE, bg=self.C("BG"), fg=self.C("FG")).pack(side="left")
        tk.Button(header, text="Wapas", font=FONT_SMALL, command=self.show_start_screen,
                  bg=self.C("BG_CARD"), fg=self.C("FG"), relief="flat", cursor="hand2", bd=0).pack(
            side="right", ipadx=8, ipady=4)

        entries = [h for h in self.history if h["session"] == self.session_id]
        if not entries:
            tk.Label(self.container, text="Is game ke liye koi data nahi mila.",
                     font=FONT_MAIN, bg=self.C("BG"), fg=self.C("FG_MUTED")).pack(expand=True)
            return

        correct_n = sum(1 for h in entries if h["correct"])
        total_n = len(entries)
        timed = [h["time"] for h in entries if h["time"] is not None]
        avg_time = round(sum(timed) / len(timed), 2) if timed else None

        good = sum(1 for h in entries if self._speed_rating(h)[0] == "Achha")
        ok = sum(1 for h in entries if self._speed_rating(h)[0] == "Theek")
        bad = sum(1 for h in entries if self._speed_rating(h)[0] == "Improve karo")

        stats = tk.Frame(self.container, bg=self.C("BG_CARD"))
        stats.pack(fill="x", padx=16, pady=(4, 10))
        line1 = f"Sahi: {correct_n}/{total_n}"
        if avg_time is not None:
            line1 += f"   |   Average time: {avg_time}s"
        tk.Label(stats, text=line1, font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED")).pack(pady=(8, 2))
        tk.Label(stats, text=f"Achha: {good}   Theek: {ok}   Improve karo: {bad}",
                 font=FONT_SMALL, bg=self.C("BG_CARD"), fg=self.C("FG_MUTED")).pack(pady=(0, 8))

        self._build_scroll_list(self.container, entries, show_rating=True)


if __name__ == "__main__":
    app = LetterNumberGame()
    app.mainloop()