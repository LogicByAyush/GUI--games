import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import random
import string
import codecs
import threading
import queue
import time
import os
import array

# ---- Optional sound support -------------------------------------------------
try:
    import pygame
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False

# =============================================================================
#  THEMES
# =============================================================================

THEMES = {
    "Matrix": {
        "bg_dark": "#0b0f14", "bg_panel": "#111820", "fg_primary": "#39ff14",
        "fg_accent": "#38f5ff", "fg_warning": "#f5f542", "fg_danger": "#ff3b3b",
        "term_bg": "#000000",
    },
    "Cyberpunk": {
        "bg_dark": "#0d0221", "bg_panel": "#1a0b2e", "fg_primary": "#ff2bd6",
        "fg_accent": "#05d9e8", "fg_warning": "#f9f871", "fg_danger": "#ff3864",
        "term_bg": "#05010f",
    },
    "Blood Red": {
        "bg_dark": "#120000", "bg_panel": "#210000", "fg_primary": "#ff2020",
        "fg_accent": "#ff8b3d", "fg_warning": "#ffcc00", "fg_danger": "#ff5050",
        "term_bg": "#000000",
    },
    "Ice Blue": {
        "bg_dark": "#01111d", "bg_panel": "#02233b", "fg_primary": "#7fe3ff",
        "fg_accent": "#ffffff", "fg_warning": "#ffd166", "fg_danger": "#ff6b6b",
        "term_bg": "#000814",
    },
}
THEME = dict(THEMES["Matrix"])  # mutable "current theme" - mutated in place


def set_theme(name):
    if name in THEMES:
        THEME.update(THEMES[name])


FONT_MONO = ("Consolas", 12)
FONT_MONO_SMALL = ("Consolas", 10)
FONT_MONO_BIG = ("Consolas", 17, "bold")
FONT_TITLE = ("Consolas", 26, "bold")

DB_PATH = "leaderboard.db"
SAVE_PATH = "save.json"
SETTINGS_PATH = "settings.json"
ACHIEVEMENTS_PATH = "achievements.json"

# Rooms now scaled up for the longer 25-room run
DIFFICULTY_SETTINGS = {
    "Easy":      {"health": 9, "time": 900, "ai_interval": (30, 45), "hint_cost": 12},
    "Medium":    {"health": 7, "time": 720, "ai_interval": (22, 34), "hint_cost": 20},
    "Hard":      {"health": 5, "time": 600, "ai_interval": (15, 26), "hint_cost": 30},
    "Nightmare": {"health": 4, "time": 480, "ai_interval": (9, 18),  "hint_cost": 45},
}

# How much time is refunded to the player for clearing a room (keeps the
# clock from running out just because an early puzzle took a while).
ROOM_CLEAR_TIME_BONUS = {"Easy": 20, "Medium": 16, "Hard": 12, "Nightmare": 8}

# Cost multiplier for the "Answer Key" (skip-room) feature, relative to
# the normal hint cost for the chosen difficulty.
ANSWER_KEY_COST_MULTIPLIER = 2.5

WORD_BANK = ["FIREWALL", "SERVER", "ROOTKIT", "BACKDOOR", "ENCRYPT",
             "BINARY", "PROTOCOL", "MAINFRAME", "KERNEL", "GATEWAY",
             "PACKET", "PAYLOAD", "TROJAN", "CIPHER", "NETWORK",
             "SHELL", "PROXY", "SANDBOX", "MALWARE", "SPOOF"]

SHORT_WORD_BANK = ["HI", "OK", "GO", "YES", "RUN", "BYE", "BOT", "KEY", "LOG", "BUG"]

MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
}
REVERSE_MORSE = {v: k for k, v in MORSE_CODE_DICT.items()}

# 23 flavourful lab locations + Boss + Final
ROOM_LOCATIONS = [
    "Firewall Breach", "Data Vault", "Proxy Tunnel", "Cooling Core",
    "Backup Array", "Auth Gateway", "Log Archive", "Router Nexus",
    "Cache Chamber", "Cloud Node", "Packet Bay", "Kernel Hall",
    "Socket Room", "DNS Spire", "VPN Corridor", "Load Balancer",
    "Sandbox Lab", "Honeypot Den", "Bastion Wing", "Cipher Vault",
    "Relay Station", "Mirror Array", "Quarantine Zone",
]

# ---------------------------------------------------------------------------
# DIFFICULTY CURVE: puzzle types are grouped into EASY -> MEDIUM -> HARD
# tiers so the game gently ramps up instead of throwing something tough
# at Room 1. Sudoku/Memory (the fiddlier ones) only show up later.
# ---------------------------------------------------------------------------
PUZZLE_TIER_EASY = ["pattern", "scramble", "rot13", "math"]
PUZZLE_TIER_MEDIUM = ["caesar", "binary", "hex", "sudoku"]
PUZZLE_TIER_HARD = ["morse", "memory"]


def _build_puzzle_cycle(total_slots):
    """Builds a tier-ordered puzzle cycle: easy types first (x2), then
    medium types (x2), then hard types filling out the rest. This keeps
    early rooms approachable and difficulty rising gradually."""
    cycle = list(PUZZLE_TIER_EASY) * 2
    cycle += list(PUZZLE_TIER_MEDIUM) * 2
    i = 0
    while len(cycle) < total_slots:
        cycle.append(PUZZLE_TIER_HARD[i % len(PUZZLE_TIER_HARD)])
        i += 1
    return cycle[:total_slots]


PUZZLE_TYPE_CYCLE = _build_puzzle_cycle(len(ROOM_LOCATIONS))

ROOMS = []
for i, loc in enumerate(ROOM_LOCATIONS):
    ptype = PUZZLE_TYPE_CYCLE[i]
    ROOMS.append({"name": f"Room {i + 1} - {loc}", "type": ptype})
ROOMS.append({"name": "Room 24 - AI Boss Fight", "type": "boss"})
ROOMS.append({"name": "Room 25 - Main Server / Escape", "type": "final"})

ITEM_POOL = ["USB_DRIVE", "MASTER_KEY", "SHIELD_MODULE"]
ITEM_DESCRIPTIONS = {
    "USB_DRIVE": "Instantly auto-solves the CURRENT room's puzzle.",
    "MASTER_KEY": "Instantly clears any AI door-lock and blocks the next one.",
    "SHIELD_MODULE": "Blocks the next wrong-answer heart loss.",
}

ACHIEVEMENT_DEFS = {
    "no_damage": "Ghost Protocol - Escape without losing a single heart",
    "speed_runner": "Speed Runner - Escape with over half the timer remaining",
    "hint_free": "Self Made - Escape without buying a single hint",
    "boss_slayer": "Boss Slayer - Defeat the AI Security Boss",
    "perfect_escape": "Perfect Escape - Ghost Protocol + Self Made + Boss Slayer",
    "coin_collector": "Coin Collector - Hold 300+ coins at once",
}


# =============================================================================
#  PUZZLE / CRYPTO HELPERS
# =============================================================================
class PuzzleGenerator:
    """All puzzle-related static helpers live here (OOP: puzzle factory)."""

    @staticmethod
    def rot13(text):
        return codecs.encode(text, "rot_13")

    @staticmethod
    def caesar_encrypt(text, shift):
        out = []
        for ch in text:
            if ch.isalpha():
                base = 65 if ch.isupper() else 97
                out.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                out.append(ch)
        return "".join(out)

    @staticmethod
    def caesar_decrypt(text, shift):
        return PuzzleGenerator.caesar_encrypt(text, -shift)

    @staticmethod
    def to_binary(text):
        return " ".join(format(ord(c), "08b") for c in text)

    @staticmethod
    def to_morse(text):
        return " ".join(MORSE_CODE_DICT[c] for c in text if c in MORSE_CODE_DICT)

    @staticmethod
    def from_morse(code):
        return "".join(REVERSE_MORSE.get(c, "") for c in code.split())

    @staticmethod
    def to_hex(text):
        return " ".join(format(ord(c), "02x") for c in text)

    @staticmethod
    def scramble(word):
        letters = list(word)
        scrambled = word
        tries = 0
        while scrambled == word and tries < 20:
            random.shuffle(letters)
            scrambled = "".join(letters)
            tries += 1
        return scrambled

    # ---- puzzle factories (return word/answer + encoded/display text [+extra]) ----
    @staticmethod
    def make_rot13_puzzle():
        word = random.choice(WORD_BANK)
        return word, PuzzleGenerator.rot13(word)

    @staticmethod
    def make_caesar_puzzle(shift=None):
        if shift is None:
            shift = random.randint(2, 9)
        word = random.choice(WORD_BANK)
        return word, PuzzleGenerator.caesar_encrypt(word, shift), shift

    @staticmethod
    def make_binary_puzzle():
        word = random.choice(SHORT_WORD_BANK)
        return word, PuzzleGenerator.to_binary(word)

    @staticmethod
    def make_morse_puzzle():
        word = random.choice(SHORT_WORD_BANK)
        return word, PuzzleGenerator.to_morse(word)

    @staticmethod
    def make_hex_puzzle():
        word = random.choice(SHORT_WORD_BANK)
        return word, PuzzleGenerator.to_hex(word)

    @staticmethod
    def make_scramble_puzzle():
        word = random.choice(WORD_BANK)
        return word, PuzzleGenerator.scramble(word)

    @staticmethod
    def make_math_puzzle():
        kind = random.choice(["arith", "geo", "square"])
        if kind == "arith":
            start = random.randint(1, 10)
            diff = random.randint(2, 9)
            seq = [start + diff * i for i in range(4)]
            answer = start + diff * 4
        elif kind == "geo":
            start = random.randint(1, 4)
            ratio = random.choice([2, 3])
            seq = [start * (ratio ** i) for i in range(4)]
            answer = start * (ratio ** 4)
        else:
            start = random.randint(1, 5)
            seq = [(start + i) ** 2 for i in range(4)]
            answer = (start + 4) ** 2
        return seq, str(answer)

    @staticmethod
    def make_pattern_puzzle():
        symbols = ["STAR", "MOON", "SUN", "BOLT"]
        cycle = random.sample(symbols, len(symbols))
        length = random.choice([6, 8])
        seq = [cycle[i % len(cycle)] for i in range(length)]
        answer = cycle[length % len(cycle)]
        return seq, answer

    # ---- 4x4 Sudoku ----
    _BASE_SOLUTION = [
        [1, 2, 3, 4],
        [3, 4, 1, 2],
        [2, 1, 4, 3],
        [4, 3, 2, 1],
    ]

    @staticmethod
    def generate_sudoku4(blanks=6):
        perm = list(range(1, 5))
        random.shuffle(perm)
        mapping = {i + 1: perm[i] for i in range(4)}
        sol = [[mapping[v] for v in row] for row in PuzzleGenerator._BASE_SOLUTION]

        bands = [[0, 1], [2, 3]]
        for band in bands:
            random.shuffle(band)
        row_order = bands[0] + bands[1]
        sol = [sol[r] for r in row_order]

        stacks = [[0, 1], [2, 3]]
        for s in stacks:
            random.shuffle(s)
        col_order = stacks[0] + stacks[1]
        sol = [[row[c] for c in col_order] for row in sol]

        puzzle = [row[:] for row in sol]
        cells = [(r, c) for r in range(4) for c in range(4)]
        random.shuffle(cells)
        for i in range(min(blanks, 15)):
            r, c = cells[i]
            puzzle[r][c] = 0
        return puzzle, sol

    @staticmethod
    def generate_memory_sequence(length=4):
        colors = ["#ff4d4d", "#4dff88", "#4d9dff", "#ffe14d"]
        return [random.choice(colors) for _ in range(length)], colors

    @staticmethod
    def generate_password(length=5):
        return "".join(random.choice(string.ascii_uppercase) for _ in range(length))

    # ---- LEGEND / REFERENCE TABLES ------------------------------------
    # These exist so a puzzle is never a mystery: the player can always
    # open a legend and see exactly how the encoding works, with a
    # worked example, instead of guessing.

    @staticmethod
    def legend_rot13():
        pairs = [f"{c}<->{PuzzleGenerator.rot13(c)}" for c in string.ascii_uppercase[:13]]
        return (
            "ROT13 REFERENCE\n"
            "----------------\n"
            "Every letter is shifted 13 places through the alphabet\n"
            "(and shifting again by 13 brings it back - that's why it's\n"
            "symmetric: A<->N, B<->O, etc).\n\n"
            + "   ".join(pairs) +
            "\n\nWorked example: 'HELLO' -> rot13 -> 'URYYB'\n"
            "So if you see 'URYYB', the answer is 'HELLO'."
        )

    @staticmethod
    def legend_caesar(shift):
        example_word = "HELLO"
        example_enc = PuzzleGenerator.caesar_encrypt(example_word, shift)
        return (
            f"CAESAR CIPHER REFERENCE (shift = {shift})\n"
            "-----------------------------------\n"
            f"Every letter in the answer was moved FORWARD by {shift}\n"
            f"places to create the puzzle text. To solve it, move each\n"
            f"letter in the puzzle BACKWARD by {shift} places.\n\n"
            f"Worked example with this shift: '{example_word}' encrypts to\n"
            f"'{example_enc}'. So if you saw '{example_enc}', decoding it\n"
            f"(shift back {shift}) gives you '{example_word}'."
        )

    @staticmethod
    def legend_binary():
        sample = "HI"
        enc = PuzzleGenerator.to_binary(sample)
        table = "  ".join(f"{c}={format(ord(c), '08b')}" for c in "ABCDEFGHIJ")
        return (
            "BINARY (8-BIT ASCII) REFERENCE\n"
            "-------------------------------\n"
            "Each group of 8 bits (0s and 1s) is ONE letter. Convert each\n"
            "8-bit group to a decimal number, then to its ASCII letter.\n\n"
            f"Sample letters: {table}\n\n"
            f"Worked example: '{sample}' -> '{enc}'\n"
            f"So '{enc}' decodes back to '{sample}'."
        )

    @staticmethod
    def legend_hex():
        sample = "HI"
        enc = PuzzleGenerator.to_hex(sample)
        table = "  ".join(f"{c}={format(ord(c), '02x')}" for c in "ABCDEFGHIJ")
        return (
            "HEXADECIMAL REFERENCE\n"
            "----------------------\n"
            "Each pair of hex digits is ONE letter's ASCII code in base 16.\n\n"
            f"Sample letters: {table}\n\n"
            f"Worked example: '{sample}' -> '{enc}'\n"
            f"So '{enc}' decodes back to '{sample}'."
        )

    @staticmethod
    def legend_morse():
        table_lines = []
        letters = list(MORSE_CODE_DICT.items())
        for i in range(0, len(letters), 6):
            chunk = letters[i:i + 6]
            table_lines.append("   ".join(f"{k}={v}" for k, v in chunk))
        sample = "HI"
        enc = PuzzleGenerator.to_morse(sample)
        return (
            "MORSE CODE REFERENCE\n"
            "---------------------\n"
            "'.' = a short dot, '-' = a long dash. Each letter's code is\n"
            "separated by a space in the puzzle.\n\n"
            + "\n".join(table_lines) +
            f"\n\nWorked example: '{sample}' -> '{enc}'\n"
            f"So '{enc}' decodes back to '{sample}'."
        )

    @staticmethod
    def legend_generic(kind):
        mapping = {
            "scramble": (
                "WORD SCRAMBLE REFERENCE\n------------------------\n"
                "All the letters of a real hacking-related word have been\n"
                "shuffled into a random order. Rearrange them to spell the\n"
                "original word (e.g. 'RESERV' -> 'SERVER')."
            ),
            "math": (
                "LOGIC SEQUENCE REFERENCE\n--------------------------\n"
                "You're shown 4 numbers that follow ONE of these patterns:\n"
                "  - Arithmetic: same amount added each time (2,5,8,11 -> +3 each -> next 14)\n"
                "  - Geometric: multiplied by the same amount each time (2,4,8,16 -> x2 -> next 32)\n"
                "  - Squares: consecutive numbers squared (1,4,9,16 -> next is 25)\n"
                "Work out the pattern and type the NEXT number."
            ),
            "pattern": (
                "SYMBOL PATTERN REFERENCE\n--------------------------\n"
                "The 4 symbols STAR, MOON, SUN, BOLT repeat in a fixed cycle,\n"
                "e.g. STAR -> MOON -> SUN -> BOLT -> STAR -> MOON ...\n"
                "Figure out the repeating cycle and type the NEXT symbol\n"
                "in the sequence shown (type it exactly, e.g. MOON)."
            ),
            "sudoku": (
                "4x4 SUDOKU REFERENCE\n----------------------\n"
                "Fill every empty cell with a digit 1-4 so that:\n"
                "  - each ROW contains 1,2,3,4 exactly once\n"
                "  - each COLUMN contains 1,2,3,4 exactly once\n"
                "  - each 2x2 BOX contains 1,2,3,4 exactly once\n"
                "Once the grid is correct, submit the TOP ROW's 4 digits\n"
                "(read left to right, no spaces, e.g. 2413) as the password."
            ),
            "memory": (
                "MEMORY SEQUENCE REFERENCE\n---------------------------\n"
                "Click 'SHOW SEQUENCE' to watch the colours flash in order.\n"
                "Then click the 4 coloured squares in that EXACT same order.\n"
                "Get it right and the password box will auto-fill 'DONE' -\n"
                "just hit Submit."
            ),
            "boss": (
                "AI BOSS FIGHT REFERENCE\n-------------------------\n"
                "Each round shows one coded word (ROT13 / Binary / Caesar /\n"
                "Morse / Hex - the round tells you which). Decode it and\n"
                "submit it as the password to land a hit on the boss.\n"
                "A WRONG answer hits YOU instead (lose a heart). Repeat\n"
                "until the boss's health bar reaches zero."
            ),
        }
        return mapping.get(kind, "No extra reference available for this puzzle type.")


# =============================================================================
#  DATABASE (SQLite leaderboard)
# =============================================================================
class LeaderboardDB:
    def __init__(self, path=DB_PATH):
        self.path = path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, time_taken INTEGER, score INTEGER,
                difficulty TEXT, date TEXT
            )
        """)
        conn.commit()
        conn.close()

    def add_score(self, name, time_taken, score, difficulty):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO leaderboard (name, time_taken, score, difficulty, date) VALUES (?,?,?,?,?)",
            (name, time_taken, score, difficulty, time.strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
        conn.close()

    def get_top(self, limit=10):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute(
            "SELECT name, time_taken, score, difficulty, date FROM leaderboard "
            "ORDER BY score DESC, time_taken ASC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return rows


# =============================================================================
#  SAVE / LOAD (JSON)
# =============================================================================
class SaveManager:
    @staticmethod
    def save(player, path=SAVE_PATH):
        data = {
            "name": player.name, "difficulty": player.difficulty,
            "health": player.health, "max_health": player.max_health,
            "coins": player.coins, "time_left": player.time_left,
            "room_index": player.current_room_index, "inventory": player.inventory,
            "score": player.score, "hints_used": player.hints_used,
            "hearts_lost": player.hearts_lost, "boss_defeated": player.boss_defeated,
            "key_used": player.key_used,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(path=SAVE_PATH):
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return json.load(f)


class SettingsManager:
    DEFAULTS = {"sound_on": True, "music_on": True, "theme": "Matrix",
                "fullscreen": False, "intro_on": True}

    def __init__(self, path=SETTINGS_PATH):
        self.path = path
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    loaded = json.load(f)
                self.data.update(loaded)
            except Exception:
                pass

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)


class AchievementManager:
    def __init__(self, path=ACHIEVEMENTS_PATH):
        self.path = path
        self.unlocked = set()
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self.unlocked = set(json.load(f))
            except Exception:
                self.unlocked = set()

    def save(self):
        with open(self.path, "w") as f:
            json.dump(sorted(self.unlocked), f, indent=2)

    def unlock(self, key):
        """Returns True if this was newly unlocked."""
        if key not in self.unlocked:
            self.unlocked.add(key)
            return True
        return False


# =============================================================================
#  PLAYER (OOP model)
# =============================================================================
class Player:
    def __init__(self, name, difficulty):
        self.name = name
        self.difficulty = difficulty
        settings = DIFFICULTY_SETTINGS[difficulty]
        self.max_health = settings["health"]
        self.health = self.max_health
        self.coins = 100
        self.time_left = settings["time"]
        self.total_time = settings["time"]
        self.inventory = []
        self.current_room_index = 0
        self.score = 0
        self.hints_used = 0
        self.hearts_lost = 0
        self.boss_defeated = False
        self.shield_active = False
        # True the moment the player ever uses the Answer Key. Rooms
        # skipped this way give NO coins/score and this flag blocks
        # achievements, so it never overtakes genuine play.
        self.key_used = False

    def lose_heart(self, n=1):
        if self.shield_active:
            self.shield_active = False
            return False
        self.health = max(0, self.health - n)
        self.hearts_lost += n
        return self.health <= 0

    def add_coins(self, n):
        self.coins += n

    def spend_coins(self, n):
        if self.coins >= n:
            self.coins -= n
            return True
        return False

    def hearts_display(self):
        return "\u2665" * self.health + "\u2661" * (self.max_health - self.health)

    def restore_from_dict(self, data):
        self.name = data["name"]
        self.difficulty = data["difficulty"]
        self.health = data["health"]
        self.max_health = data["max_health"]
        self.coins = data["coins"]
        self.time_left = data["time_left"]
        self.current_room_index = data["room_index"]
        self.inventory = data["inventory"]
        self.score = data.get("score", 0)
        self.hints_used = data.get("hints_used", 0)
        self.hearts_lost = data.get("hearts_lost", 0)
        self.boss_defeated = data.get("boss_defeated", False)
        self.key_used = data.get("key_used", False)


# =============================================================================
#  AI ENEMY  (background thread -> queue -> main thread consumes safely)
# =============================================================================
class AIEngine(threading.Thread):
    ACTIONS = ["lock_door", "change_password", "time_penalty", "fake_alarm"]

    def __init__(self, interval_range, event_queue):
        super().__init__(daemon=True)
        self.interval_range = interval_range
        self.event_queue = event_queue
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            wait = random.uniform(*self.interval_range)
            slept = 0.0
            while slept < wait and not self._stop_event.is_set():
                time.sleep(0.25)
                slept += 0.25
            if self._stop_event.is_set():
                break
            self.event_queue.put(random.choice(self.ACTIONS))

    def stop(self):
        self._stop_event.set()


# =============================================================================
#  SOUND MANAGER (safe no-op if pygame missing) - all tones synthesized
# =============================================================================
class SoundManager:
    def __init__(self, settings):
        self.settings = settings
        self._bg_sound = None
        self._bg_channel = None

    @property
    def enabled(self):
        return SOUND_AVAILABLE and self.settings.data.get("sound_on", True)

    @property
    def music_enabled(self):
        return SOUND_AVAILABLE and self.settings.data.get("music_on", True)

    def _make_tone_buffer(self, freq, duration, volume=0.3, rate=22050):
        n = int(rate * duration)
        buf = array.array("h", [0] * n)
        for i in range(n):
            buf[i] = int(32767 * volume * ((i // max(1, rate // freq)) % 2))
        return buf

    def _play_tone(self, freq, duration, volume=0.3):
        if not self.enabled:
            return
        try:
            buf = self._make_tone_buffer(freq, duration, volume)
            pygame.mixer.Sound(buffer=bytes(buf)).play()
        except Exception:
            pass

    def beep_ok(self):
        self._play_tone(880, 0.08)

    def beep_wrong(self):
        self._play_tone(180, 0.15)

    def beep_victory(self):
        for f in (523, 659, 784, 1046):
            self._play_tone(f, 0.12)

    def beep_gameover(self):
        for f in (400, 300, 200, 120):
            self._play_tone(f, 0.18)

    def beep_achievement(self):
        self._play_tone(1200, 0.06)
        self._play_tone(1500, 0.09)

    def beep_boss_hit(self):
        self._play_tone(250, 0.1)

    def beep_level_up(self):
        """Distinct short rising chime played whenever a room is cleared."""
        for f in (660, 880, 1100):
            self._play_tone(f, 0.07, volume=0.25)

    # ---------------- background ambient loop ----------------
    def start_background_music(self):
        if not self.music_enabled:
            return
        try:
            rate = 22050
            duration = 2.0
            n = int(rate * duration)
            buf = array.array("h", [0] * n)
            # Soft layered hum: two low sine-ish square waves for an
            # ambient "server room" drone, no external audio files.
            import math
            for i in range(n):
                t = i / rate
                val = 0.12 * math.sin(2 * math.pi * 110 * t)
                val += 0.06 * math.sin(2 * math.pi * 164 * t)
                buf[i] = int(32767 * val)
            self._bg_sound = pygame.mixer.Sound(buffer=bytes(buf))
            self._bg_channel = self._bg_sound.play(loops=-1)
        except Exception:
            self._bg_sound = None
            self._bg_channel = None

    def stop_background_music(self):
        try:
            if self._bg_channel is not None:
                self._bg_channel.stop()
        except Exception:
            pass
        self._bg_channel = None
        self._bg_sound = None

    def refresh_background_music(self):
        """Call after a settings change to start/stop the loop as needed."""
        if self.music_enabled and self._bg_channel is None:
            self.start_background_music()
        elif not self.music_enabled and self._bg_channel is not None:
            self.stop_background_music()


# =============================================================================
#  MAIN APPLICATION
# =============================================================================
class HackerEscapeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hacker Escape: Cyber Breach - Deluxe Edition")
        self.geometry("1020x720")
        self.configure(bg=THEME["bg_dark"])
        self.resizable(False, False)

        self.settings = SettingsManager()
        set_theme(self.settings.data.get("theme", "Matrix"))
        self.configure(bg=THEME["bg_dark"])

        self.db = LeaderboardDB()
        self.sound = SoundManager(self.settings)
        self.achievements = AchievementManager()

        self.player = None
        self.ai_engine = None
        self.ai_queue = queue.Queue()
        self.door_locked_until = 0
        self.master_key_shield_until = 0
        self.current_answer = None
        self.current_shift = None
        self.current_ptype = None
        self.hint_text = ""
        self.timer_job = None
        self.ai_poll_job = None
        self.memory_sequence = []
        self.memory_player_progress = []
        self.memory_colors = []
        self.sudoku_puzzle = None
        self.sudoku_solution = None
        self.sudoku_entries = []
        self.terminal_stage = 0
        self.matrix_job = None
        self.matrix_running = False
        self.boss_health = 0
        self.boss_max_health = 0
        self._fullscreen = self.settings.data.get("fullscreen", False)

        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_menu()

        container = tk.Frame(self, bg=THEME["bg_dark"])
        container.pack(fill="both", expand=True)
        self.container = container

        self.sound.start_background_music()

        if self.settings.data.get("intro_on", True):
            self.show_intro()
        else:
            self.show_login()

    def _on_close(self):
        self.sound.stop_background_music()
        self.destroy()

    # ------------------------------------------------------------------ MENU
    def _build_menu(self):
        menubar = tk.Menu(self)
        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="New Game", command=self.show_login)
        game_menu.add_command(label="Save Game", command=self.save_game)
        game_menu.add_command(label="Load Game", command=self.load_game)
        game_menu.add_command(label="Leaderboard", command=self.show_leaderboard)
        game_menu.add_command(label="Achievements", command=self.show_achievements)
        game_menu.add_command(label="Settings", command=self.show_settings)
        game_menu.add_command(label="Toggle Fullscreen (F11)", command=self.toggle_fullscreen)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="Menu", menu=game_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="How To Play", command=self._how_to_play)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def toggle_fullscreen(self, event=None):
        self._fullscreen = not self._fullscreen
        self.attributes("-fullscreen", self._fullscreen)
        self.settings.data["fullscreen"] = self._fullscreen
        self.settings.save()

    def _how_to_play(self):
        messagebox.showinfo(
            "How To Play",
            "25 rooms hain, har ek alag mini-game. Difficulty gradually\n"
            "badhti hai - shuru ke rooms easy hain, aakhri wale hard.\n\n"
            "ROT13 / Caesar / Morse / Hex -> text decode karo\n"
            "Binary -> 8-bit ASCII decode karo\n"
            "Scramble -> letters ko sahi order mein jodo\n"
            "Math -> sequence ka next number batao\n"
            "Pattern -> repeating pattern ka next symbol batao\n"
            "Sudoku -> 4x4 grid solve karo\n"
            "Memory -> colour sequence yaad rakh kar click karo\n"
            "Room 24 -> AI BOSS FIGHT (multiple rounds!)\n"
            "Room 25 -> Final passcode -> ESCAPE!\n\n"
            "Confused kabhi bhi? [ LEGEND ] button dabao - poora\n"
            "reference table + worked example dikhega.\n\n"
            "Wrong answer = 1 heart kam. Health 0 = Game Over.\n"
            "Room clear karne par thoda EXTRA TIME bhi milta hai.\n"
            "Coins se Hint kharido, ya [ USE ANSWER KEY ] se room\n"
            "seedha skip karo (lekin uss room ke coins/score nahi\n"
            "milenge - sirf level up hoga).\n"
            "Inventory items USE karo - woh sirf dikhawe ke liye\n"
            "nahi hain, real fayda dete hain!"
        )

    def _clear_container(self):
        if self.matrix_job:
            self.after_cancel(self.matrix_job)
            self.matrix_job = None
        self.matrix_running = False
        for widget in self.container.winfo_children():
            widget.destroy()

    # ================================================================
    #  NEON BUTTON HELPER
    # ================================================================
    def _neon_button(self, parent, text, base_fg, command, width=22, bg=None):
        bg = bg or THEME["bg_panel"]
        btn = tk.Button(parent, text=text, font=FONT_MONO, bg=bg, fg=base_fg,
                        activeforeground="#000000", activebackground=base_fg,
                        width=width, relief="ridge", bd=2, command=command,
                        cursor="hand2")

        def on_enter(e):
            btn.config(bg=base_fg, fg="#000000")

        def on_leave(e):
            btn.config(bg=bg, fg=base_fg)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # ================================================================
    #  INTRO / BOOT SEQUENCE (binary rain + typewriter)
    # ================================================================
    def show_intro(self):
        self._clear_container()
        frame = tk.Frame(self.container, bg="#000000")
        frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(frame, width=1020, height=560, bg="#000000", highlightthickness=0)
        canvas.pack()
        self._start_matrix_rain(canvas)

        boot_lines = [
            "> booting cyber-breach kernel...",
            "> mounting encrypted filesystem...",
            "> bypassing perimeter firewall...",
            "> spoofing MAC address...",
            "> injecting simulation payload...",
            "> AI SECURITY SYSTEM DETECTED",
            "> good luck, hacker.",
        ]
        text_widget = tk.Label(frame, text="", font=("Consolas", 14), fg="#39ff14",
                               bg="#000000", justify="left", anchor="w")
        text_widget.place(x=30, y=575, width=960, height=120)

        skip_btn = self._neon_button(frame, "[ SKIP INTRO ]", "#39ff14",
                                      lambda: self._finish_intro(), width=20, bg="#000000")
        skip_btn.place(x=850, y=675)

        self._intro_cancelled = False

        def type_lines(line_idx=0, char_idx=0, accumulated=""):
            if getattr(self, "_intro_cancelled", False):
                return
            if line_idx >= len(boot_lines):
                self.after(700, self._finish_intro)
                return
            line = boot_lines[line_idx]
            if char_idx <= len(line):
                text_widget.config(text=accumulated + line[:char_idx])
                self.after(20, lambda: type_lines(line_idx, char_idx + 1, accumulated))
            else:
                self.after(350, lambda: type_lines(line_idx + 1, 0, accumulated + line + "\n"))

        type_lines()

    def _finish_intro(self):
        self._intro_cancelled = True
        self.show_login()

    def _start_matrix_rain(self, canvas):
        self.matrix_running = True
        width, height = 1020, 560
        cols = width // 16
        drops = [random.randint(0, height // 16) for _ in range(cols)]
        # Real binary rain - just 0s and 1s, for the authentic hacker feel.
        chars = "01"

        def draw():
            if not self.matrix_running:
                return
            canvas.delete("matrix")
            for i in range(cols):
                x = i * 16
                y = drops[i] * 16
                ch = random.choice(chars)
                canvas.create_text(x, y, text=ch, fill="#39ff14",
                                    font=("Consolas", 12), tags="matrix")
                if y > height and random.random() > 0.975:
                    drops[i] = 0
                else:
                    drops[i] += 1
            self.matrix_job = self.after(60, draw)

        draw()

    # ================================================================
    #  LOGIN SCREEN
    # ================================================================
    def show_login(self):
        self._stop_ai()
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self._clear_container()

        frame = tk.Frame(self.container, bg=THEME["bg_dark"])
        frame.pack(fill="both", expand=True)

        title_label = tk.Label(frame, text="", font=FONT_TITLE, fg=THEME["fg_primary"],
                                bg=THEME["bg_dark"])
        title_label.pack(pady=(50, 10))
        full_title = ">>> HACKER ESCAPE: CYBER BREACH <<<"

        def typewriter(i=0):
            if i <= len(full_title):
                title_label.config(text=full_title[:i])
                self.after(35, lambda: typewriter(i + 1))

        typewriter()

        tk.Label(frame, text="Ethical Hacker Simulation - Bypass the AI Security System",
                 font=FONT_MONO, fg=THEME["fg_accent"], bg=THEME["bg_dark"]).pack(pady=(0, 25))

        form = tk.Frame(frame, bg=THEME["bg_panel"], padx=30, pady=25, highlightbackground=THEME["fg_primary"],
                         highlightthickness=1)
        form.pack(pady=5)

        tk.Label(form, text="Player Name:", font=FONT_MONO, fg=THEME["fg_primary"],
                 bg=THEME["bg_panel"]).grid(row=0, column=0, sticky="w", pady=8)
        name_entry = tk.Entry(form, font=FONT_MONO, bg="#000000", fg=THEME["fg_primary"],
                               insertbackground=THEME["fg_primary"], width=25)
        name_entry.grid(row=0, column=1, pady=8, padx=10)
        name_entry.insert(0, "Agent")

        tk.Label(form, text="Difficulty:", font=FONT_MONO, fg=THEME["fg_primary"],
                 bg=THEME["bg_panel"]).grid(row=1, column=0, sticky="w", pady=8)
        difficulty_var = tk.StringVar(value="Medium")
        diff_menu = ttk.Combobox(form, textvariable=difficulty_var, state="readonly",
                                  values=list(DIFFICULTY_SETTINGS.keys()), width=22)
        diff_menu.grid(row=1, column=1, pady=8, padx=10)

        def start_new():
            name = name_entry.get().strip() or "Agent"
            diff = difficulty_var.get()
            self.player = Player(name, diff)
            self.hint_text = ""
            self._start_ai()
            self.show_room(0)

        def load_saved():
            data = SaveManager.load()
            if not data:
                messagebox.showwarning("Load Game", "Koi saved game nahi mila (save.json not found).")
                return
            p = Player(data["name"], data["difficulty"])
            p.restore_from_dict(data)
            self.player = p
            self._start_ai()
            self.show_room(p.current_room_index)

        btn_frame = tk.Frame(frame, bg=THEME["bg_dark"])
        btn_frame.pack(pady=20)
        self._neon_button(btn_frame, "[ START NEW GAME ]", THEME["fg_primary"],
                           start_new).grid(row=0, column=0, padx=8, pady=6)
        self._neon_button(btn_frame, "[ LOAD GAME ]", THEME["fg_accent"],
                           load_saved).grid(row=0, column=1, padx=8, pady=6)
        self._neon_button(btn_frame, "[ LEADERBOARD ]", THEME["fg_warning"],
                           self.show_leaderboard).grid(row=1, column=0, padx=8, pady=6)
        self._neon_button(btn_frame, "[ ACHIEVEMENTS ]", THEME["fg_danger"],
                           self.show_achievements).grid(row=1, column=1, padx=8, pady=6)
        self._neon_button(btn_frame, "[ SETTINGS ]", THEME["fg_primary"],
                           self.show_settings).grid(row=2, column=0, columnspan=2, pady=6)

        tk.Label(frame, text="Tip: 25 rooms, difficulty ramps up gradually, ek AI Boss Fight\n"
                             "aur multiple endings hain. Confused ho toh LEGEND button use karo!",
                 font=("Consolas", 10, "italic"), fg="#888888", bg=THEME["bg_dark"],
                 justify="center").pack(pady=15)

    # ================================================================
    #  SETTINGS SCREEN
    # ================================================================
    def show_settings(self):
        self._stop_ai()
        self._clear_container()
        frame = tk.Frame(self.container, bg=THEME["bg_dark"])
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=">>> SETTINGS <<<", font=FONT_TITLE, fg=THEME["fg_primary"],
                 bg=THEME["bg_dark"]).pack(pady=30)

        panel = tk.Frame(frame, bg=THEME["bg_panel"], padx=30, pady=25)
        panel.pack(pady=10)

        sound_var = tk.BooleanVar(value=self.settings.data.get("sound_on", True))
        music_var = tk.BooleanVar(value=self.settings.data.get("music_on", True))
        intro_var = tk.BooleanVar(value=self.settings.data.get("intro_on", True))
        theme_var = tk.StringVar(value=self.settings.data.get("theme", "Matrix"))

        tk.Checkbutton(panel, text="Sound Effects", variable=sound_var, font=FONT_MONO,
                       fg=THEME["fg_primary"], bg=THEME["bg_panel"], selectcolor="#000000",
                       activebackground=THEME["bg_panel"]).grid(row=0, column=0, sticky="w", pady=8)
        tk.Checkbutton(panel, text="Background Music", variable=music_var, font=FONT_MONO,
                       fg=THEME["fg_primary"], bg=THEME["bg_panel"], selectcolor="#000000",
                       activebackground=THEME["bg_panel"]).grid(row=1, column=0, sticky="w", pady=8)
        tk.Checkbutton(panel, text="Show Boot Intro", variable=intro_var, font=FONT_MONO,
                       fg=THEME["fg_primary"], bg=THEME["bg_panel"], selectcolor="#000000",
                       activebackground=THEME["bg_panel"]).grid(row=2, column=0, sticky="w", pady=8)

        tk.Label(panel, text="Theme:", font=FONT_MONO, fg=THEME["fg_primary"],
                 bg=THEME["bg_panel"]).grid(row=3, column=0, sticky="w", pady=8)
        theme_menu = ttk.Combobox(panel, textvariable=theme_var, state="readonly",
                                   values=list(THEMES.keys()), width=20)
        theme_menu.grid(row=3, column=1, padx=10)

        if not SOUND_AVAILABLE:
            tk.Label(panel, text="(pygame not installed - sound/music stay silent)",
                     font=FONT_MONO_SMALL, fg="#888888", bg=THEME["bg_panel"]
                     ).grid(row=4, column=0, columnspan=2, pady=(6, 0))

        def apply_and_back():
            self.settings.data["sound_on"] = sound_var.get()
            self.settings.data["music_on"] = music_var.get()
            self.settings.data["intro_on"] = intro_var.get()
            self.settings.data["theme"] = theme_var.get()
            self.settings.save()
            set_theme(theme_var.get())
            self.configure(bg=THEME["bg_dark"])
            self.sound.refresh_background_music()
            messagebox.showinfo("Settings", "Settings saved!")
            self.show_login()

        self._neon_button(frame, "[ SAVE & BACK ]", THEME["fg_primary"],
                           apply_and_back, width=25).pack(pady=25)

    # ================================================================
    #  ACHIEVEMENTS SCREEN
    # ================================================================
    def show_achievements(self):
        self._stop_ai()
        self._clear_container()
        frame = tk.Frame(self.container, bg=THEME["bg_dark"])
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=">>> ACHIEVEMENTS <<<", font=FONT_TITLE, fg=THEME["fg_warning"],
                 bg=THEME["bg_dark"]).pack(pady=25)

        listing = tk.Frame(frame, bg=THEME["bg_panel"], padx=25, pady=20)
        listing.pack(pady=10)
        for key, desc in ACHIEVEMENT_DEFS.items():
            unlocked = key in self.achievements.unlocked
            icon = "[X]" if unlocked else "[ ]"
            color = THEME["fg_primary"] if unlocked else "#555555"
            tk.Label(listing, text=f"{icon} {desc}", font=FONT_MONO, fg=color,
                     bg=THEME["bg_panel"], anchor="w", justify="left").pack(anchor="w", pady=4)

        tk.Label(frame, text="Note: rooms skipped with the Answer Key don't count\n"
                             "toward achievements - those need genuine solves.",
                 font=FONT_MONO_SMALL, fg="#888888", bg=THEME["bg_dark"],
                 justify="center").pack(pady=(0, 10))

        self._neon_button(frame, "[ BACK TO MENU ]", THEME["fg_primary"],
                           self.show_login, width=25).pack(pady=20)

    # ================================================================
    #  AI ENGINE CONTROL
    # ================================================================
    def _start_ai(self):
        self._stop_ai()
        settings = DIFFICULTY_SETTINGS[self.player.difficulty]
        self.ai_queue = queue.Queue()
        self.ai_engine = AIEngine(settings["ai_interval"], self.ai_queue)
        self.ai_engine.start()
        self._poll_ai_queue()

    def _stop_ai(self):
        if self.ai_engine is not None:
            self.ai_engine.stop()
            self.ai_engine = None
        if self.ai_poll_job:
            self.after_cancel(self.ai_poll_job)
            self.ai_poll_job = None

    def _poll_ai_queue(self):
        try:
            while True:
                action = self.ai_queue.get_nowait()
                self._handle_ai_action(action)
        except queue.Empty:
            pass
        self.ai_poll_job = self.after(400, self._poll_ai_queue)

    def _handle_ai_action(self, action):
        if self.player is None or not hasattr(self, "status_bar_labels"):
            return
        if action == "lock_door":
            if time.time() < self.master_key_shield_until:
                self._flash_alert("MASTER KEY blocked an AI lock attempt!")
                return
            self.door_locked_until = time.time() + 4
            self._flash_alert("AI SECURITY: Door temporarily LOCKED! (4s)")
        elif action == "change_password":
            self._regenerate_current_puzzle()
            self._flash_alert("AI SECURITY: Password changed! Read the new hint.")
        elif action == "time_penalty":
            penalty = random.randint(8, 20)
            self.player.time_left = max(0, self.player.time_left - penalty)
            self._flash_alert(f"AI SECURITY: -{penalty}s time penalty!")
        elif action == "fake_alarm":
            self._flash_alert("AI SECURITY: Intrusion alarm triggered! (no real effect)")
        self._refresh_status_bar()

    def _flash_alert(self, msg):
        if hasattr(self, "alert_label"):
            self.alert_label.config(text=msg, fg=THEME["fg_danger"])
            self.after(3000, lambda: self.alert_label.config(text="", fg=THEME["fg_danger"]))

    # ================================================================
    #  PARTICLE BURST EFFECT
    # ================================================================
    def _particle_burst(self, parent, color=None, count=18):
        color = color or THEME["fg_primary"]
        w, h = 380, 220
        canvas = tk.Canvas(parent, width=w, height=h, bg=THEME["bg_panel"], highlightthickness=0)
        canvas.place(relx=0.5, rely=0.5, anchor="center")
        cx, cy = w // 2, h // 2
        particles = []
        for _ in range(count):
            angle = random.uniform(0, 6.283)
            speed = random.uniform(2, 6)
            dx, dy = speed * random.uniform(-1, 1), speed * random.uniform(-1, 1)
            pid = canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=color, outline="")
            particles.append([pid, dx, dy])

        def animate(step=0):
            if step > 18:
                canvas.destroy()
                return
            for p in particles:
                canvas.move(p[0], p[1], p[2])
            self.after(35, lambda: animate(step + 1))

        animate()

    # ================================================================
    #  GAME OVER / WIN
    # ================================================================
    def _compute_ending_tier(self):
        pct_time = self.player.time_left / max(1, self.player.total_time)
        if (self.player.hearts_lost == 0 and self.player.hints_used == 0
                and self.player.boss_defeated and not self.player.key_used):
            return "PERFECT ESCAPE", "Bilkul flawless run! Ek bhi galti nahi, ek bhi hint nahi."
        if pct_time > 0.4 and self.player.health >= self.player.max_health * 0.6:
            return "CLEAN ESCAPE", "Bahut badhiya! Health aur time dono achhe rahe."
        return "NARROW ESCAPE", "Bach gaye, lekin bahut kareeb tha! Health/time kam bacha tha."

    def _check_achievements(self):
        newly = []
        if self.player.key_used:
            # Answer Key was used at least once this run - no achievements,
            # since those are meant to reward genuine solving.
            self.achievements.save()
            return newly
        if self.player.hearts_lost == 0 and self.achievements.unlock("no_damage"):
            newly.append(ACHIEVEMENT_DEFS["no_damage"])
        if self.player.time_left > self.player.total_time * 0.5 and self.achievements.unlock("speed_runner"):
            newly.append(ACHIEVEMENT_DEFS["speed_runner"])
        if self.player.hints_used == 0 and self.achievements.unlock("hint_free"):
            newly.append(ACHIEVEMENT_DEFS["hint_free"])
        if self.player.boss_defeated and self.achievements.unlock("boss_slayer"):
            newly.append(ACHIEVEMENT_DEFS["boss_slayer"])
        if self.player.coins >= 300 and self.achievements.unlock("coin_collector"):
            newly.append(ACHIEVEMENT_DEFS["coin_collector"])
        if (self.player.hearts_lost == 0 and self.player.hints_used == 0
                and self.player.boss_defeated and self.achievements.unlock("perfect_escape")):
            newly.append(ACHIEVEMENT_DEFS["perfect_escape"])
        self.achievements.save()
        return newly

    def _end_game(self, won):
        self._stop_ai()
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

        elapsed = self.player.total_time - self.player.time_left
        self.db.add_score(self.player.name, elapsed, self.player.score, self.player.difficulty)

        if won:
            bonus = self.player.health * 50 + self.player.coins
            self.player.score += bonus
            tier, tier_desc = self._compute_ending_tier()
            newly = self._check_achievements()
            self.sound.beep_victory()
            self._show_ending_screen(tier, tier_desc, elapsed, newly)
        else:
            self.sound.beep_gameover()
            self._show_gameover_screen(elapsed)

    def _show_ending_screen(self, tier, tier_desc, elapsed, newly_unlocked):
        self._clear_container()
        frame = tk.Frame(self.container, bg=THEME["bg_dark"])
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=">>> ESCAPE SUCCESSFUL <<<", font=FONT_TITLE,
                 fg=THEME["fg_primary"], bg=THEME["bg_dark"]).pack(pady=(40, 5))
        tk.Label(frame, text=tier, font=("Consolas", 22, "bold"), fg=THEME["fg_warning"],
                 bg=THEME["bg_dark"]).pack(pady=5)
        tk.Label(frame, text=tier_desc, font=FONT_MONO, fg=THEME["fg_accent"],
                 bg=THEME["bg_dark"]).pack(pady=5)

        stats_frame = tk.Frame(frame, bg=THEME["bg_panel"], padx=30, pady=20)
        stats_frame.pack(pady=15)
        self._particle_burst(stats_frame, THEME["fg_primary"])
        tk.Label(stats_frame, text=f"Player: {self.player.name}", font=FONT_MONO,
                 fg=THEME["fg_primary"], bg=THEME["bg_panel"]).pack(anchor="w")
        tk.Label(stats_frame, text=f"Final Score: {self.player.score}", font=FONT_MONO,
                 fg=THEME["fg_primary"], bg=THEME["bg_panel"]).pack(anchor="w")
        tk.Label(stats_frame, text=f"Time Taken: {elapsed}s", font=FONT_MONO,
                 fg=THEME["fg_primary"], bg=THEME["bg_panel"]).pack(anchor="w")

        if newly_unlocked:
            tk.Label(frame, text="New Achievements Unlocked!", font=FONT_MONO_BIG,
                     fg=THEME["fg_warning"], bg=THEME["bg_dark"]).pack(pady=(15, 5))
            self.sound.beep_achievement()
            for a in newly_unlocked:
                tk.Label(frame, text=f"* {a}", font=FONT_MONO, fg=THEME["fg_warning"],
                         bg=THEME["bg_dark"]).pack()

        btn_frame = tk.Frame(frame, bg=THEME["bg_dark"])
        btn_frame.pack(pady=25)
        self._neon_button(btn_frame, "[ LEADERBOARD ]", THEME["fg_accent"],
                           self.show_leaderboard).grid(row=0, column=0, padx=8)
        self._neon_button(btn_frame, "[ MAIN MENU ]", THEME["fg_primary"],
                           self.show_login).grid(row=0, column=1, padx=8)

    def _show_gameover_screen(self, elapsed):
        self._clear_container()
        frame = tk.Frame(self.container, bg="#1a0000")
        frame.pack(fill="both", expand=True)

        title = tk.Label(frame, text="GAME OVER", font=FONT_TITLE, fg=THEME["fg_danger"], bg="#1a0000")
        title.pack(pady=(60, 10))

        def flash(count=0):
            if count > 8:
                return
            color = "#ff0000" if count % 2 == 0 else "#550000"
            title.config(fg=color)
            self.after(250, lambda: flash(count + 1))

        flash()

        tk.Label(frame, text=f"{self.player.name}, AI security ne tumhe pakad liya!",
                 font=FONT_MONO, fg="#ffffff", bg="#1a0000").pack(pady=10)
        tk.Label(frame, text=f"Score: {self.player.score}   |   Survived: {elapsed}s",
                 font=FONT_MONO, fg=THEME["fg_warning"], bg="#1a0000").pack(pady=10)

        btn_frame = tk.Frame(frame, bg="#1a0000")
        btn_frame.pack(pady=25)
        self._neon_button(btn_frame, "[ LEADERBOARD ]", THEME["fg_accent"],
                           self.show_leaderboard).grid(row=0, column=0, padx=8)
        self._neon_button(btn_frame, "[ MAIN MENU ]", THEME["fg_primary"],
                           self.show_login).grid(row=0, column=1, padx=8)

    # ================================================================
    #  LEADERBOARD
    # ================================================================
    def show_leaderboard(self):
        self._stop_ai()
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self._clear_container()

        frame = tk.Frame(self.container, bg=THEME["bg_dark"])
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=">>> LEADERBOARD <<<", font=FONT_TITLE,
                 fg=THEME["fg_warning"], bg=THEME["bg_dark"]).pack(pady=20)

        cols = ("Name", "Time(s)", "Score", "Difficulty", "Date")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=150, anchor="center")
        tree.pack(pady=10, padx=20, fill="x")

        for row in self.db.get_top(15):
            tree.insert("", "end", values=row)

        self._neon_button(frame, "[ BACK TO MENU ]", THEME["fg_primary"],
                           self.show_login, width=25).pack(pady=20)

    # ================================================================
    #  SAVE / LOAD from menu
    # ================================================================
    def save_game(self):
        if self.player is None:
            messagebox.showwarning("Save Game", "Pehle ek game start karo!")
            return
        SaveManager.save(self.player)
        messagebox.showinfo("Save Game", "Game saved to save.json")

    def load_game(self):
        data = SaveManager.load()
        if not data:
            messagebox.showwarning("Load Game", "Koi saved game nahi mila.")
            return
        p = Player(data["name"], data["difficulty"])
        p.restore_from_dict(data)
        self.player = p
        self._start_ai()
        self.show_room(p.current_room_index)

    # ================================================================
    #  ROOM / GAMEPLAY SCREEN
    # ================================================================

    def show_room(self, room_index):
        self.player.current_room_index = room_index
        self._clear_container()
        self.terminal_stage = 0

        main = tk.Frame(self.container, bg=THEME["bg_dark"])
        main.pack(fill="both", expand=True)

        status = tk.Frame(main, bg=THEME["bg_panel"], pady=8)
        status.pack(fill="x")
        self.status_bar_labels = {}

        self.status_bar_labels["health"] = tk.Label(
            status, text=f"Health: {self.player.hearts_display()}",
            font=FONT_MONO_BIG, fg=THEME["fg_danger"], bg=THEME["bg_panel"])
        self.status_bar_labels["health"].pack(side="left", padx=15)

        self.status_bar_labels["coins"] = tk.Label(
            status, text=f"Coins: {self.player.coins}",
            font=FONT_MONO_BIG, fg=THEME["fg_warning"], bg=THEME["bg_panel"])
        self.status_bar_labels["coins"].pack(side="left", padx=15)

        self.status_bar_labels["timer"] = tk.Label(
            status, text=f"Time: {self._fmt_time(self.player.time_left)}",
            font=FONT_MONO_BIG, fg=THEME["fg_accent"], bg=THEME["bg_panel"])
        self.status_bar_labels["timer"].pack(side="left", padx=15)

        self.status_bar_labels["room"] = tk.Label(
            status, text=f"{ROOMS[room_index]['name']}  ({room_index + 1}/{len(ROOMS)})",
            font=("Consolas", 14, "bold"), fg=THEME["fg_primary"], bg=THEME["bg_panel"])
        self.status_bar_labels["room"].pack(side="right", padx=15)

        self.alert_label = tk.Label(main, text="", font=("Consolas", 12, "bold"),
                                     fg=THEME["fg_danger"], bg=THEME["bg_dark"])
        self.alert_label.pack(fill="x")

        prog = ttk.Progressbar(main, length=980, maximum=len(ROOMS) - 1, value=room_index)
        prog.pack(pady=4)

        body = tk.Frame(main, bg=THEME["bg_dark"])
        body.pack(fill="both", expand=True, padx=15, pady=5)

        # ---------------- terminal (left) ----------------
        term_frame = tk.Frame(body, bg=THEME["term_bg"], bd=2, relief="sunken")
        term_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(term_frame, text="TERMINAL", font=FONT_MONO, fg=THEME["fg_primary"],
                 bg=THEME["term_bg"]).pack(anchor="w", padx=5)

        self.terminal_text = tk.Text(term_frame, width=42, height=18, bg=THEME["term_bg"],
                                      fg=THEME["fg_primary"], font=("Consolas", 11), state="disabled")
        self.terminal_text.pack(padx=5, pady=5, fill="both", expand=True)

        term_btns = tk.Frame(term_frame, bg=THEME["term_bg"])
        term_btns.pack(pady=5)
        self._neon_button(term_btns, "connect", THEME["fg_primary"], self._term_connect,
                           width=9, bg=THEME["term_bg"]).grid(row=0, column=0, padx=2)
        self._neon_button(term_btns, "scan", THEME["fg_primary"], self._term_scan,
                           width=9, bg=THEME["term_bg"]).grid(row=0, column=1, padx=2)
        self._neon_button(term_btns, "exploit", THEME["fg_primary"], self._term_exploit,
                           width=9, bg=THEME["term_bg"]).grid(row=0, column=2, padx=2)
        self._neon_button(term_btns, "clear", THEME["fg_danger"], self._term_clear,
                           width=9, bg=THEME["term_bg"]).grid(row=0, column=3, padx=2)

        self._term_print("Welcome, hacker. Type-simulate commands using the buttons below.")
        self._term_print(f"Objective: {ROOMS[room_index]['name']}")

        # ---------------- puzzle area (right) ----------------
        self.puzzle_frame = tk.Frame(body, bg=THEME["bg_panel"], bd=2, relief="ridge")
        self.puzzle_frame.pack(side="right", fill="both", expand=True)

        self._build_puzzle_for_room(room_index)

        # ---------------- bottom controls ----------------
        bottom = tk.Frame(main, bg=THEME["bg_dark"], pady=8)
        bottom.pack(fill="x")

        pw_row = tk.Frame(bottom, bg=THEME["bg_dark"])
        pw_row.pack(fill="x")
        tk.Label(pw_row, text="Password:", font=FONT_MONO, fg=THEME["fg_primary"],
                 bg=THEME["bg_dark"]).pack(side="left", padx=5)
        self.password_entry = tk.Entry(pw_row, font=FONT_MONO, width=22, bg="#000000",
                                        fg=THEME["fg_primary"], insertbackground=THEME["fg_primary"])
        self.password_entry.pack(side="left", padx=5)
        self.password_entry.bind("<Return>", lambda e: self._submit_password())
        self.password_entry.bind("<KeyRelease>", self._update_strength_meter)

        self.strength_label = tk.Label(pw_row, text="Strength: -", font=FONT_MONO_SMALL,
                                        fg="#888888", bg=THEME["bg_dark"], width=22)
        self.strength_label.pack(side="left", padx=10)

        self._neon_button(pw_row, "[ SUBMIT ]", THEME["fg_primary"], self._submit_password,
                           width=10).pack(side="left", padx=4)

        btn_row = tk.Frame(bottom, bg=THEME["bg_dark"])
        btn_row.pack(pady=6)
        self._neon_button(btn_row, "[ HINT ]", THEME["fg_warning"], self._buy_hint,
                           width=13).grid(row=0, column=0, padx=3)
        self._neon_button(btn_row, "[ LEGEND ]", "#9dff9d", self._show_legend,
                           width=13).grid(row=0, column=1, padx=3)
        self._neon_button(btn_row, "[ USE ANSWER KEY ]", "#ff9d5c", self._use_answer_key,
                           width=17).grid(row=0, column=2, padx=3)
        self._neon_button(btn_row, "[ INVENTORY ]", THEME["fg_accent"], self._show_inventory,
                           width=13).grid(row=0, column=3, padx=3)
        self._neon_button(btn_row, "[ MAP ]", "#d38bff", self._show_map,
                           width=13).grid(row=0, column=4, padx=3)
        self._neon_button(btn_row, "[ SAVE ]", "#ffffff", self.save_game,
                           width=13).grid(row=0, column=5, padx=3)

        self._refresh_status_bar()
        self._start_timer()

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _fmt_time(seconds):
        m, s = divmod(max(0, int(seconds)), 60)
        return f"{m:02d}:{s:02d}"

    def _refresh_status_bar(self):
        if not hasattr(self, "status_bar_labels"):
            return
        self.status_bar_labels["health"].config(text=f"Health: {self.player.hearts_display()}")
        self.status_bar_labels["coins"].config(text=f"Coins: {self.player.coins}")
        self.status_bar_labels["timer"].config(text=f"Time: {self._fmt_time(self.player.time_left)}")

    def _update_strength_meter(self, event=None):
        text = self.password_entry.get()
        score = min(len(text) * 15, 70)
        if any(c.isdigit() for c in text):
            score += 15
        if any(c.isupper() for c in text) and any(c.islower() for c in text):
            score += 15
        score = min(score, 100)
        if score == 0:
            label, color = "-", "#888888"
        elif score < 40:
            label, color = "Weak", THEME["fg_danger"]
        elif score < 75:
            label, color = "Medium", THEME["fg_warning"]
        else:
            label, color = "Strong", THEME["fg_primary"]
        self.strength_label.config(text=f"Strength: {label}", fg=color)

    def _start_timer(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)

        def tick():
            if self.player is None:
                return
            self.player.time_left -= 1
            self._refresh_status_bar()
            if self.player.time_left <= 0:
                self._end_game(won=False)
                return
            self.timer_job = self.after(1000, tick)

        self.timer_job = self.after(1000, tick)

    # ---------------------------------------------------------------- terminal
    def _term_print(self, line):
        self.terminal_text.config(state="normal")
        self.terminal_text.insert("end", line + "\n")
        self.terminal_text.see("end")
        self.terminal_text.config(state="disabled")

    def _term_clear(self):
        self.terminal_text.config(state="normal")
        self.terminal_text.delete("1.0", "end")
        self.terminal_text.config(state="disabled")

    def _term_connect(self):
        self._term_print("> connect")
        self._term_print("Connected to 192.168.0.101 [simulation]")
        self.terminal_stage = max(self.terminal_stage, 1)

    def _term_scan(self):
        self._term_print("> scan")
        if self.terminal_stage < 1:
            self._term_print("Error: connect first!")
            return
        self._term_print("Port 22 Open (SSH)")
        self._term_print("Port 80 Open (HTTP)")
        self._term_print("Port 443 Open (HTTPS)")
        self.terminal_stage = max(self.terminal_stage, 2)

    def _term_exploit(self):
        self._term_print("> exploit")
        if self.terminal_stage < 2:
            self._term_print("Error: scan the ports first!")
            return
        self._term_print("Running simulated exploit module...")
        self._term_print("Access partially granted. Hint unlocked!")
        self.terminal_stage = 3
        if self.hint_text:
            self._term_print(f"HINT: {self.hint_text}")

    # ---------------------------------------------------------------- hint / legend / key / inventory / map
    def _buy_hint(self):
        cost = DIFFICULTY_SETTINGS[self.player.difficulty]["hint_cost"]
        if not self.hint_text:
            messagebox.showinfo("Hint", "Is puzzle ke liye koi extra hint available nahi hai.")
            return
        if self.player.spend_coins(cost):
            self.player.hints_used += 1
            self._refresh_status_bar()
            messagebox.showinfo("Hint", self.hint_text)
        else:
            messagebox.showwarning("Hint", f"Not enough coins! Hint costs {cost} coins.")

    def _show_legend(self):
        ptype = self.current_ptype or ROOMS[self.player.current_room_index]["type"]
        if ptype == "rot13":
            text = PuzzleGenerator.legend_rot13()
        elif ptype == "caesar":
            text = PuzzleGenerator.legend_caesar(self.current_shift or 3)
        elif ptype == "binary":
            text = PuzzleGenerator.legend_binary()
        elif ptype == "hex":
            text = PuzzleGenerator.legend_hex()
        elif ptype == "morse":
            text = PuzzleGenerator.legend_morse()
        elif ptype == "final":
            text = PuzzleGenerator.legend_caesar(self.current_shift or 3)
        elif ptype == "boss":
            text = PuzzleGenerator.legend_generic("boss")
        else:
            text = PuzzleGenerator.legend_generic(ptype)

        win = tk.Toplevel(self)
        win.title("Legend / Reference")
        win.configure(bg=THEME["bg_panel"])
        win.geometry("480x420")
        tk.Label(win, text="REFERENCE / LEGEND", font=FONT_MONO_BIG, fg=THEME["fg_accent"],
                 bg=THEME["bg_panel"]).pack(pady=(10, 5))
        txt_widget = tk.Text(win, bg="#000000", fg=THEME["fg_primary"], font=("Consolas", 11),
                              wrap="word", width=55, height=18)
        txt_widget.pack(padx=12, pady=8, fill="both", expand=True)
        txt_widget.insert("1.0", text)
        txt_widget.config(state="disabled")
        self._neon_button(win, "[ CLOSE ]", THEME["fg_primary"], win.destroy, width=15).pack(pady=8)

    def _answer_key_cost(self):
        base = DIFFICULTY_SETTINGS[self.player.difficulty]["hint_cost"]
        return int(round(base * ANSWER_KEY_COST_MULTIPLIER))

    def _use_answer_key(self):
        cost = self._answer_key_cost()
        confirm = messagebox.askyesno(
            "Use Answer Key",
            f"Answer Key clears this room instantly for {cost} coins.\n\n"
            "NOTE: no coins or score are earned for this room, and it\n"
            "won't count toward achievements. Continue?"
        )
        if not confirm:
            return
        if not self.player.spend_coins(cost):
            messagebox.showwarning("Answer Key", f"Not enough coins! Answer Key costs {cost} coins.")
            return
        self.player.key_used = True
        self._term_print("Answer Key used - room bypassed (no reward).")
        self._refresh_status_bar()
        self._advance_room(reward=False)

    def _show_inventory(self):
        win = tk.Toplevel(self)
        win.title("Inventory")
        win.configure(bg=THEME["bg_panel"])
        win.geometry("380x300")

        tk.Label(win, text="INVENTORY", font=FONT_MONO_BIG, fg=THEME["fg_primary"],
                 bg=THEME["bg_panel"]).pack(pady=10)

        if not self.player.inventory:
            tk.Label(win, text="Inventory khaali hai.\nRooms solve karke items dhoondo!",
                     font=FONT_MONO, fg="#aaaaaa", bg=THEME["bg_panel"]).pack(pady=20)
            return

        for item in list(self.player.inventory):
            row = tk.Frame(win, bg=THEME["bg_panel"])
            row.pack(fill="x", padx=15, pady=6)
            tk.Label(row, text=item, font=FONT_MONO, fg=THEME["fg_warning"],
                     bg=THEME["bg_panel"], width=14, anchor="w").pack(side="left")
            tk.Button(row, text="Use", font=FONT_MONO_SMALL, bg=THEME["fg_primary"],
                      fg="#000000", command=lambda it=item, w=win: self._use_item(it, w)).pack(side="right")
            tk.Label(win, text=ITEM_DESCRIPTIONS.get(item, ""), font=FONT_MONO_SMALL,
                     fg="#888888", bg=THEME["bg_panel"], wraplength=340, justify="left").pack(padx=15)

    def _use_item(self, item, window=None):
        if item not in self.player.inventory:
            return
        if item == "USB_DRIVE":
            self.player.inventory.remove(item)
            messagebox.showinfo("USB Drive", "Auto-solving current puzzle...")
            self._correct_answer()
        elif item == "MASTER_KEY":
            self.player.inventory.remove(item)
            self.door_locked_until = 0
            self.master_key_shield_until = time.time() + 30
            messagebox.showinfo("Master Key", "Door unlocked! AI locks blocked for 30 seconds.")
        elif item == "SHIELD_MODULE":
            self.player.inventory.remove(item)
            self.player.shield_active = True
            messagebox.showinfo("Shield Module", "Shield active! Next wrong answer won't cost a heart.")
        if window is not None:
            window.destroy()
            self._show_inventory()

    def _maybe_award_item(self):
        if random.random() < 0.18 and len(self.player.inventory) < 3:
            item = random.choice(ITEM_POOL)
            self.player.inventory.append(item)
            self._term_print(f"Item found: {item}!")
            messagebox.showinfo("Item Acquired", f"You found: {item}\n{ITEM_DESCRIPTIONS[item]}")

    def _show_map(self):
        lines = []
        for i, r in enumerate(ROOMS):
            marker = ">> " if i == self.player.current_room_index else "   "
            done = "[DONE]" if i < self.player.current_room_index else ""
            lines.append(f"{marker}{r['name']} {done}")
        win = tk.Toplevel(self)
        win.title("Map")
        win.configure(bg=THEME["bg_panel"])
        win.geometry("420x500")
        text = tk.Text(win, bg=THEME["bg_panel"], fg=THEME["fg_primary"], font=FONT_MONO_SMALL)
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", "\n".join(lines))
        text.config(state="disabled")

    # ================================================================
    #  PUZZLE BUILDERS PER ROOM
    # ================================================================
    def _build_puzzle_for_room(self, room_index):
        for w in self.puzzle_frame.winfo_children():
            w.destroy()
        room = ROOMS[room_index]
        ptype = room["type"]
        self.current_ptype = ptype

        builders = {
            "rot13": self._build_rot13_puzzle,
            "binary": self._build_binary_puzzle,
            "caesar": self._build_caesar_puzzle,
            "morse": self._build_morse_puzzle,
            "hex": self._build_hex_puzzle,
            "scramble": self._build_scramble_puzzle,
            "math": self._build_math_puzzle,
            "pattern": self._build_pattern_puzzle,
            "sudoku": self._build_sudoku_room,
            "memory": self._build_memory_room,
            "boss": self._build_boss_room,
            "final": self._build_final_room,
        }
        builders[ptype]()

    def _regenerate_current_puzzle(self):
        room = self.player.current_room_index
        ptype = ROOMS[room]["type"]
        if ptype == "sudoku":
            return  # regenerating mid-solve would be too harsh
        self._build_puzzle_for_room(room)

    def _puzzle_title(self, text):
        tk.Label(self.puzzle_frame, text=text, font=FONT_MONO_BIG, fg=THEME["fg_accent"],
                 bg=THEME["bg_panel"]).pack(pady=10)

    def _puzzle_display(self, text, size=20):
        tk.Label(self.puzzle_frame, text=text, font=("Consolas", size, "bold"),
                 fg=THEME["fg_warning"], bg=THEME["bg_panel"], wraplength=380,
                 justify="center").pack(pady=20)

    def _puzzle_tip(self, text):
        tk.Label(self.puzzle_frame, text=text, font=("Consolas", 10, "italic"),
                 fg="#888888", bg=THEME["bg_panel"], wraplength=380,
                 justify="center").pack()

    def _puzzle_question(self, text):
        """A clear one-line 'what am I supposed to do' instruction, shown
        above the puzzle display so nobody is left guessing."""
        tk.Label(self.puzzle_frame, text=text, font=("Consolas", 11), fg="#cfcfcf",
                 bg=THEME["bg_panel"], wraplength=380, justify="center").pack(pady=(0, 5))

    # ---- simple text puzzles ----
    def _build_rot13_puzzle(self):
        word, encoded = PuzzleGenerator.make_rot13_puzzle()
        self.current_answer = word
        self.hint_text = (f"ROT13 decode karo. First letter of the answer is '{word[0]}'. "
                           f"Full answer has {len(word)} letters.")
        self._puzzle_title("ROT13 PASSWORD PUZZLE")
        self._puzzle_question("Decode this ROT13 text and type the original word as the password:")
        self._puzzle_display(encoded)
        self._puzzle_tip("Tip: ROT13 shifts every letter 13 places (A<->N, B<->O...). "
                          "Tap [ LEGEND ] for the full table + a worked example.")

    def _build_binary_puzzle(self):
        word, encoded = PuzzleGenerator.make_binary_puzzle()
        self.current_answer = word
        self.hint_text = (f"Binary mein {len(word)} letters hain (8 bits each). "
                           f"First letter is '{word[0]}'.")
        self._puzzle_title("BINARY DECODE PUZZLE")
        self._puzzle_question("Convert each 8-bit group below to a letter, and type the resulting word:")
        self._puzzle_display(encoded, size=16)
        self._puzzle_tip("Tip: every 8 bits = 1 letter. Tap [ LEGEND ] for a sample table + example.")

    def _build_caesar_puzzle(self):
        word, encoded, shift = PuzzleGenerator.make_caesar_puzzle()
        self.current_answer = word
        self.current_shift = shift
        self.hint_text = (f"Caesar shift = {shift}. Har letter ko {shift} places PEECHE shift karo. "
                           f"Answer has {len(word)} letters, starts with '{word[0]}'.")
        self._puzzle_title(f"CAESAR CIPHER (shift={shift})")
        self._puzzle_question(f"Shift every letter below BACKWARD by {shift} and type the result:")
        self._puzzle_display(encoded)
        self._puzzle_tip("Tip: this is the opposite of how it was encrypted. "
                          "Tap [ LEGEND ] for a worked example with this exact shift.")

    def _build_morse_puzzle(self):
        word, encoded = PuzzleGenerator.make_morse_puzzle()
        self.current_answer = word
        self.hint_text = (f"Morse code, {len(word)} letters ka word hai, first letter '{word[0]}'. "
                           f"Tap [ LEGEND ] for the full dot/dash table if unsure.")
        self._puzzle_title("MORSE CODE PUZZLE")
        self._puzzle_question("Decode the Morse code below (each letter separated by a space):")
        self._puzzle_display(encoded, size=18)
        self._puzzle_tip("Tip: '.' = dot, '-' = dash. Don't know the code? Tap [ LEGEND ] "
                          "for the FULL A-Z Morse table + a worked example.")

    def _build_hex_puzzle(self):
        word, encoded = PuzzleGenerator.make_hex_puzzle()
        self.current_answer = word
        self.hint_text = (f"Hex decode karo, {len(word)} letters ka word hai, first letter '{word[0]}'.")
        self._puzzle_title("HEX DECODE PUZZLE")
        self._puzzle_question("Convert each 2-digit hex pair below to a letter, and type the word:")
        self._puzzle_display(encoded, size=18)
        self._puzzle_tip("Tip: every 2 hex digits = 1 ASCII letter. Tap [ LEGEND ] for a reference table.")

    def _build_scramble_puzzle(self):
        word, scrambled = PuzzleGenerator.make_scramble_puzzle()
        self.current_answer = word
        self.hint_text = f"Letters ko sahi order mein jodo. First letter is '{word[0]}', {len(word)} letters total."
        self._puzzle_title("WORD SCRAMBLE PUZZLE")
        self._puzzle_question("Unscramble these letters into a real hacking-related word:")
        self._puzzle_display(scrambled)
        self._puzzle_tip("Tip: it's a common cybersecurity term (e.g. FIREWALL, SERVER, KERNEL...).")

    def _build_math_puzzle(self):
        seq, answer = PuzzleGenerator.make_math_puzzle()
        self.current_answer = answer
        self.hint_text = "Pattern dhoondo: arithmetic (+fixed amount), geometric (x fixed amount), ya squares ho sakta hai."
        self._puzzle_title("LOGIC SEQUENCE PUZZLE")
        self._puzzle_question("Find the pattern in this number sequence and type the NEXT number:")
        self._puzzle_display(" , ".join(str(n) for n in seq) + " , ?")
        self._puzzle_tip("Tip: check if it's +same amount, x same amount, or squares of consecutive numbers.")

    def _build_pattern_puzzle(self):
        seq, answer = PuzzleGenerator.make_pattern_puzzle()
        self.current_answer = answer
        self.hint_text = f"Yeh ek repeating cycle hai. Cycle ka agla symbol '{answer}' hai."
        self._puzzle_title("SYMBOL PATTERN PUZZLE")
        self._puzzle_question("These 4 symbols repeat in a fixed cycle. Type the NEXT symbol:")
        self._puzzle_display(" -> ".join(seq) + " -> ?")
        self._puzzle_tip("Tip: type it in ALL CAPS exactly, e.g. STAR, MOON, SUN, or BOLT.")

    # ---- Sudoku ----
    def _build_sudoku_room(self):
        blanks = {"Easy": 4, "Medium": 6, "Hard": 8, "Nightmare": 10}[self.player.difficulty]
        puzzle, solution = PuzzleGenerator.generate_sudoku4(blanks)
        self.sudoku_puzzle = puzzle
        self.sudoku_solution = solution
        self.current_answer = "".join(str(v) for v in solution[0])
        self.hint_text = f"Sudoku solve karke TOP ROW ke 4 digits password mein daalo (e.g. {self.current_answer})."

        self._puzzle_title("4x4 SUDOKU - SERVER LOCK")
        self._puzzle_question("Fill the grid so every row/column/2x2 box has 1-4 exactly once:")
        tk.Label(self.puzzle_frame,
                 text="Then type the TOP ROW's 4 digits (left to right, no spaces)\n"
                      "into the password box below and hit Submit.",
                 font=FONT_MONO, fg="#cccccc", bg=THEME["bg_panel"], justify="left").pack(pady=5)

        grid_frame = tk.Frame(self.puzzle_frame, bg=THEME["bg_panel"])
        grid_frame.pack(pady=10)
        self.sudoku_entries = []
        for r in range(4):
            row_entries = []
            for c in range(4):
                val = puzzle[r][c]
                e = tk.Entry(grid_frame, width=3, font=("Consolas", 16, "bold"),
                              justify="center", bg="#000000", fg=THEME["fg_primary"],
                              insertbackground=THEME["fg_primary"])
                if val != 0:
                    e.insert(0, str(val))
                    e.config(state="disabled", disabledforeground=THEME["fg_warning"],
                              disabledbackground="#001a00")
                e.grid(row=r, column=c, padx=3, pady=3)
                row_entries.append(e)
            self.sudoku_entries.append(row_entries)

        self._neon_button(self.puzzle_frame, "[ CHECK SUDOKU ]", THEME["fg_primary"],
                           self._check_sudoku, width=20).pack(pady=10)

    def _check_sudoku(self):
        grid = []
        for r in range(4):
            row = []
            for c in range(4):
                val = self.sudoku_entries[r][c].get()
                try:
                    row.append(int(val))
                except ValueError:
                    row.append(0)
            grid.append(row)
        if grid == self.sudoku_solution:
            messagebox.showinfo("Sudoku", "Sudoku solved! Ab top row ke digits ko password box mein submit karo.")
            self.player.add_coins(20)
            self._refresh_status_bar()
        else:
            messagebox.showwarning("Sudoku", "Abhi galat hai, dobara try karo.")

    # ---- Memory game ----
    def _build_memory_room(self):
        length = {"Easy": 3, "Medium": 4, "Hard": 5, "Nightmare": 6}[self.player.difficulty]
        sequence, colors = PuzzleGenerator.generate_memory_sequence(length)
        self.memory_sequence = sequence
        self.memory_colors = colors
        self.memory_player_progress = []
        self.current_answer = "MEMORY_OK"
        self.hint_text = "Colours ka pattern yaad rakho aur wahi order mein click karo, phir 'DONE' submit karo."

        self._puzzle_title("AI CONTROL - MEMORY GAME")
        self._puzzle_question("Watch the sequence, repeat it by clicking, then submit DONE:")
        tk.Label(self.puzzle_frame, text="1) Click 'SHOW SEQUENCE'\n2) Click the squares in the SAME order shown\n"
                                          "3) Once correct, password box auto-fills - just hit Submit",
                 font=FONT_MONO, fg="#cccccc", bg=THEME["bg_panel"], justify="left").pack(pady=5)

        canvas = tk.Canvas(self.puzzle_frame, width=320, height=100, bg=THEME["bg_panel"], highlightthickness=0)
        canvas.pack(pady=10)
        self.memory_canvas = canvas
        self.memory_squares = []
        for i, color in enumerate(colors):
            x0 = 10 + i * 78
            sq = canvas.create_rectangle(x0, 10, x0 + 65, 75, fill="#222222", outline="#555555", width=2)
            canvas.tag_bind(sq, "<Button-1>", lambda e, idx=i: self._memory_click(idx))
            self.memory_squares.append(sq)

        self.memory_status_label = tk.Label(self.puzzle_frame, text=f"Progress: 0/{len(sequence)}",
                                             font=FONT_MONO, fg=THEME["fg_warning"], bg=THEME["bg_panel"])
        self.memory_status_label.pack(pady=5)

        self._neon_button(self.puzzle_frame, "[ SHOW SEQUENCE ]", THEME["fg_primary"],
                           self._play_memory_sequence, width=20).pack(pady=10)

    def _play_memory_sequence(self):
        self.memory_player_progress = []
        self.memory_status_label.config(text="Watch carefully...")

        def flash(i):
            if i >= len(self.memory_sequence):
                self.memory_status_label.config(text=f"Progress: 0/{len(self.memory_sequence)} - your turn!")
                return
            color = self.memory_sequence[i]
            idx = self.memory_colors.index(color)
            sq = self.memory_squares[idx]
            self.memory_canvas.itemconfig(sq, fill=color)
            self.after(500, lambda: self.memory_canvas.itemconfig(sq, fill="#222222"))
            self.after(700, lambda: flash(i + 1))

        flash(0)

    def _memory_click(self, idx):
        if not self.memory_sequence:
            return
        color = self.memory_colors[idx]
        sq = self.memory_squares[idx]
        self.memory_canvas.itemconfig(sq, fill=color)
        self.after(200, lambda: self.memory_canvas.itemconfig(sq, fill="#222222"))

        pos = len(self.memory_player_progress)
        if pos >= len(self.memory_sequence):
            return
        self.memory_player_progress.append(color)
        if color != self.memory_sequence[pos]:
            self.memory_status_label.config(text="Wrong pattern! Try again.")
            self._wrong_answer()
            self.memory_player_progress = []
            return

        self.memory_status_label.config(
            text=f"Progress: {len(self.memory_player_progress)}/{len(self.memory_sequence)}")
        if len(self.memory_player_progress) == len(self.memory_sequence):
            self.memory_status_label.config(text="Sequence complete! Type DONE and submit.")
            self.current_answer = "DONE"

    # ---- Boss Fight ----
    def _build_boss_room(self):
        self.boss_max_health = {"Easy": 4, "Medium": 5, "Hard": 6, "Nightmare": 7}[self.player.difficulty]
        self.boss_health = self.boss_max_health
        self._puzzle_title("!!! AI SECURITY BOSS !!!")
        self._puzzle_question("Decode each round's puzzle and submit it to land a hit on the boss:")
        self.boss_bar = ttk.Progressbar(self.puzzle_frame, length=300, maximum=self.boss_max_health,
                                         value=self.boss_health)
        self.boss_bar.pack(pady=10)
        self.boss_health_label = tk.Label(self.puzzle_frame, text=f"Boss Health: {self.boss_health}/{self.boss_max_health}",
                                           font=FONT_MONO, fg=THEME["fg_danger"], bg=THEME["bg_panel"])
        self.boss_health_label.pack(pady=5)
        tk.Label(self.puzzle_frame, text="Har sahi jawab boss ko hit karega.\nHar galat jawab tumhe hit karega!\n"
                                          "Confused ho? [ LEGEND ] button dabao.",
                 font=FONT_MONO, fg="#cccccc", bg=THEME["bg_panel"], justify="center").pack(pady=5)
        self._next_boss_round()

    def _next_boss_round(self):
        if hasattr(self, "boss_round_frame") and self.boss_round_frame.winfo_exists():
            self.boss_round_frame.destroy()
        self.boss_round_frame = tk.Frame(self.puzzle_frame, bg=THEME["bg_panel"])
        self.boss_round_frame.pack(pady=10)

        kind = random.choice(["rot13", "binary", "caesar", "morse", "hex"])
        if kind == "rot13":
            word, enc = PuzzleGenerator.make_rot13_puzzle()
            display = f"ROT13: {enc}"
            self.current_shift = None
        elif kind == "binary":
            word, enc = PuzzleGenerator.make_binary_puzzle()
            display = f"BINARY: {enc}"
            self.current_shift = None
        elif kind == "caesar":
            word, enc, shift = PuzzleGenerator.make_caesar_puzzle()
            display = f"CAESAR (shift={shift}): {enc}"
            self.current_shift = shift
        elif kind == "morse":
            word, enc = PuzzleGenerator.make_morse_puzzle()
            display = f"MORSE: {enc}"
            self.current_shift = None
        else:
            word, enc = PuzzleGenerator.make_hex_puzzle()
            display = f"HEX: {enc}"
            self.current_shift = None

        self.current_answer = word
        self.current_ptype = kind
        self.hint_text = (f"Boss round - decode the {kind.upper()} text below and submit the plain word "
                           f"({len(word)} letters, starts with '{word[0]}').")
        tk.Label(self.boss_round_frame, text=f"Round type: {kind.upper()}", font=FONT_MONO_SMALL,
                 fg=THEME["fg_accent"], bg=THEME["bg_panel"]).pack()
        tk.Label(self.boss_round_frame, text=display, font=("Consolas", 16, "bold"),
                 fg=THEME["fg_warning"], bg=THEME["bg_panel"], wraplength=350).pack(pady=10)

    def _build_final_room(self):
        word, encoded, shift = PuzzleGenerator.make_caesar_puzzle()
        self.current_answer = word
        self.current_shift = shift
        self.hint_text = (f"Caesar shift = {shift}. Har letter ko {shift} places peeche shift karo. "
                           f"Answer has {len(word)} letters, starts with '{word[0]}'.")

        self._puzzle_title("MAIN SERVER - FINAL LOCK")
        self._puzzle_question(f"Shift every letter below BACKWARD by {shift} to decode the final passcode:")
        self._puzzle_display(encoded)
        tk.Label(self.puzzle_frame, text="Yeh solve karte hi tum MAIN SERVER unlock\nkarke ESCAPE kar jaoge!",
                 font=FONT_MONO, fg=THEME["fg_accent"], bg=THEME["bg_panel"], justify="left").pack(pady=10)

    # ================================================================
    #  SUBMIT / ANSWER CHECKING
    # ================================================================
    def _submit_password(self):
        if time.time() < self.door_locked_until:
            remaining = int(self.door_locked_until - time.time()) + 1
            messagebox.showwarning("Locked", f"AI ne door lock kar rakha hai! Wait {remaining}s.")
            return

        entered = self.password_entry.get().strip().upper()
        expected = str(self.current_answer).strip().upper()
        room_type = ROOMS[self.player.current_room_index]["type"]

        if entered == expected:
            if room_type == "boss":
                self._boss_hit()
            else:
                self._correct_answer()
        else:
            self._wrong_answer()

        self.password_entry.delete(0, "end")
        self._update_strength_meter()

    def _boss_hit(self):
        self.sound.beep_boss_hit()
        self.boss_health -= 1
        self.boss_bar.config(value=self.boss_health)
        self.boss_health_label.config(text=f"Boss Health: {max(0, self.boss_health)}/{self.boss_max_health}")
        self._term_print("Boss hit! Security weakened...")
        if self.boss_health <= 0:
            self.player.boss_defeated = True
            self.player.score += 200
            self.sound.beep_level_up()
            messagebox.showinfo("Boss Defeated!", "AI Security Boss down! Main Server ab reachable hai.")
            self._advance_room(reward=False, already_rewarded=True)
        else:
            self._next_boss_round()

    def _correct_answer(self):
        self.sound.beep_ok()
        self._advance_room(reward=True)

    def _advance_room(self, reward=True, already_rewarded=False):
        """Central place that moves the player to the next room. `reward`
        controls whether coins/score/time-bonus/items are granted - the
        Answer Key path calls this with reward=False so it truly only
        levels you up."""
        if reward:
            coin_reward = random.randint(15, 30)
            self.player.add_coins(coin_reward)
            self.player.score += 100
            time_bonus = ROOM_CLEAR_TIME_BONUS.get(self.player.difficulty, 10)
            self.player.time_left += time_bonus
            self._term_print(f"Password accepted. +{coin_reward} coins, +{time_bonus}s time. Door opening...")
            self.sound.beep_level_up()
            self._maybe_award_item()
        elif not already_rewarded:
            self._term_print("Room cleared via Answer Key - no coins/score/time bonus this time.")

        self._refresh_status_bar()

        next_room = self.player.current_room_index + 1
        if next_room >= len(ROOMS):
            self._end_game(won=True)
        else:
            if reward:
                messagebox.showinfo("Access Granted", f"Correct! Moving to {ROOMS[next_room]['name']}.")
            self.show_room(next_room)

    def _wrong_answer(self):
        self.sound.beep_wrong()
        self._term_print("ACCESS DENIED. Wrong password!")
        dead = self.player.lose_heart(1)
        if not self.player.shield_active:
            self._term_print("-1 Health")
        else:
            self._term_print("Shield absorbed the damage!")
        self._refresh_status_bar()
        if dead:
            self._end_game(won=False)

# =============================================================================
#  ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = HackerEscapeApp()
    app.mainloop()