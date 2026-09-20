import os
import sys
import json
import random
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
th = gd = sm = sys.modules[__name__]

# =============================================================================
# THEME
# =============================================================================

BG = "#0a0e0a"            # main background
BG_PANEL = "#10160f"      # card / panel background
BG_PANEL_2 = "#151d14"    # slightly lighter panel (hover/alt row)
BORDER = "#1f3320"

NEON_GREEN = "#39ff6a"
NEON_GREEN_DIM = "#1fae4a"
NEON_CYAN = "#33e0ff"
NEON_PINK = "#ff4fd8"
NEON_YELLOW = "#ffe14f"
RED = "#ff4b4b"
GREY = "#8a9a8a"
WHITE = "#eafff0"

FONT_FAMILY = "Consolas"
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)
FONT_BOLD = (FONT_FAMILY, 10, "bold")
FONT_HEADER = (FONT_FAMILY, 16, "bold")
FONT_SUBHEADER = (FONT_FAMILY, 12, "bold")
FONT_STAT = (FONT_FAMILY, 13, "bold")
FONT_MONEY = (FONT_FAMILY, 20, "bold")
FONT_ICON = (FONT_FAMILY, 18)


def style_button(btn, accent=NEON_GREEN, big=False):
    btn.configure(
        bg=BG_PANEL_2, fg=accent, activebackground=accent, activeforeground=BG,
        relief="flat", bd=0, cursor="hand2",
        font=FONT_BOLD if not big else (FONT_FAMILY, 12, "bold"),
        highlightthickness=1, highlightbackground=accent, highlightcolor=accent,
        padx=10, pady=6,
    )

    def on_enter(e):
        btn.configure(bg=accent, fg=BG)

    def on_leave(e):
        btn.configure(bg=BG_PANEL_2, fg=accent)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


# =============================================================================
# GAME DATA
# =============================================================================
"""
Static game data / config for Shadow Market: Rise to Billionaire.
"""

# ---------------------------------------------------------------------------
# BUSINESS TYPES
# ---------------------------------------------------------------------------

BUSINESS_TYPES = [
    {
        "key": "food_stall",
        "name": "Food Stall",
        "icon": "\U0001F35C",
        "cost": 8_000,
        "base_profit": 500,
        "risk": 0.05,
        "growth": 1.15,
        "upgrade_cost": 4_000,
        "desc": "Low risk, slow and steady street food business.",
    },
    {
        "key": "tea_shop",
        "name": "Tea Shop",
        "icon": "\U0001F375",
        "cost": 5_000,
        "base_profit": 300,
        "risk": 0.04,
        "growth": 1.12,
        "upgrade_cost": 2_500,
        "desc": "Cheapest way to start. Small but reliable income.",
    },
    {
        "key": "freelancing",
        "name": "Freelancing",
        "icon": "\U0001F4BB",
        "cost": 2_000,
        "base_profit": 800,
        "risk": 0.10,
        "growth": 1.10,
        "upgrade_cost": 1_500,
        "desc": "Sell your skills online. Depends on your energy.",
    },
    {
        "key": "online_store",
        "name": "Online Store",
        "icon": "\U0001F6D2",
        "cost": 25_000,
        "base_profit": 2_200,
        "risk": 0.12,
        "growth": 1.18,
        "upgrade_cost": 12_000,
        "desc": "E-commerce. Good growth, medium risk.",
    },
    {
        "key": "youtube",
        "name": "YouTube Channel",
        "icon": "\U0001F3A5",
        "cost": 15_000,
        "base_profit": 1_500,
        "risk": 0.15,
        "growth": 1.20,
        "upgrade_cost": 8_000,
        "desc": "Views and followers boost your reputation too.",
    },
    {
        "key": "app_dev",
        "name": "App Development",
        "icon": "\U0001F4F1",
        "cost": 1_50_000,
        "base_profit": 9_000,
        "risk": 0.18,
        "growth": 1.25,
        "upgrade_cost": 60_000,
        "desc": "Build apps. High skill requirement, high reward.",
    },
    {
        "key": "software_company",
        "name": "Software Company",
        "icon": "\U0001F5A5\uFE0F",
        "cost": 10_00_000,
        "base_profit": 80_000,
        "risk": 0.15,
        "growth": 1.3,
        "upgrade_cost": 5_00_000,
        "desc": "Hire developers, sell software. Very high growth.",
    },
    {
        "key": "real_estate_firm",
        "name": "Real Estate Firm",
        "icon": "\U0001F3E2",
        "cost": 50_00_000,
        "base_profit": 3_00_000,
        "risk": 0.10,
        "growth": 1.2,
        "upgrade_cost": 20_00_000,
        "desc": "Buy, sell and rent property empires.",
    },
    {
        "key": "ai_company",
        "name": "AI Company",
        "icon": "\U0001F916",
        "cost": 50_00_00_000,
        "base_profit": 40_00_000,
        "risk": 0.20,
        "growth": 1.4,
        "upgrade_cost": 20_00_00_000,
        "desc": "The final frontier. Unlimited profit potential.",
    },
]

# ---------------------------------------------------------------------------
# STOCK MARKET
# ---------------------------------------------------------------------------
STOCKS = [
    {"symbol": "TSLA", "name": "Tesla", "price": 1200.0, "volatility": 0.03},
    {"symbol": "GOOG", "name": "Google", "price": 890.0, "volatility": 0.02},
    {"symbol": "AAPL", "name": "Apple", "price": 1600.0, "volatility": 0.02},
    {"symbol": "NVDA", "name": "NVIDIA", "price": 2900.0, "volatility": 0.045},
    {"symbol": "AMZN", "name": "Amazon", "price": 1450.0, "volatility": 0.025},
    {"symbol": "MSFT", "name": "Microsoft", "price": 980.0, "volatility": 0.018},
    {"symbol": "GOLD", "name": "Gold ETF", "price": 610.0, "volatility": 0.01},
    {"symbol": "BTC", "name": "Bitcoin", "price": 34_00_000.0, "volatility": 0.06},
]

# ---------------------------------------------------------------------------
# EMPLOYEE POOL
# ---------------------------------------------------------------------------
FIRST_NAMES = ["Aarav", "Vivaan", "Isha", "Meera", "Rohan", "Kabir", "Ananya",
               "Diya", "Aditya", "Sara", "Arjun", "Neha", "Karan", "Priya",
               "Yash", "Tanya", "Dev", "Riya", "Zoya", "Ishaan"]

PERSONALITIES = ["Lazy", "Smart", "Genius", "Thief", "Loyal", "Funny", "Aggressive"]

ROLES = [
    {"role": "Developer", "base_salary": 30_000, "skill_range": (40, 99)},
    {"role": "Marketer", "base_salary": 20_000, "skill_range": (35, 90)},
    {"role": "Manager", "base_salary": 35_000, "skill_range": (45, 95)},
    {"role": "Support Staff", "base_salary": 12_000, "skill_range": (30, 80)},
    {"role": "Designer", "base_salary": 22_000, "skill_range": (40, 92)},
]


def generate_employee():
    role = random.choice(ROLES)
    skill = random.randint(*role["skill_range"])
    personality = random.choice(PERSONALITIES)
    name = random.choice(FIRST_NAMES)
    salary = int(role["base_salary"] * (0.7 + skill / 100))
    return {
        "name": name,
        "role": role["role"],
        "skill": skill,
        "personality": personality,
        "salary": salary,
        "mood": random.randint(60, 100),
        "experience": 0,
        "loyal": personality == "Loyal",
    }


# ---------------------------------------------------------------------------
# WORLD EVENTS
# ---------------------------------------------------------------------------
WORLD_EVENTS = [
    {
        "name": "Global Pandemic",
        "text": "A pandemic sweeps the world! Foot-traffic businesses suffer.",
        "effect": "pandemic",
    },
    {
        "name": "Flood",
        "text": "Heavy floods damage local businesses in your city.",
        "effect": "flood",
    },
    {
        "name": "War Tensions",
        "text": "Geopolitical tensions rattle global markets.",
        "effect": "war",
    },
    {
        "name": "Earthquake",
        "text": "An earthquake disrupts operations for many companies.",
        "effect": "earthquake",
    },
    {
        "name": "Recession",
        "text": "The economy slips into recession. Spending drops.",
        "effect": "recession",
    },
    {
        "name": "Oil Price Surge",
        "text": "Oil prices spike, raising costs everywhere.",
        "effect": "oil",
    },
    {
        "name": "AI Revolution",
        "text": "A new AI breakthrough boosts tech stocks massively!",
        "effect": "ai_boom",
    },
    {
        "name": "Market Rally",
        "text": "Investor confidence soars. Stocks are up across the board!",
        "effect": "rally",
    },
    {
        "name": "Viral Trend",
        "text": "Something you did went viral! Followers are pouring in.",
        "effect": "viral",
    },
    {
        "name": "Tax Audit",
        "text": "The government is auditing businesses this quarter.",
        "effect": "audit",
    },
]

# ---------------------------------------------------------------------------
# ACHIEVEMENTS  (key, name, condition description used by engine)
# ---------------------------------------------------------------------------
ACHIEVEMENTS = [
    {"key": "first_lakh", "name": "First \u20B91 Lakh", "desc": "Reach \u20B91,00,000 net worth."},
    {"key": "first_business", "name": "First Company", "desc": "Start your first business."},
    {"key": "first_employee", "name": "First Employee", "desc": "Hire your first employee."},
    {"key": "hundred_employees", "name": "100 Employees", "desc": "Employ 100 people."},
    {"key": "millionaire", "name": "Millionaire", "desc": "Reach \u20B91,00,00,000 net worth."},
    {"key": "billionaire", "name": "Billionaire", "desc": "Reach \u20B9100,00,00,000 net worth."},
    {"key": "trillionaire", "name": "Trillionaire", "desc": "Reach \u20B91,00,000 Crore net worth."},
    {"key": "first_stock", "name": "Market Player", "desc": "Buy your first stock."},
    {"key": "survivor", "name": "Survivor", "desc": "Survive your first world event."},
    {"key": "loan_free", "name": "Debt Free", "desc": "Fully pay off a bank loan."},
]

# ---------------------------------------------------------------------------
# NEWS HEADLINE POOL (flavor, shown in ticker regardless of events)
# ---------------------------------------------------------------------------
FLAVOR_NEWS = [
    "Gold price increased amid global uncertainty",
    "Startup founders raise record funding this quarter",
    "New tax policy proposed for small businesses",
    "Tech layoffs continue across major firms",
    "Local entrepreneur donates to city hospital",
    "Cryptocurrency prices swing wildly overnight",
    "Interest rates expected to change next month",
    "Consumer spending hits a new seasonal high",
    "Electric vehicle sales overtake petrol cars in region",
    "Remote work reshapes the office real estate market",
]

# ---------------------------------------------------------------------------
# GAMEPLAY HINTS (shown as rotating tips, e.g. on the stock market screen)
# ---------------------------------------------------------------------------
GAME_HINTS = [
    "Tip: Diversify — don't put all your money into one stock.",
    "Tip: Gold and low-volatility stocks are safer during a recession.",
    "Tip: Upgrading a business raises its daily profit but costs more each time.",
    "Tip: Employees with high mood and skill boost every business's profit.",
    "Tip: 'Thief' personality employees can steal from you — watch their mood.",
    "Tip: Taking a loan hurts your credit score a little, but paying EMIs on time helps it recover.",
    "Tip: Fixed Deposits are a safe way to grow idle cash over time.",
    "Tip: World events can help or hurt you — tech stocks love an AI boom!",
    "Tip: Check the Ledger screen to see exactly what you earned and spent each day.",
    "Tip: Your net worth includes businesses, stocks, FDs and bank balance minus loans.",
]

# =============================================================================
# SOUND ENGINE (in-memory synthesis)
# =============================================================================

SR = 44100

try:
    import numpy as np
    import pygame
    pygame.mixer.init(frequency=SR, size=-16, channels=2)
    _AUDIO_OK = True
except Exception:
    _AUDIO_OK = False

_SOUNDS = {}
_AMBIENT_SOUND = None
_AMBIENT_CHANNEL = None


def _env(n, attack=0.02, release=0.25):
    env = np.ones(n)
    a = min(int(SR * attack), n // 2)
    r = min(int(SR * release), n // 2)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if r > 0:
        env[-r:] = np.linspace(1, 0, r)
    return env


def _tone(freq, dur, vol=0.4, wave_type="sine", fade=True):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, False)
    if wave_type == "square":
        w = np.sign(np.sin(freq * 2 * np.pi * t))
    else:
        w = np.sin(freq * 2 * np.pi * t)
    if fade:
        w = w * _env(n)
    return w * vol


def _chord(freqs, dur, vol=0.3):
    n = int(SR * dur)
    out = np.zeros(n)
    for f in freqs:
        out += _tone(f, dur, vol=1.0, fade=False)[:n]
    out = (out / max(1, len(freqs))) * _env(n) * vol
    return out


def _sweep(f_start, f_end, dur, vol=0.35, attack=0.01, release=0.2):
    n = int(SR * dur)
    freq_path = np.linspace(f_start, f_end, n)
    w = np.sin(2 * np.pi * np.cumsum(freq_path) / SR)
    return w * _env(n, attack, release) * vol


def _silence(dur):
    return np.zeros(int(SR * dur))


def _to_sound(mono_array):
    """Convert a float numpy array in [-1, 1] into a pygame Sound (in memory)."""
    mono_array = np.clip(mono_array, -1, 1)
    data = (mono_array * 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack([data, data]))
    return pygame.sndarray.make_sound(stereo)


def _build_all_sounds():
    """Synthesize every sound effect used by the game, once, at startup."""
    if not _AUDIO_OK:
        # numpy/pygame not available (or no audio device) - skip synthesis
        # entirely so the game still runs fine, just silently.
        return
    defs = {}
    defs["click"] = _tone(1200, 0.045, vol=0.25, wave_type="square")
    defs["coin"] = np.concatenate([_tone(880, 0.08, vol=0.35), _tone(1320, 0.12, vol=0.35)])
    defs["error"] = _sweep(300, 120, 0.35, vol=0.35, release=0.2)
    defs["notify"] = np.concatenate([_tone(660, 0.12, vol=0.3), _silence(0.03), _tone(990, 0.18, vol=0.3)])
    defs["event"] = np.concatenate([
        _tone(520, 0.1, vol=0.35, wave_type="square"), _silence(0.05),
        _tone(520, 0.1, vol=0.35, wave_type="square"),
    ])
    defs["achievement"] = np.concatenate([
        _tone(523.25, 0.12, vol=0.3), _tone(659.25, 0.12, vol=0.3),
        _tone(783.99, 0.12, vol=0.3), _chord([1046.5, 1318.5, 1568.0], 0.35, vol=0.35),
    ])
    defs["levelup"] = np.concatenate([
        _tone(440, 0.09, vol=0.3), _tone(554.37, 0.09, vol=0.3), _tone(659.25, 0.16, vol=0.35),
    ])
    defs["tick"] = _tone(700, 0.05, vol=0.18)
    defs["buy"] = np.concatenate([_tone(700, 0.06, vol=0.28), _tone(1000, 0.08, vol=0.28)])
    defs["sell"] = np.concatenate([_tone(1000, 0.06, vol=0.28), _tone(700, 0.08, vol=0.28)])
    defs["fanfare"] = np.concatenate([
        _chord([523.25, 659.25, 783.99], 0.25, vol=0.35),
        _chord([587.33, 739.99, 880.0], 0.25, vol=0.35),
        _chord([659.25, 830.61, 987.77], 0.5, vol=0.4),
    ])
    defs["gameover"] = _sweep(220, 60, 0.9, vol=0.4, attack=0.02, release=0.5)

    global _AMBIENT_SOUND
    dur = 4.0
    n = int(SR * dur)
    t = np.linspace(0, dur, n, False)
    bg = 0.05 * np.sin(2 * np.pi * 110 * t) + 0.03 * np.sin(2 * np.pi * 164.8 * t)
    bg *= _env(n, 0.5, 0.5)

    if _AUDIO_OK:
        for name, arr in defs.items():
            try:
                _SOUNDS[name] = _to_sound(arr)
            except Exception:
                _SOUNDS[name] = None
        try:
            _AMBIENT_SOUND = _to_sound(bg)
        except Exception:
            _AMBIENT_SOUND = None


def play(name, sound_on=True):
    """Play a synthesized sound effect by name (e.g. play('coin'))."""
    if not sound_on or not _AUDIO_OK:
        return
    snd = _SOUNDS.get(name)
    if snd is not None:
        try:
            snd.play()
        except Exception:
            pass


def start_ambient(music_on=True):
    global _AMBIENT_CHANNEL
    if not _AUDIO_OK or not music_on or _AMBIENT_SOUND is None:
        return
    try:
        _AMBIENT_CHANNEL = _AMBIENT_SOUND.play(loops=-1)
        if _AMBIENT_CHANNEL:
            _AMBIENT_CHANNEL.set_volume(0.35)
    except Exception:
        pass


def stop_ambient():
    if _AUDIO_OK and _AMBIENT_CHANNEL is not None:
        try:
            _AMBIENT_CHANNEL.stop()
        except Exception:
            pass


def set_ambient_enabled(on):
    if on:
        start_ambient(True)
    else:
        stop_ambient()


_build_all_sounds()



# =============================================================================
# GAME ENGINE
# =============================================================================
"""
Core game engine for Shadow Market: Rise to Billionaire.
No GUI code here — pure game state & logic so it's easy to test/extend.
"""


SAVE_DIR = os.path.dirname(__file__)
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")
USERS_FILE = os.path.join(SAVE_DIR, "users.json")


def fmt_money(amount):
    """Format a rupee amount in Indian-style grouping with a symbol."""
    amount = int(round(amount))
    neg = amount < 0
    amount = abs(amount)
    s = str(amount)
    if len(s) <= 3:
        grouped = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        grouped = ",".join(parts) + "," + last3
    return ("-\u20B9" if neg else "\u20B9") + grouped


class Business:
    def __init__(self, key, level=1):
        self.key = key
        self.level = level
        self.total_invested = 0
        self.days_owned = 0

    @property
    def spec(self):
        for b in gd.BUSINESS_TYPES:
            if b["key"] == self.key:
                return b
        return None

    def daily_profit(self, multiplier=1.0):
        spec = self.spec
        base = spec["base_profit"] * (spec["growth"] ** (self.level - 1))
        return base * multiplier

    def to_dict(self):
        return {"key": self.key, "level": self.level,
                "total_invested": self.total_invested, "days_owned": self.days_owned}

    @staticmethod
    def from_dict(d):
        b = Business(d["key"], d["level"])
        b.total_invested = d.get("total_invested", 0)
        b.days_owned = d.get("days_owned", 0)
        return b


class Employee:
    def __init__(self, data):
        self.data = dict(data)

    def to_dict(self):
        return self.data

    @staticmethod
    def from_dict(d):
        return Employee(d)


class Stock(dict):
    """Live stock, tracks current price + history."""
    pass


class GameState:
    def __init__(self):
        self.year = 2026
        self.day = 1
        self.age = 18
        self.money = 10_000
        self.bank_balance = 0
        self.health = 100
        self.stress = 5
        self.energy = 100
        self.followers = 0
        self.reputation = 0  # -100..100
        self.credit_score = 650

        self.businesses = []          # list[Business]
        self.employees = []           # list[Employee]
        self.portfolio = {}           # symbol -> qty
        self.loans = []               # list of dicts: principal, rate, remaining, emi
        self.fixed_deposits = []      # list of dicts: amount, rate, days_left
        self.had_loan = False         # tracks whether a loan was ever taken (for achievements)

        self.stocks = [dict(s) for s in gd.STOCKS]  # live copies
        for s in self.stocks:
            s["history"] = [s["price"]]

        self.achievements_unlocked = set()
        self.net_worth_history = [self.money]
        self.money_history = [self.money]
        self.business_profit_history = [0]
        self.portfolio_value_history = [0]
        self.followers_history = [0]
        self.networth_by_year = {}
        self.ledger = []              # list of dicts: day, year, income, expense, net
        self.news_log = []
        self.event_log = []
        self.game_over = False
        self.game_over_reason = None

        self.sound_on = True
        self.music_on = True

    # ------------------------------------------------------------------
    # NET WORTH / STATS
    # ------------------------------------------------------------------
    def net_worth(self):
        total = self.money + self.bank_balance
        for b in self.businesses:
            spec = b.spec
            total += spec["cost"] * 0.6 * b.level  # rough asset value
        for fd in self.fixed_deposits:
            total += fd["amount"]
        for sym, qty in self.portfolio.items():
            stock = self._find_stock(sym)
            if stock:
                total += stock["price"] * qty
        for loan in self.loans:
            total -= loan["remaining"]
        return total

    def portfolio_value(self):
        total = 0
        for sym, qty in self.portfolio.items():
            stock = self._find_stock(sym)
            if stock:
                total += stock["price"] * qty
        return total

    def _find_stock(self, symbol):
        for s in self.stocks:
            if s["symbol"] == symbol:
                return s
        return None

    # ------------------------------------------------------------------
    # BUSINESS
    # ------------------------------------------------------------------
    def start_business(self, key):
        spec = next(b for b in gd.BUSINESS_TYPES if b["key"] == key)
        if self.money < spec["cost"]:
            return False, "Not enough money to start this business."
        self.money -= spec["cost"]
        biz = Business(key)
        biz.total_invested = spec["cost"]
        self.businesses.append(biz)
        return True, f"Started {spec['name']}!"

    def upgrade_business(self, index):
        if index < 0 or index >= len(self.businesses):
            return False, "Invalid business."
        biz = self.businesses[index]
        spec = biz.spec
        cost = int(spec["upgrade_cost"] * (1.25 ** (biz.level - 1)))
        if self.money < cost:
            return False, "Not enough money to upgrade."
        self.money -= cost
        biz.level += 1
        biz.total_invested += cost
        return True, f"{spec['name']} upgraded to level {biz.level}!"

    def close_business(self, index):
        if index < 0 or index >= len(self.businesses):
            return False, "Invalid business."
        biz = self.businesses.pop(index)
        refund = int(biz.spec["cost"] * 0.3 * biz.level)
        self.money += refund
        return True, f"Closed {biz.spec['name']}, recovered {fmt_money(refund)}."

    def employee_multiplier(self):
        """Employees boost business profit slightly based on avg skill/mood."""
        if not self.employees:
            return 1.0
        avg = sum(e.data["skill"] * (e.data["mood"] / 100) for e in self.employees) / len(self.employees)
        return 1.0 + min(0.6, avg / 200)

    # ------------------------------------------------------------------
    # EMPLOYEES
    # ------------------------------------------------------------------
    def hire_pool(self, n=3):
        return [gd.generate_employee() for _ in range(n)]

    def hire_employee(self, emp_data):
        self.employees.append(Employee(emp_data))

    def fire_employee(self, index):
        if 0 <= index < len(self.employees):
            self.employees.pop(index)

    def pay_salaries(self):
        total = sum(e.data["salary"] for e in self.employees)
        self.money -= total
        return total

    # ------------------------------------------------------------------
    # STOCK MARKET
    # ------------------------------------------------------------------
    def tick_stocks(self):
        for s in self.stocks:
            vol = s["volatility"]
            change = random.gauss(0, vol)
            s["price"] = max(1.0, s["price"] * (1 + change))
            s["history"].append(s["price"])
            if len(s["history"]) > 60:
                s["history"] = s["history"][-60:]

    def buy_stock(self, symbol, qty):
        stock = self._find_stock(symbol)
        cost = stock["price"] * qty
        if self.money < cost:
            return False, "Not enough money."
        self.money -= cost
        self.portfolio[symbol] = self.portfolio.get(symbol, 0) + qty
        return True, f"Bought {qty} {symbol} for {fmt_money(cost)}."

    def sell_stock(self, symbol, qty):
        have = self.portfolio.get(symbol, 0)
        if have < qty:
            return False, "You don't own that many shares."
        stock = self._find_stock(symbol)
        proceeds = stock["price"] * qty
        self.portfolio[symbol] -= qty
        if self.portfolio[symbol] <= 0:
            del self.portfolio[symbol]
        self.money += proceeds
        return True, f"Sold {qty} {symbol} for {fmt_money(proceeds)}."

    # ------------------------------------------------------------------
    # BANK
    # ------------------------------------------------------------------
    def take_loan(self, amount, rate=0.12, term_days=60):
        if amount <= 0:
            return False, "Invalid amount."
        emi = round(amount * (1 + rate) / term_days, 2)
        self.loans.append({
            "principal": amount, "remaining": amount * (1 + rate),
            "rate": rate, "emi": emi, "days_left": term_days,
        })
        self.money += amount
        self.credit_score = max(300, self.credit_score - 5)
        self.had_loan = True
        return True, f"Loan of {fmt_money(amount)} approved."

    def pay_emis(self):
        paid_total = 0
        cleared = []
        for loan in self.loans:
            emi = min(loan["emi"], loan["remaining"])
            if self.money >= emi:
                self.money -= emi
                loan["remaining"] -= emi
                loan["days_left"] -= 1
                paid_total += emi
                self.credit_score = min(900, self.credit_score + 1)
            else:
                self.credit_score = max(300, self.credit_score - 3)
            if loan["remaining"] <= 1:
                cleared.append(loan)
        for c in cleared:
            self.loans.remove(c)
        return paid_total, len(cleared)

    def open_fd(self, amount, rate=0.08, days=90):
        if self.money < amount:
            return False, "Not enough money."
        self.money -= amount
        self.fixed_deposits.append({"amount": amount, "rate": rate, "days_left": days, "start": amount})
        return True, f"Opened FD of {fmt_money(amount)}."

    def mature_fds(self):
        matured = []
        for fd in self.fixed_deposits:
            fd["days_left"] -= 1
            if fd["days_left"] <= 0:
                payout = fd["start"] * (1 + fd["rate"])
                self.money += payout
                matured.append(fd)
        for m in matured:
            self.fixed_deposits.remove(m)
        return matured

    # ------------------------------------------------------------------
    # DAILY TICK — call once per in-game day
    # ------------------------------------------------------------------
    def advance_day(self):
        self.day += 1
        if self.day > 365:
            self.day = 1
            self.year += 1
            if self.year % 1 == 0:  # every year
                self.age += 1

        mult = self.employee_multiplier()
        profit_today = 0
        events_today = []
        for biz in self.businesses:
            biz.days_owned += 1
            p = biz.daily_profit(mult)
            if random.random() < biz.spec["risk"]:
                loss = p * random.uniform(0.3, 1.0)
                p -= loss
                events_today.append(f"{biz.spec['name']} had a rough day (-{fmt_money(loss)}).")
            profit_today += p
        self.money += profit_today

        salary_paid = self.pay_salaries()
        emi_paid, cleared_loans = self.pay_emis()
        self.mature_fds()

        # mood/energy drift
        self.energy = max(10, min(100, self.energy - random.randint(1, 5) + (3 if self.businesses == [] else 0)))
        self.stress = max(0, min(100, self.stress + (2 if profit_today < 0 else -1) + random.randint(-1, 2)))
        self.health = max(0, min(100, self.health - (2 if self.stress > 70 else 0) + (1 if self.energy > 60 else 0)))

        for e in self.employees:
            e.data["experience"] += 1
            drift = random.randint(-4, 4)
            e.data["mood"] = max(0, min(100, e.data["mood"] + drift))
            if e.data["personality"] == "Thief" and random.random() < 0.03:
                stolen = random.randint(500, 5000)
                self.money -= stolen
                events_today.append(f"{e.data['name']} (Thief) stole {fmt_money(stolen)}!")

        self.tick_stocks()

        # ---- history tracking for the multi-graph home screen ----
        self.net_worth_history.append(self.net_worth())
        self.money_history.append(self.money)
        self.business_profit_history.append(profit_today)
        self.portfolio_value_history.append(self.portfolio_value())
        self.followers_history.append(self.followers)
        for hist in (self.net_worth_history, self.money_history, self.business_profit_history,
                     self.portfolio_value_history, self.followers_history):
            if len(hist) > 200:
                del hist[:len(hist) - 200]

        # ---- daily income/expense ledger ----
        income = max(0.0, profit_today)
        expense = salary_paid + emi_paid + max(0.0, -profit_today)
        self.ledger.append({
            "day": self.day, "year": self.year,
            "income": income, "expense": expense, "net": income - expense,
        })
        if len(self.ledger) > 365:
            del self.ledger[:len(self.ledger) - 365]

        # ---- net worth by year, for the leaderboard ----
        self.networth_by_year[str(self.year)] = self.net_worth()

        if self.money < 0 and self.net_worth() < -50000:
            self.game_over = True
            self.game_over_reason = "bankrupt"

        return {
            "profit": profit_today,
            "salary": salary_paid,
            "emi": emi_paid,
            "cleared_loans": cleared_loans,
            "events": events_today,
        }

    # ------------------------------------------------------------------
    # WORLD EVENTS
    # ------------------------------------------------------------------
    def trigger_random_event(self):
        event = random.choice(gd.WORLD_EVENTS)
        effect = event["effect"]
        impact_lines = []

        if effect == "pandemic":
            for b in self.businesses:
                if b.key in ("food_stall", "tea_shop"):
                    loss = int(b.daily_profit() * 3)
                    self.money -= loss
                    impact_lines.append(f"{b.spec['name']} lost {fmt_money(loss)}.")
        elif effect == "flood":
            if self.businesses:
                b = random.choice(self.businesses)
                loss = int(b.daily_profit() * 4)
                self.money -= loss
                impact_lines.append(f"{b.spec['name']} lost {fmt_money(loss)}.")
        elif effect == "war":
            for s in self.stocks:
                s["price"] *= random.uniform(0.85, 0.95)
            impact_lines.append("Global stocks dipped.")
        elif effect == "earthquake":
            if self.businesses:
                b = random.choice(self.businesses)
                loss = int(b.spec["cost"] * 0.1)
                self.money -= loss
                impact_lines.append(f"{b.spec['name']} repair cost {fmt_money(loss)}.")
        elif effect == "recession":
            for s in self.stocks:
                s["price"] *= random.uniform(0.9, 0.98)
            impact_lines.append("Market-wide slowdown.")
        elif effect == "oil":
            for b in self.businesses:
                loss = int(b.daily_profit() * 0.5)
                self.money -= loss
            impact_lines.append("Operating costs rose everywhere.")
        elif effect == "ai_boom":
            for s in self.stocks:
                if s["symbol"] in ("NVDA", "GOOG", "MSFT"):
                    s["price"] *= random.uniform(1.08, 1.20)
            impact_lines.append("Tech stocks surged!")
        elif effect == "rally":
            for s in self.stocks:
                s["price"] *= random.uniform(1.02, 1.08)
            impact_lines.append("All stocks are up.")
        elif effect == "viral":
            gain = random.randint(500, 5000)
            self.followers += gain
            self.reputation = min(100, self.reputation + 5)
            impact_lines.append(f"+{gain} followers, reputation up.")
        elif effect == "audit":
            if self.money > 0:
                fine = int(self.money * random.uniform(0.01, 0.05))
                self.money -= fine
                impact_lines.append(f"Tax fine: {fmt_money(fine)}.")

        entry = {"name": event["name"], "text": event["text"], "impact": impact_lines}
        self.event_log.insert(0, entry)
        self.event_log = self.event_log[:30]
        self.check_achievement("survivor")
        return entry

    def push_news(self, headline):
        self.news_log.insert(0, headline)
        self.news_log = self.news_log[:40]

    # ------------------------------------------------------------------
    # ACHIEVEMENTS
    # ------------------------------------------------------------------
    def check_achievement(self, key):
        if key in self.achievements_unlocked:
            return None
        self.achievements_unlocked.add(key)
        spec = next((a for a in gd.ACHIEVEMENTS if a["key"] == key), None)
        return spec

    def check_all_achievements(self):
        newly = []
        nw = self.net_worth()
        conditions = {
            "first_lakh": nw >= 1_00_000,
            "first_business": len(self.businesses) >= 1,
            "first_employee": len(self.employees) >= 1,
            "hundred_employees": len(self.employees) >= 100,
            "millionaire": nw >= 1_00_00_000,
            "billionaire": nw >= 100_00_00_000,
            "trillionaire": nw >= 1_00_000_00_00_000,
            "first_stock": len(self.portfolio) >= 1,
            "loan_free": self.had_loan and len(self.loans) == 0,
        }
        for key, met in conditions.items():
            if met:
                spec = self.check_achievement(key)
                if spec:
                    newly.append(spec)
        return newly

    def get_ending(self):
        nw = self.net_worth()
        if self.game_over:
            return "Bankrupt", "You ran out of money and lost everything. Better luck next time!"
        if nw >= 1_00_000_00_00_000:
            return "World's Richest", "You are now the richest person on Earth. Legendary!"
        if nw >= 100_00_00_000:
            return "Billionaire", "You made it to billionaire status!"
        if nw >= 1_00_00_000:
            return "Millionaire", "You are officially a millionaire!"
        return "In Progress", "Keep building your empire."

    # ------------------------------------------------------------------
    # SAVE / LOAD
    # ------------------------------------------------------------------
    def to_dict(self):
        return {
            "year": self.year, "day": self.day, "age": self.age,
            "money": self.money, "bank_balance": self.bank_balance,
            "health": self.health, "stress": self.stress, "energy": self.energy,
            "followers": self.followers, "reputation": self.reputation,
            "credit_score": self.credit_score,
            "businesses": [b.to_dict() for b in self.businesses],
            "employees": [e.to_dict() for e in self.employees],
            "portfolio": self.portfolio,
            "loans": self.loans,
            "fixed_deposits": self.fixed_deposits,
            "had_loan": self.had_loan,
            "stocks": self.stocks,
            "achievements_unlocked": list(self.achievements_unlocked),
            "net_worth_history": self.net_worth_history,
            "money_history": self.money_history,
            "business_profit_history": self.business_profit_history,
            "portfolio_value_history": self.portfolio_value_history,
            "followers_history": self.followers_history,
            "networth_by_year": self.networth_by_year,
            "ledger": self.ledger,
            "news_log": self.news_log,
            "event_log": self.event_log,
            "sound_on": self.sound_on,
            "music_on": self.music_on,
            "saved_at": datetime.datetime.now().isoformat(),
        }

    def save(self, path=None):
        path = path or SAVE_FILE
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load(path=None):
        path = path or SAVE_FILE
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        gs = GameState()
        gs.year = d["year"]; gs.day = d["day"]; gs.age = d["age"]
        gs.money = d["money"]; gs.bank_balance = d["bank_balance"]
        gs.health = d["health"]; gs.stress = d["stress"]; gs.energy = d["energy"]
        gs.followers = d["followers"]; gs.reputation = d["reputation"]
        gs.credit_score = d.get("credit_score", 650)
        gs.businesses = [Business.from_dict(b) for b in d["businesses"]]
        gs.employees = [Employee.from_dict(e) for e in d["employees"]]
        gs.portfolio = d["portfolio"]
        gs.loans = d["loans"]
        gs.fixed_deposits = d["fixed_deposits"]
        gs.had_loan = d.get("had_loan", False)
        gs.stocks = d["stocks"]
        gs.achievements_unlocked = set(d["achievements_unlocked"])
        gs.net_worth_history = d["net_worth_history"]
        gs.money_history = d.get("money_history", [gs.money])
        gs.business_profit_history = d.get("business_profit_history", [0])
        gs.portfolio_value_history = d.get("portfolio_value_history", [0])
        gs.followers_history = d.get("followers_history", [0])
        gs.networth_by_year = d.get("networth_by_year", {})
        gs.ledger = d.get("ledger", [])
        gs.news_log = d["news_log"]
        gs.event_log = d["event_log"]
        gs.sound_on = d.get("sound_on", True)
        gs.music_on = d.get("music_on", True)
        return gs

    @staticmethod
    def save_exists(path=None):
        path = path or SAVE_FILE
        return os.path.exists(path)


# =============================================================================
# USER ACCOUNTS (multi-user login system)
# =============================================================================
"""
Very small local account system so several people can share this one game
file, each with their own unique ID, username and save game.

- Each user gets a unique ID like "U1001" (never reused).
- Usernames must be unique (case-insensitive).
- Passwords are stored as salted SHA-256 hashes, never in plain text.
- Every user has their own save file: save_<id>.json
- Logging back in with the same ID/username + password resumes the game
  exactly where that user left off.
"""
import hashlib
import secrets


def _hash_password(password, salt):
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _load_users_db():
    if not os.path.exists(USERS_FILE):
        return {"next_id": 1001, "users": []}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"next_id": 1001, "users": []}


def _save_users_db(db):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def _find_user(db, identifier):
    ident = identifier.strip().lower()
    for u in db["users"]:
        if u["username"].lower() == ident or u["id"].lower() == ident:
            return u
    return None


def register_user(username, password):
    username = username.strip()
    if not username or not password:
        return None, "Username and password are required."
    if len(username) < 3:
        return None, "Username must be at least 3 characters."
    if len(password) < 4:
        return None, "Password must be at least 4 characters."
    db = _load_users_db()
    if _find_user(db, username) is not None:
        return None, "That username is already taken. Choose another."
    user_id = f"U{db['next_id']}"
    db["next_id"] += 1
    salt = secrets.token_hex(8)
    user = {
        "id": user_id,
        "username": username,
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "save_file": f"save_{user_id}.json",
        "created_at": datetime.datetime.now().isoformat(),
    }
    db["users"].append(user)
    _save_users_db(db)
    # create a fresh save game for this user right away
    GameState().save(os.path.join(SAVE_DIR, user["save_file"]))
    return user, None


def login_user(identifier, password):
    db = _load_users_db()
    user = _find_user(db, identifier)
    if user is None:
        return None, "No account found with that username/ID."
    if _hash_password(password, user["salt"]) != user["password_hash"]:
        return None, "Incorrect password."
    return user, None


def all_users():
    db = _load_users_db()
    return db["users"]


# =============================================================================
# REUSABLE WIDGETS
# =============================================================================
# -*- coding: utf-8 -*-
"""
Small reusable Tkinter widgets used across the game's screens.
"""


class StatBar(tk.Frame):
    """A labelled horizontal progress bar (health / stress / energy)."""

    def __init__(self, parent, label, color=th.NEON_GREEN, width=140, height=14, **kw):
        super().__init__(parent, bg=th.BG_PANEL, **kw)
        self.color = color
        self.width = width
        self.height = height
        self.label_text = label

        self.top = tk.Frame(self, bg=th.BG_PANEL)
        self.top.pack(fill="x")
        self.lbl = tk.Label(self.top, text=label, bg=th.BG_PANEL, fg=th.GREY, font=th.FONT_SMALL)
        self.lbl.pack(side="left")
        self.val_lbl = tk.Label(self.top, text="", bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_SMALL)
        self.val_lbl.pack(side="right")

        self.canvas = tk.Canvas(self, width=width, height=height, bg=th.BG, highlightthickness=1,
                                 highlightbackground=th.BORDER)
        self.canvas.pack(fill="x", pady=(2, 4))
        self.set_value(100)

    def set_value(self, pct, color=None):
        pct = max(0, min(100, pct))
        color = color or self.color
        self.canvas.delete("all")
        w = int(self.width * (pct / 100))
        self.canvas.create_rectangle(0, 0, w, self.height, fill=color, outline="")
        self.val_lbl.configure(text=f"{int(pct)}%")


class NetWorthGraph(tk.Canvas):
    """Simple line-chart canvas for any numeric history, no external deps."""

    def __init__(self, parent, width=520, height=180, title="Net Worth", color=None, **kw):
        super().__init__(parent, width=width, height=height, bg=th.BG,
                          highlightthickness=1, highlightbackground=th.BORDER, **kw)
        self.width = width
        self.height = height
        self.title = title
        self.color = color or th.NEON_GREEN

    def draw(self, history, fmt_money=None, title=None, color=None):
        self.delete("all")
        title = title or self.title
        color = color or self.color
        if not history:
            return
        pad = 30
        w = self.width - 2 * pad
        h = self.height - 2 * pad
        lo, hi = min(history), max(history)
        if hi == lo:
            hi = lo + 1
        n = len(history)
        step = w / max(1, n - 1)

        # gridlines
        for i in range(4):
            y = pad + h * i / 3
            self.create_line(pad, y, pad + w, y, fill=th.BORDER)

        points = []
        for i, v in enumerate(history):
            x = pad + i * step
            y = pad + h - (v - lo) / (hi - lo) * h
            points.append((x, y))

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            self.create_line(x1, y1, x2, y2, fill=color, width=2)

        if points:
            x, y = points[-1]
            self.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="")

        label = fmt_money(history[-1]) if fmt_money else str(int(history[-1]))
        self.create_text(pad, 12, text=title, fill=th.GREY, anchor="w", font=th.FONT_SMALL)
        self.create_text(pad + w, 12, text=label, fill=color, anchor="e", font=th.FONT_BOLD)


class Toast(tk.Toplevel):
    """A small auto-dismissing notification popup in the corner of the window."""

    def __init__(self, parent, title, message, accent=th.NEON_GREEN, duration=3500):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=accent)
        self.attributes("-alpha", 0.97)

        inner = tk.Frame(self, bg=th.BG_PANEL, padx=14, pady=10)
        inner.pack(padx=2, pady=2)
        tk.Label(inner, text=title, bg=th.BG_PANEL, fg=accent, font=th.FONT_BOLD,
                  anchor="w", justify="left").pack(anchor="w")
        tk.Label(inner, text=message, bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_SMALL,
                  wraplength=280, justify="left", anchor="w").pack(anchor="w")

        self.update_idletasks()
        parent.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        x = px + pw - w - 24
        y = py + ph - h - 24 - getattr(parent, "_toast_offset", 0)
        self.geometry(f"+{x}+{y}")

        parent._toast_offset = getattr(parent, "_toast_offset", 0) + h + 10
        self.after(duration, self._close)

    def _close(self):
        try:
            self.master._toast_offset = max(0, getattr(self.master, "_toast_offset", 0) - (self.winfo_height() + 10))
            self.destroy()
        except Exception:
            pass


def card(parent, **kw):
    f = tk.Frame(parent, bg=th.BG_PANEL, highlightthickness=1,
                 highlightbackground=th.BORDER, **kw)
    return f


# =============================================================================
# LOGIN / REGISTER WINDOW
# =============================================================================
class LoginWindow(tk.Tk):
    """Shown before the main game. Lets a person register a new unique
    account or log back into an existing one and resume exactly where
    they left off."""

    def __init__(self):
        super().__init__()
        self.title("Shadow Market — Login")
        self.geometry("440x520")
        self.minsize(420, 500)
        self.configure(bg=th.BG)
        self.resizable(False, False)

        self.logged_in_user = None  # set on success; main() checks this

        wrap = tk.Frame(self, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(wrap, text="\U0001F4B8 SHADOW MARKET", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(pady=(0, 4))
        tk.Label(wrap, text="Rise to Billionaire", bg=th.BG, fg=th.GREY,
                  font=th.FONT_SMALL).pack(pady=(0, 16))

        self.tab_frame = tk.Frame(wrap, bg=th.BG)
        self.tab_frame.pack(fill="x")
        self.login_tab_btn = tk.Button(self.tab_frame, text="Login", command=lambda: self._show_tab("login"))
        th.style_button(self.login_tab_btn)
        self.login_tab_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.register_tab_btn = tk.Button(self.tab_frame, text="Register", command=lambda: self._show_tab("register"))
        th.style_button(self.register_tab_btn, accent=th.NEON_CYAN)
        self.register_tab_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.form_card = card(wrap)
        self.form_card.pack(fill="both", expand=True, pady=16)

        self.status_lbl = tk.Label(wrap, text="", bg=th.BG, fg=th.RED, font=th.FONT_SMALL, wraplength=380)
        self.status_lbl.pack(pady=(0, 6))

        self._show_tab("login")
        self.bind("<Return>", lambda e: self._submit())

    def _entry(self, parent, show=None):
        e = tk.Entry(parent, bg=th.BG, fg=th.WHITE, insertbackground=th.WHITE, relief="flat",
                      highlightthickness=1, highlightbackground=th.BORDER, font=th.FONT_NORMAL, show=show)
        return e

    def _show_tab(self, which):
        self.mode = which
        for w in self.form_card.winfo_children():
            w.destroy()
        self.status_lbl.configure(text="")
        self.login_tab_btn.configure(bg=th.NEON_GREEN if which == "login" else th.BG_PANEL_2,
                                      fg=th.BG if which == "login" else th.NEON_GREEN)
        self.register_tab_btn.configure(bg=th.NEON_CYAN if which == "register" else th.BG_PANEL_2,
                                         fg=th.BG if which == "register" else th.NEON_CYAN)

        if which == "login":
            tk.Label(self.form_card, text="Log In", bg=th.BG_PANEL, fg=th.NEON_GREEN,
                      font=th.FONT_SUBHEADER).pack(anchor="w", padx=16, pady=(16, 10))
            tk.Label(self.form_card, text="Username or User ID", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w", padx=16)
            self.login_id = self._entry(self.form_card)
            self.login_id.pack(fill="x", padx=16, pady=(2, 10))
            tk.Label(self.form_card, text="Password", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w", padx=16)
            self.login_pw = self._entry(self.form_card, show="*")
            self.login_pw.pack(fill="x", padx=16, pady=(2, 16))
            btn = tk.Button(self.form_card, text="Log In & Resume Game", command=self._submit)
            th.style_button(btn)
            btn.pack(fill="x", padx=16, pady=(0, 16))
            self.login_id.focus_set()
        else:
            tk.Label(self.form_card, text="Create Account", bg=th.BG_PANEL, fg=th.NEON_CYAN,
                      font=th.FONT_SUBHEADER).pack(anchor="w", padx=16, pady=(16, 10))
            tk.Label(self.form_card, text="Choose a unique username", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w", padx=16)
            self.reg_username = self._entry(self.form_card)
            self.reg_username.pack(fill="x", padx=16, pady=(2, 10))
            tk.Label(self.form_card, text="Password", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w", padx=16)
            self.reg_pw = self._entry(self.form_card, show="*")
            self.reg_pw.pack(fill="x", padx=16, pady=(2, 10))
            tk.Label(self.form_card, text="Confirm Password", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w", padx=16)
            self.reg_pw2 = self._entry(self.form_card, show="*")
            self.reg_pw2.pack(fill="x", padx=16, pady=(2, 16))
            btn = tk.Button(self.form_card, text="Create Account", command=self._submit)
            th.style_button(btn, accent=th.NEON_CYAN)
            btn.pack(fill="x", padx=16, pady=(0, 8))
            tk.Label(self.form_card, text="You'll get a unique User ID — keep it safe,\n"
                                           "you can log in with either your ID or username.",
                      bg=th.BG_PANEL, fg=th.GREY, font=th.FONT_SMALL, justify="left").pack(
                anchor="w", padx=16, pady=(0, 16))
            self.reg_username.focus_set()

    def _submit(self):
        if self.mode == "login":
            ident = self.login_id.get().strip()
            pw = self.login_pw.get()
            if not ident or not pw:
                self.status_lbl.configure(text="Enter your username/ID and password.")
                return
            user, err = login_user(ident, pw)
            if err:
                self.status_lbl.configure(text=err)
                return
            self.logged_in_user = user
            self.destroy()
        else:
            uname = self.reg_username.get().strip()
            pw = self.reg_pw.get()
            pw2 = self.reg_pw2.get()
            if pw != pw2:
                self.status_lbl.configure(text="Passwords do not match.")
                return
            user, err = register_user(uname, pw)
            if err:
                self.status_lbl.configure(text=err)
                return
            messagebox.showinfo("Account Created",
                                 f"Welcome, {user['username']}!\nYour unique User ID is: {user['id']}\n"
                                 "Keep it safe — you can log in with either your ID or username.")
            self.logged_in_user = user
            self.destroy()


# =============================================================================
# MAIN GUI APPLICATION
# =============================================================================
# -*- coding: utf-8 -*-
"""
Shadow Market: Rise to Billionaire — main GUI application.
"""



class App(tk.Tk):
    def __init__(self, user=None):
        super().__init__()
        self.title("Shadow Market: Rise to Billionaire")
        self.geometry("1180x760")
        self.minsize(1000, 640)
        self.configure(bg=th.BG)

        # ---- multi-user account info ----
        self.user = user or {"id": "GUEST", "username": "Guest", "save_file": "savegame.json"}
        self.save_path = os.path.join(SAVE_DIR, self.user.get("save_file", "savegame.json"))
        self.should_return_to_login = False

        if GameState.save_exists(self.save_path):
            try:
                self.gs = GameState.load(self.save_path)
            except Exception:
                self.gs = GameState()
        else:
            self.gs = GameState()

        self._toast_offset = 0
        self.auto_advance = True
        self.day_speed_ms = 10000  # 1 in-game day per 10 real seconds
        self._hint_index = 0

        self._build_layout()
        self.show_screen("home")

        sm.start_ambient(self.gs.music_on)

        self.after(1000, self._stock_tick_loop)
        self.after(self.day_speed_ms, self._day_loop)
        self.after(random.randint(20000, 40000), self._event_loop)
        self.after(30000, self._autosave_loop)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build_layout(self):
        # Top header (stats bar)
        self.header = tk.Frame(self, bg=th.BG_PANEL, height=92)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)
        self._build_header()

        # Body = sidebar + content
        body = tk.Frame(self, bg=th.BG)
        body.pack(side="top", fill="both", expand=True)

        self.sidebar = tk.Frame(body, bg=th.BG_PANEL, width=190)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        self.content = tk.Frame(body, bg=th.BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Bottom news ticker
        self.ticker_frame = tk.Frame(self, bg="#050705", height=28)
        self.ticker_frame.pack(side="bottom", fill="x")
        self.ticker_frame.pack_propagate(False)
        self.ticker_label = tk.Label(self.ticker_frame, text="", bg="#050705", fg=th.NEON_CYAN,
                                      font=th.FONT_SMALL, anchor="w")
        self.ticker_label.pack(fill="both", expand=True, padx=10)
        self._ticker_text = "Welcome to Shadow Market. Build your empire...  " * 3
        self._ticker_pos = 0
        self._scroll_ticker()

    def _build_header(self):
        left = tk.Frame(self.header, bg=th.BG_PANEL)
        left.pack(side="left", padx=18, pady=10)
        tk.Label(left, text="\U0001F4B8 SHADOW MARKET", bg=th.BG_PANEL, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w")
        who = f"{self.user.get('username', 'Guest')}  ({self.user.get('id', 'GUEST')})"
        tk.Label(left, text=who, bg=th.BG_PANEL, fg=th.GREY, font=th.FONT_SMALL).pack(anchor="w")
        self.money_lbl = tk.Label(left, text="", bg=th.BG_PANEL, fg=th.NEON_YELLOW, font=th.FONT_MONEY)
        self.money_lbl.pack(anchor="w")

        stats = tk.Frame(self.header, bg=th.BG_PANEL)
        stats.pack(side="left", padx=20, pady=8, fill="y")
        self.stat_labels = {}
        grid_specs = [
            ("net_worth", "Net Worth"), ("age", "Age"), ("day", "Day/Year"),
            ("followers", "Followers"), ("companies", "Companies"), ("employees", "Employees"),
        ]
        for i, (key, label) in enumerate(grid_specs):
            col = tk.Frame(stats, bg=th.BG_PANEL)
            col.grid(row=0, column=i, padx=12)
            tk.Label(col, text=label, bg=th.BG_PANEL, fg=th.GREY, font=th.FONT_SMALL).pack(anchor="w")
            v = tk.Label(col, text="-", bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_BOLD)
            v.pack(anchor="w")
            self.stat_labels[key] = v

        bars = tk.Frame(self.header, bg=th.BG_PANEL)
        bars.pack(side="right", padx=18, pady=10)
        self.health_bar = StatBar(bars, "Health", th.NEON_GREEN, width=110)
        self.health_bar.grid(row=0, column=0, padx=6)
        self.stress_bar = StatBar(bars, "Stress", th.RED, width=110)
        self.stress_bar.grid(row=0, column=1, padx=6)
        self.energy_bar = StatBar(bars, "Energy", th.NEON_CYAN, width=110)
        self.energy_bar.grid(row=0, column=2, padx=6)

    def _build_sidebar(self):
        tk.Label(self.sidebar, text="MENU", bg=th.BG_PANEL, fg=th.GREY, font=th.FONT_SMALL).pack(
            anchor="w", padx=16, pady=(16, 4))
        items = [
            ("home", "\U0001F3E0  Home"),
            ("business", "\U0001F3E2  Business"),
            ("market", "\U0001F4C8  Market"),
            ("bank", "\U0001F3E6  Bank"),
            ("employees", "\U0001F468\u200D\U0001F4BC  Employees"),
            ("ledger", "\U0001F4D2  Ledger"),
            ("news", "\U0001F4F0  News & Events"),
            ("achievements", "\U0001F3C6  Achievements"),
            ("leaderboard", "\U0001F947  Leaderboard"),
            ("settings", "\u2699\uFE0F  Settings"),
        ]
        self.nav_buttons = {}
        for key, label in items:
            b = tk.Button(self.sidebar, text=label, anchor="w",
                           command=lambda k=key: self.show_screen(k))
            th.style_button(b)
            b.configure(justify="left")
            b.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[key] = b

        tk.Frame(self.sidebar, bg=th.BORDER, height=1).pack(fill="x", padx=10, pady=10)

        next_btn = tk.Button(self.sidebar, text="\u23E9 Next Day", command=self.manual_next_day)
        th.style_button(next_btn, accent=th.NEON_YELLOW)
        next_btn.pack(fill="x", padx=10, pady=3)

        self.pause_btn = tk.Button(self.sidebar, text="\u23F8 Pause Auto-Day", command=self.toggle_auto_advance)
        th.style_button(self.pause_btn, accent=th.NEON_CYAN)
        self.pause_btn.pack(fill="x", padx=10, pady=3)

        save_btn = tk.Button(self.sidebar, text="\U0001F4BE Save Game", command=self.save_game)
        th.style_button(save_btn)
        save_btn.pack(fill="x", padx=10, pady=(20, 3))

        logout_btn = tk.Button(self.sidebar, text="\U0001F6AA Logout", command=self.logout)
        th.style_button(logout_btn, accent=th.RED)
        logout_btn.pack(fill="x", padx=10, pady=3)

    # ------------------------------------------------------------------
    # SCREEN SWITCHING
    # ------------------------------------------------------------------
    def show_screen(self, key, preserve_scroll=False):
        self.play("click")
        prev_frac = None
        if preserve_scroll:
            prev_canvas = getattr(self, "_scroll_canvas", None)
            if prev_canvas is not None:
                try:
                    prev_frac = prev_canvas.yview()[0]
                except Exception:
                    prev_frac = None
        for w in self.content.winfo_children():
            w.destroy()
        for k, b in self.nav_buttons.items():
            b.configure(fg=th.NEON_GREEN if k != key else th.BG,
                        bg=th.BG_PANEL_2 if k != key else th.NEON_GREEN)
        builder = getattr(self, f"_screen_{key}", None)
        if builder:
            builder(self.content)
        self.refresh_header()
        if preserve_scroll and prev_frac is not None:
            new_canvas = getattr(self, "_scroll_canvas", None)
            if new_canvas is not None:
                self.after(1, lambda: new_canvas.yview_moveto(prev_frac))

    # ------------------------------------------------------------------
    # HEADER REFRESH
    # ------------------------------------------------------------------
    def refresh_header(self):
        gs = self.gs
        self.money_lbl.configure(text=fmt_money(gs.money))
        self.stat_labels["net_worth"].configure(text=fmt_money(gs.net_worth()))
        self.stat_labels["age"].configure(text=str(gs.age))
        self.stat_labels["day"].configure(text=f"{gs.day}/{gs.year}")
        self.stat_labels["followers"].configure(text=str(gs.followers))
        self.stat_labels["companies"].configure(text=str(len(gs.businesses)))
        self.stat_labels["employees"].configure(text=str(len(gs.employees)))
        self.health_bar.set_value(gs.health, th.NEON_GREEN if gs.health > 40 else th.RED)
        self.stress_bar.set_value(gs.stress, th.RED if gs.stress > 60 else th.NEON_YELLOW)
        self.energy_bar.set_value(gs.energy, th.NEON_CYAN if gs.energy > 30 else th.RED)

    # ------------------------------------------------------------------
    # SOUND / TOAST HELPERS
    # ------------------------------------------------------------------
    def play(self, name):
        sm.play(f"{name}.wav", self.gs.sound_on)

    def toast(self, title, message, accent=th.NEON_GREEN):
        try:
            Toast(self, title, message, accent=accent)
        except Exception:
            pass

    def push_ticker(self, text):
        self.gs.push_news(text)
        self._ticker_text = "   \u2022   ".join(self.gs.news_log[:12]) + "   \u2022   "

    def _scroll_ticker(self):
        text = self._ticker_text or " "
        display = (text + "     ") * 2
        pos = self._ticker_pos % max(1, len(text) + 5)
        self.ticker_label.configure(text=display[pos:pos + 160])
        self._ticker_pos += 1
        self.after(180, self._scroll_ticker)

    # ------------------------------------------------------------------
    # GAME LOOPS
    # ------------------------------------------------------------------
    def _stock_tick_loop(self):
        self.gs.tick_stocks()
        if getattr(self, "_current_screen", None) == "market":
            self.show_screen("market")
        self.after(3000, self._stock_tick_loop)

    def _day_loop(self):
        if self.auto_advance and not self.gs.game_over:
            self._do_advance_day()
        self.after(self.day_speed_ms, self._day_loop)

    def _event_loop(self):
        if not self.gs.game_over:
            entry = self.gs.trigger_random_event()
            self.play("event")
            self.push_ticker(f"BREAKING: {entry['name']} — {entry['text']}")
            self.toast("\U0001F4E2 World Event: " + entry["name"], entry["text"], accent=th.NEON_PINK)
            self.refresh_header()
        self.after(random.randint(35000, 70000), self._event_loop)

    def _autosave_loop(self):
        try:
            self.gs.save(self.save_path)
        except Exception:
            pass
        self.after(30000, self._autosave_loop)

    def manual_next_day(self):
        self._do_advance_day()

    def toggle_auto_advance(self):
        self.auto_advance = not self.auto_advance
        self.pause_btn.configure(text="\u25B6 Resume Auto-Day" if not self.auto_advance else "\u23F8 Pause Auto-Day")

    def _do_advance_day(self):
        gs = self.gs
        result = gs.advance_day()
        self.play("tick")
        if result["profit"] > 0:
            self.push_ticker(f"Day {gs.day}: business profit {fmt_money(result['profit'])}")
        for ev in result["events"]:
            self.push_ticker(ev)
        newly = gs.check_all_achievements()
        for spec in newly:
            self.play("achievement")
            self.toast("\U0001F3C6 Achievement Unlocked!", spec["name"], accent=th.NEON_YELLOW)
        if gs.game_over:
            self.play("gameover")
            self._show_game_over()
        self.refresh_header()
        if getattr(self, "_current_screen", None) in ("home", "business", "bank", "employees", "ledger"):
            self.show_screen(self._current_screen, preserve_scroll=True)

    def _show_game_over(self):
        title, msg = self.gs.get_ending()
        messagebox.showinfo("Game Over: " + title, msg)

    # ------------------------------------------------------------------
    # SAVE / LOGOUT / CLOSE
    # ------------------------------------------------------------------
    def save_game(self):
        try:
            self.gs.save(self.save_path)
            self.play("coin")
            self.toast("Saved", "Your game has been saved.", accent=th.NEON_GREEN)
        except Exception as e:
            messagebox.showerror("Save Failed", str(e))

    def logout(self):
        if not messagebox.askyesno("Logout", "Save and logout? You can log back in any time to resume."):
            return
        try:
            self.gs.save(self.save_path)
        except Exception:
            pass
        self.should_return_to_login = True
        self.destroy()

    def _on_close(self):
        try:
            self.gs.save(self.save_path)
        except Exception:
            pass
        self.destroy()

    # ------------------------------------------------------------------
    # SCREEN: HOME
    # ------------------------------------------------------------------
    def _screen_home(self, parent):
        self._current_screen = "home"
        gs = self.gs
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        left = tk.Frame(wrap, bg=th.BG)
        left.pack(side="left", fill="both", expand=True)

        # --- multiple small graphs: net worth, cash, business profit, portfolio ---
        graphs_card = card(left)
        graphs_card.pack(fill="x", pady=(0, 12))
        tk.Label(graphs_card, text="\U0001F4CA Your Numbers Over Time", bg=th.BG_PANEL, fg=th.NEON_GREEN,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 4))
        graphs_grid = tk.Frame(graphs_card, bg=th.BG_PANEL)
        graphs_grid.pack(padx=10, pady=(0, 10))

        graph_specs = [
            ("Net Worth", gs.net_worth_history, th.NEON_GREEN),
            ("Cash in Hand", gs.money_history, th.NEON_YELLOW),
            ("Daily Business Profit", gs.business_profit_history, th.NEON_CYAN),
            ("Stock Portfolio Value", gs.portfolio_value_history, th.NEON_PINK),
        ]
        for i, (title, hist, color) in enumerate(graph_specs):
            g = NetWorthGraph(graphs_grid, width=270, height=140, title=title, color=color)
            g.grid(row=i // 2, column=i % 2, padx=6, pady=6)
            g.draw(hist, fmt_money)

        ending_title, ending_msg = gs.get_ending()
        status_card = card(left)
        status_card.pack(fill="x", pady=(0, 12))
        tk.Label(status_card, text=f"Status: {ending_title}", bg=th.BG_PANEL, fg=th.NEON_YELLOW,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(status_card, text=ending_msg, bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_NORMAL,
                  wraplength=520, justify="left").pack(anchor="w", padx=14, pady=(2, 10))

        events_card = card(left)
        events_card.pack(fill="both", expand=True)
        tk.Label(events_card, text="\U0001F4CB Recent Activity", bg=th.BG_PANEL, fg=th.NEON_GREEN,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 4))
        log_box = tk.Listbox(events_card, bg=th.BG, fg=th.WHITE, font=th.FONT_SMALL,
                              highlightthickness=0, bd=0, selectbackground=th.BG_PANEL_2)
        log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        for headline in gs.news_log[:20]:
            log_box.insert("end", "  " + headline)
        if not gs.news_log:
            log_box.insert("end", "  Nothing has happened yet. Start a business!")

        right = tk.Frame(wrap, bg=th.BG, width=280)
        right.pack(side="left", fill="y", padx=(14, 0))
        right.pack_propagate(False)

        quick_card = card(right)
        quick_card.pack(fill="x", pady=(0, 12))
        tk.Label(quick_card, text="\u26A1 Quick Actions", bg=th.BG_PANEL, fg=th.NEON_GREEN,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 6))
        qb1 = tk.Button(quick_card, text="Start a Business", command=lambda: self.show_screen("business"))
        th.style_button(qb1)
        qb1.pack(fill="x", padx=14, pady=4)
        qb2 = tk.Button(quick_card, text="Trade Stocks", command=lambda: self.show_screen("market"))
        th.style_button(qb2, accent=th.NEON_CYAN)
        qb2.pack(fill="x", padx=14, pady=4)
        qb3 = tk.Button(quick_card, text="Visit Bank", command=lambda: self.show_screen("bank"))
        th.style_button(qb3, accent=th.NEON_YELLOW)
        qb3.pack(fill="x", padx=14, pady=(4, 14))

        hint_card = card(right)
        hint_card.pack(fill="x", pady=(0, 12))
        tk.Label(hint_card, text="\U0001F4A1 Hint", bg=th.BG_PANEL, fg=th.NEON_PINK,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 4))
        tip = random.choice(gd.GAME_HINTS)
        tk.Label(hint_card, text=tip, bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_SMALL,
                  wraplength=240, justify="left").pack(anchor="w", padx=14, pady=(0, 12))

        biz_card = card(right)
        biz_card.pack(fill="both", expand=True)
        tk.Label(biz_card, text="\U0001F3E2 Your Businesses", bg=th.BG_PANEL, fg=th.NEON_GREEN,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 4))
        if not gs.businesses:
            tk.Label(biz_card, text="No businesses yet.", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w", padx=14, pady=10)
        else:
            mult = gs.employee_multiplier()
            for b in gs.businesses:
                row = tk.Frame(biz_card, bg=th.BG_PANEL_2)
                row.pack(fill="x", padx=12, pady=3)
                tk.Label(row, text=f"{b.spec['icon']} {b.spec['name']} Lv{b.level}", bg=th.BG_PANEL_2,
                          fg=th.WHITE, font=th.FONT_SMALL).pack(side="left", padx=8, pady=4)
                tk.Label(row, text=f"+{fmt_money(b.daily_profit(mult))}/day", bg=th.BG_PANEL_2,
                          fg=th.NEON_GREEN, font=th.FONT_SMALL).pack(side="right", padx=8)

    # ------------------------------------------------------------------
    # SCREEN: BUSINESS
    # ------------------------------------------------------------------
    def _screen_business(self, parent):
        self._current_screen = "business"
        gs = self.gs
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        canvas = tk.Canvas(wrap, bg=th.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=th.BG)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._scroll_canvas = canvas

        tk.Label(scroll_frame, text="\U0001F3E2 Start a New Business", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w", pady=(0, 10))

        grid = tk.Frame(scroll_frame, bg=th.BG)
        grid.pack(fill="x")
        for i, spec in enumerate(gd.BUSINESS_TYPES):
            c = card(grid)
            c.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="nsew")
            tk.Label(c, text=f"{spec['icon']} {spec['name']}", bg=th.BG_PANEL, fg=th.WHITE,
                      font=th.FONT_SUBHEADER).pack(anchor="w", padx=12, pady=(10, 2))
            tk.Label(c, text=spec["desc"], bg=th.BG_PANEL, fg=th.GREY, font=th.FONT_SMALL,
                      wraplength=200, justify="left").pack(anchor="w", padx=12)
            info = tk.Frame(c, bg=th.BG_PANEL)
            info.pack(anchor="w", padx=12, pady=6)
            tk.Label(info, text=f"Cost: {fmt_money(spec['cost'])}", bg=th.BG_PANEL, fg=th.NEON_YELLOW,
                      font=th.FONT_SMALL).pack(anchor="w")
            tk.Label(info, text=f"Profit: {fmt_money(spec['base_profit'])}/day", bg=th.BG_PANEL,
                      fg=th.NEON_GREEN, font=th.FONT_SMALL).pack(anchor="w")
            risk_pct = int(spec["risk"] * 100)
            tk.Label(info, text=f"Risk: {risk_pct}%", bg=th.BG_PANEL, fg=th.RED, font=th.FONT_SMALL).pack(anchor="w")
            btn = tk.Button(c, text="Start", command=lambda k=spec["key"]: self._start_business(k))
            th.style_button(btn)
            btn.pack(fill="x", padx=12, pady=(4, 12))
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1, uniform="biz")

        tk.Label(scroll_frame, text="\U0001F4CA Your Businesses", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w", pady=(20, 10))

        if not gs.businesses:
            tk.Label(scroll_frame, text="You don't own any businesses yet.", bg=th.BG, fg=th.GREY,
                      font=th.FONT_NORMAL).pack(anchor="w")
        else:
            mult = gs.employee_multiplier()
            for idx, b in enumerate(gs.businesses):
                spec = b.spec
                row = card(scroll_frame)
                row.pack(fill="x", pady=6)
                left = tk.Frame(row, bg=th.BG_PANEL)
                left.pack(side="left", fill="x", expand=True, padx=12, pady=10)
                tk.Label(left, text=f"{spec['icon']} {spec['name']}  (Level {b.level})", bg=th.BG_PANEL,
                          fg=th.WHITE, font=th.FONT_BOLD).pack(anchor="w")
                tk.Label(left, text=f"Profit: {fmt_money(b.daily_profit(mult))}/day   |   "
                                     f"Invested: {fmt_money(b.total_invested)}   |   "
                                     f"Days owned: {b.days_owned}",
                          bg=th.BG_PANEL, fg=th.GREY, font=th.FONT_SMALL).pack(anchor="w")
                btns = tk.Frame(row, bg=th.BG_PANEL)
                btns.pack(side="right", padx=12)
                up_cost = int(spec["upgrade_cost"] * (1.25 ** (b.level - 1)))
                up_btn = tk.Button(btns, text=f"Upgrade ({fmt_money(up_cost)})",
                                    command=lambda i=idx: self._upgrade_business(i))
                th.style_button(up_btn, accent=th.NEON_CYAN)
                up_btn.pack(side="left", padx=4)
                close_btn = tk.Button(btns, text="Close", command=lambda i=idx: self._close_business(i))
                th.style_button(close_btn, accent=th.RED)
                close_btn.pack(side="left", padx=4)

    def _start_business(self, key):
        ok, msg = self.gs.start_business(key)
        if ok:
            self.play("coin")
            self.push_ticker(msg)
            self.gs.check_all_achievements()
        else:
            self.play("error")
        self.toast("Business" if ok else "Failed", msg, accent=th.NEON_GREEN if ok else th.RED)
        self.refresh_header()
        self.show_screen("business", preserve_scroll=True)

    def _upgrade_business(self, idx):
        ok, msg = self.gs.upgrade_business(idx)
        self.play("levelup" if ok else "error")
        self.toast("Upgraded" if ok else "Failed", msg, accent=th.NEON_CYAN if ok else th.RED)
        self.refresh_header()
        self.show_screen("business", preserve_scroll=True)

    def _close_business(self, idx):
        ok, msg = self.gs.close_business(idx)
        self.play("coin" if ok else "error")
        self.toast("Closed" if ok else "Failed", msg, accent=th.NEON_YELLOW if ok else th.RED)
        self.refresh_header()
        self.show_screen("business", preserve_scroll=True)

    # ------------------------------------------------------------------
    # SCREEN: MARKET
    # ------------------------------------------------------------------
    def _screen_market(self, parent):
        self._current_screen = "market"
        gs = self.gs
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        canvas = tk.Canvas(wrap, bg=th.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=th.BG)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._scroll_canvas = canvas

        header_row = tk.Frame(scroll_frame, bg=th.BG)
        header_row.pack(fill="x", pady=(0, 10))
        tk.Label(header_row, text="\U0001F4C8 Live Stock Market", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(side="left")

        hint_lbl = tk.Label(scroll_frame, text="\U0001F4A1 " + random.choice(gd.GAME_HINTS), bg=th.BG,
                             fg=th.NEON_PINK, font=th.FONT_SMALL, wraplength=900, justify="left")
        hint_lbl.pack(anchor="w", pady=(0, 12))

        portfolio_value = gs.portfolio_value()
        tk.Label(scroll_frame, text=f"Cash: {fmt_money(gs.money)}    |    "
                                     f"Portfolio Value: {fmt_money(portfolio_value)}",
                  bg=th.BG, fg=th.NEON_YELLOW, font=th.FONT_BOLD).pack(anchor="w", pady=(0, 10))

        # ---- one row per stock, each with its own qty + Buy/Sell so the
        #      player can pick as many different stocks as they like, in
        #      whatever quantities they like, in one visit to the screen ----
        for s in gs.stocks:
            hist = s["history"]
            change = 0.0
            if len(hist) >= 2:
                change = (hist[-1] - hist[-2]) / hist[-2] * 100
            arrow = "\u25B2" if change >= 0 else "\u25BC"
            change_color = th.NEON_GREEN if change >= 0 else th.RED
            owned = gs.portfolio.get(s["symbol"], 0)

            row = card(scroll_frame)
            row.pack(fill="x", pady=5)

            info = tk.Frame(row, bg=th.BG_PANEL)
            info.pack(side="left", fill="x", expand=True, padx=12, pady=10)
            tk.Label(info, text=f"{s['symbol']} — {s['name']}", bg=th.BG_PANEL, fg=th.WHITE,
                      font=th.FONT_BOLD).pack(anchor="w")
            tk.Label(info, text=f"{fmt_money(s['price'])}   {arrow} {change:+.2f}%   |   You own: {owned}",
                      bg=th.BG_PANEL, fg=change_color, font=th.FONT_SMALL).pack(anchor="w")

            trade = tk.Frame(row, bg=th.BG_PANEL)
            trade.pack(side="right", padx=12, pady=10)
            qty_var = tk.StringVar(value="1")
            qty_entry = tk.Entry(trade, textvariable=qty_var, width=6, bg=th.BG, fg=th.WHITE,
                                  insertbackground=th.WHITE, relief="flat", highlightthickness=1,
                                  highlightbackground=th.BORDER)
            qty_entry.pack(side="left", padx=(0, 6))
            buy_btn = tk.Button(trade, text="Buy",
                                 command=lambda sym=s["symbol"], v=qty_var: self._trade(sym, v.get(), "buy"))
            th.style_button(buy_btn)
            buy_btn.pack(side="left", padx=3)
            sell_btn = tk.Button(trade, text="Sell",
                                  command=lambda sym=s["symbol"], v=qty_var: self._trade(sym, v.get(), "sell"))
            th.style_button(sell_btn, accent=th.RED)
            sell_btn.pack(side="left", padx=3)

    def _trade(self, symbol, qty_str, action):
        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError
        except ValueError:
            self.play("error")
            self.toast("Invalid", "Enter a valid quantity.", accent=th.RED)
            return
        if action == "buy":
            ok, msg = self.gs.buy_stock(symbol, qty)
            self.play("buy" if ok else "error")
        else:
            ok, msg = self.gs.sell_stock(symbol, qty)
            self.play("sell" if ok else "error")
        if ok:
            self.gs.check_all_achievements()
        self.toast("Trade" if ok else "Failed", msg, accent=th.NEON_GREEN if ok else th.RED)
        self.refresh_header()
        self.show_screen("market", preserve_scroll=True)

    # ------------------------------------------------------------------
    # SCREEN: BANK
    # ------------------------------------------------------------------
    def _screen_bank(self, parent):
        self._current_screen = "bank"
        gs = self.gs
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        tk.Label(wrap, text="\U0001F3E6 Bank", bg=th.BG, fg=th.NEON_GREEN, font=th.FONT_HEADER).pack(
            anchor="w", pady=(0, 10))
        tk.Label(wrap, text=f"Credit Score: {gs.credit_score}", bg=th.BG, fg=th.NEON_CYAN,
                  font=th.FONT_BOLD).pack(anchor="w", pady=(0, 14))

        cols_wrap = tk.Frame(wrap, bg=th.BG)
        cols_wrap.pack(fill="both", expand=True)

        # LOANS
        loan_card = card(cols_wrap)
        loan_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(loan_card, text="\U0001F4B5 Loans", bg=th.BG_PANEL, fg=th.NEON_YELLOW,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 6))
        form = tk.Frame(loan_card, bg=th.BG_PANEL)
        form.pack(anchor="w", padx=14)
        amt_var = tk.StringVar(value="10000")
        tk.Label(form, text="Amount:", bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_SMALL).grid(row=0, column=0)
        tk.Entry(form, textvariable=amt_var, width=12, bg=th.BG, fg=th.WHITE, insertbackground=th.WHITE,
                  relief="flat", highlightthickness=1, highlightbackground=th.BORDER).grid(row=0, column=1, padx=6)
        loan_btn = tk.Button(form, text="Take Loan (12% / 60 days)", command=lambda: self._take_loan(amt_var.get()))
        th.style_button(loan_btn, accent=th.NEON_YELLOW)
        loan_btn.grid(row=0, column=2, padx=6)

        loan_list = tk.Frame(loan_card, bg=th.BG_PANEL)
        loan_list.pack(fill="both", expand=True, padx=14, pady=10)
        if not gs.loans:
            tk.Label(loan_list, text="No active loans.", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w")
        for loan in gs.loans:
            tk.Label(loan_list, text=f"Remaining: {fmt_money(loan['remaining'])}  |  "
                                      f"EMI: {fmt_money(loan['emi'])}/day  |  "
                                      f"Days left: {loan['days_left']}",
                      bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_SMALL).pack(anchor="w", pady=2)

        # FIXED DEPOSITS
        fd_card = card(cols_wrap)
        fd_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(fd_card, text="\U0001F4B0 Fixed Deposits", bg=th.BG_PANEL, fg=th.NEON_GREEN,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 6))
        form2 = tk.Frame(fd_card, bg=th.BG_PANEL)
        form2.pack(anchor="w", padx=14)
        fd_var = tk.StringVar(value="5000")
        tk.Label(form2, text="Amount:", bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_SMALL).grid(row=0, column=0)
        tk.Entry(form2, textvariable=fd_var, width=12, bg=th.BG, fg=th.WHITE, insertbackground=th.WHITE,
                  relief="flat", highlightthickness=1, highlightbackground=th.BORDER).grid(row=0, column=1, padx=6)
        fd_btn = tk.Button(form2, text="Open FD (8% / 90 days)", command=lambda: self._open_fd(fd_var.get()))
        th.style_button(fd_btn)
        fd_btn.grid(row=0, column=2, padx=6)

        fd_list = tk.Frame(fd_card, bg=th.BG_PANEL)
        fd_list.pack(fill="both", expand=True, padx=14, pady=10)
        if not gs.fixed_deposits:
            tk.Label(fd_list, text="No active FDs.", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w")
        for fd in gs.fixed_deposits:
            tk.Label(fd_list, text=f"Amount: {fmt_money(fd['amount'])}  |  Matures in {fd['days_left']} days",
                      bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_SMALL).pack(anchor="w", pady=2)

    def _take_loan(self, amt_str):
        try:
            amt = float(amt_str)
        except ValueError:
            amt = -1
        ok, msg = self.gs.take_loan(amt) if amt > 0 else (False, "Enter a valid amount.")
        self.play("coin" if ok else "error")
        self.toast("Loan" if ok else "Failed", msg, accent=th.NEON_YELLOW if ok else th.RED)
        self.refresh_header()
        self.show_screen("bank")

    def _open_fd(self, amt_str):
        try:
            amt = float(amt_str)
        except ValueError:
            amt = -1
        ok, msg = self.gs.open_fd(amt) if amt > 0 else (False, "Enter a valid amount.")
        self.play("coin" if ok else "error")
        self.toast("FD" if ok else "Failed", msg, accent=th.NEON_GREEN if ok else th.RED)
        self.refresh_header()
        self.show_screen("bank")

    # ------------------------------------------------------------------
    # SCREEN: EMPLOYEES
    # ------------------------------------------------------------------
    def _screen_employees(self, parent):
        self._current_screen = "employees"
        gs = self.gs
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        tk.Label(wrap, text="\U0001F468\u200D\U0001F4BC Employees", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w", pady=(0, 10))

        top = tk.Frame(wrap, bg=th.BG)
        top.pack(fill="both", expand=True)

        # Hiring pool
        pool_card = card(top)
        pool_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        header_row = tk.Frame(pool_card, bg=th.BG_PANEL)
        header_row.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(header_row, text="\U0001F50E Candidates", bg=th.BG_PANEL, fg=th.NEON_CYAN,
                  font=th.FONT_SUBHEADER).pack(side="left")
        refresh_btn = tk.Button(header_row, text="Refresh", command=lambda: self.show_screen("employees"))
        th.style_button(refresh_btn, accent=th.NEON_CYAN)
        refresh_btn.pack(side="right")

        if not hasattr(self, "_hire_pool") or not self._hire_pool:
            self._hire_pool = gs.hire_pool(3)

        for i, emp in enumerate(self._hire_pool):
            row = tk.Frame(pool_card, bg=th.BG_PANEL_2)
            row.pack(fill="x", padx=12, pady=4)
            info = tk.Frame(row, bg=th.BG_PANEL_2)
            info.pack(side="left", fill="x", expand=True, padx=8, pady=6)
            tk.Label(info, text=f"{emp['name']} — {emp['role']}", bg=th.BG_PANEL_2, fg=th.WHITE,
                      font=th.FONT_BOLD).pack(anchor="w")
            tk.Label(info, text=f"Skill {emp['skill']}  |  {emp['personality']}  |  "
                                 f"Salary {fmt_money(emp['salary'])}/day",
                      bg=th.BG_PANEL_2, fg=th.GREY, font=th.FONT_SMALL).pack(anchor="w")
            hire_btn = tk.Button(row, text="Hire", command=lambda i=i: self._hire(i))
            th.style_button(hire_btn)
            hire_btn.pack(side="right", padx=8)

        # Current staff
        staff_card = card(top)
        staff_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(staff_card, text=f"\U0001F465 Your Staff ({len(gs.employees)})", bg=th.BG_PANEL,
                  fg=th.NEON_GREEN, font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 6))
        if not gs.employees:
            tk.Label(staff_card, text="You haven't hired anyone yet.", bg=th.BG_PANEL, fg=th.GREY,
                      font=th.FONT_SMALL).pack(anchor="w", padx=14)
        for idx, e in enumerate(gs.employees):
            row = tk.Frame(staff_card, bg=th.BG_PANEL_2)
            row.pack(fill="x", padx=12, pady=4)
            info = tk.Frame(row, bg=th.BG_PANEL_2)
            info.pack(side="left", fill="x", expand=True, padx=8, pady=6)
            tk.Label(info, text=f"{e.data['name']} — {e.data['role']}", bg=th.BG_PANEL_2, fg=th.WHITE,
                      font=th.FONT_BOLD).pack(anchor="w")
            tk.Label(info, text=f"Skill {e.data['skill']}  |  Mood {e.data['mood']}%  |  "
                                 f"{e.data['personality']}  |  Salary {fmt_money(e.data['salary'])}/day",
                      bg=th.BG_PANEL_2, fg=th.GREY, font=th.FONT_SMALL).pack(anchor="w")
            fire_btn = tk.Button(row, text="Fire", command=lambda i=idx: self._fire(i))
            th.style_button(fire_btn, accent=th.RED)
            fire_btn.pack(side="right", padx=8)

    def _hire(self, pool_index):
        emp = self._hire_pool.pop(pool_index)
        self.gs.hire_employee(emp)
        self.gs.check_all_achievements()
        self.play("coin")
        self.toast("Hired!", f"{emp['name']} joined as {emp['role']}.", accent=th.NEON_GREEN)
        self.refresh_header()
        self.show_screen("employees")

    def _fire(self, index):
        self.gs.fire_employee(index)
        self.play("click")
        self.refresh_header()
        self.show_screen("employees")

    # ------------------------------------------------------------------
    # SCREEN: LEDGER (daily income vs expense)
    # ------------------------------------------------------------------
    def _screen_ledger(self, parent):
        self._current_screen = "ledger"
        gs = self.gs
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        tk.Label(wrap, text="\U0001F4D2 Daily Ledger", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w", pady=(0, 4))
        tk.Label(wrap, text="See exactly how much came in and went out each day.", bg=th.BG, fg=th.GREY,
                  font=th.FONT_SMALL).pack(anchor="w", pady=(0, 10))

        recent = list(reversed(gs.ledger[-30:]))
        if recent:
            total_income = sum(e["income"] for e in recent)
            total_expense = sum(e["expense"] for e in recent)
            summary_card = card(wrap)
            summary_card.pack(fill="x", pady=(0, 10))
            tk.Label(summary_card, text=f"Last {len(recent)} days — Income: {fmt_money(total_income)}   "
                                         f"|   Expense: {fmt_money(total_expense)}   |   "
                                         f"Net: {fmt_money(total_income - total_expense)}",
                      bg=th.BG_PANEL, fg=th.NEON_YELLOW, font=th.FONT_BOLD).pack(anchor="w", padx=14, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Ledger.Treeview", background=th.BG_PANEL, fieldbackground=th.BG_PANEL,
                        foreground=th.WHITE, rowheight=26, font=th.FONT_SMALL, borderwidth=0)
        style.configure("Ledger.Treeview.Heading", background=th.BG_PANEL_2, foreground=th.NEON_GREEN,
                        font=th.FONT_BOLD)

        cols = ("day", "year", "income", "expense", "net")
        tree = ttk.Treeview(wrap, columns=cols, show="headings", style="Ledger.Treeview", height=16)
        for c, label, w in [("day", "Day", 80), ("year", "Year", 80), ("income", "Income", 160),
                             ("expense", "Expense", 160), ("net", "Net", 160)]:
            tree.heading(c, text=label)
            tree.column(c, width=w, anchor="w")
        tree.pack(fill="both", expand=True)

        if not recent:
            tk.Label(wrap, text="No days recorded yet — advance a day to see your ledger.",
                      bg=th.BG, fg=th.GREY, font=th.FONT_SMALL).pack(anchor="w", pady=10)
        for e in recent:
            net = e["net"]
            iid = tree.insert("", "end", values=(e["day"], e["year"], fmt_money(e["income"]),
                                                   fmt_money(e["expense"]), fmt_money(net)))
            tree.tag_configure(iid, foreground=th.NEON_GREEN if net >= 0 else th.RED)
            tree.item(iid, tags=(iid,))

    # ------------------------------------------------------------------
    # SCREEN: NEWS & EVENTS
    # ------------------------------------------------------------------
    def _screen_news(self, parent):
        self._current_screen = "news"
        gs = self.gs
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        tk.Label(wrap, text="\U0001F4F0 News & World Events", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w", pady=(0, 10))

        cols = tk.Frame(wrap, bg=th.BG)
        cols.pack(fill="both", expand=True)

        news_card = card(cols)
        news_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(news_card, text="Headlines", bg=th.BG_PANEL, fg=th.NEON_CYAN,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 6))
        news_list = tk.Listbox(news_card, bg=th.BG, fg=th.WHITE, font=th.FONT_SMALL,
                                highlightthickness=0, bd=0)
        news_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        for h in gs.news_log:
            news_list.insert("end", "  " + h)
        for h in random.sample(gd.FLAVOR_NEWS, min(4, len(gd.FLAVOR_NEWS))):
            news_list.insert("end", "  " + h)

        event_card = card(cols)
        event_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(event_card, text="World Events Log", bg=th.BG_PANEL, fg=th.NEON_PINK,
                  font=th.FONT_SUBHEADER).pack(anchor="w", padx=14, pady=(10, 6))
        event_list = tk.Listbox(event_card, bg=th.BG, fg=th.WHITE, font=th.FONT_SMALL,
                                 highlightthickness=0, bd=0)
        event_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        for ev in gs.event_log:
            line = f"{ev['name']}: {ev['text']}"
            event_list.insert("end", "  " + line)
            for impact in ev["impact"]:
                event_list.insert("end", "     -> " + impact)
        if not gs.event_log:
            event_list.insert("end", "  No world events yet.")

    # ------------------------------------------------------------------
    # SCREEN: ACHIEVEMENTS
    # ------------------------------------------------------------------
    def _screen_achievements(self, parent):
        self._current_screen = "achievements"
        gs = self.gs
        gs.check_all_achievements()
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        tk.Label(wrap, text="\U0001F3C6 Achievements", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w", pady=(0, 10))

        grid = tk.Frame(wrap, bg=th.BG)
        grid.pack(fill="both", expand=True)
        for i, a in enumerate(gd.ACHIEVEMENTS):
            unlocked = a["key"] in gs.achievements_unlocked
            c = card(grid)
            c.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="nsew")
            accent = th.NEON_YELLOW if unlocked else th.GREY
            icon = "\U0001F3C6" if unlocked else "\U0001F512"
            tk.Label(c, text=f"{icon} {a['name']}", bg=th.BG_PANEL, fg=accent,
                      font=th.FONT_SUBHEADER).pack(anchor="w", padx=12, pady=(10, 2))
            tk.Label(c, text=a["desc"], bg=th.BG_PANEL, fg=th.GREY if unlocked else "#556",
                      font=th.FONT_SMALL, wraplength=220, justify="left").pack(anchor="w", padx=12, pady=(0, 10))
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1, uniform="ach")

    # ------------------------------------------------------------------
    # SCREEN: LEADERBOARD (all users, net worth by year)
    # ------------------------------------------------------------------
    def _screen_leaderboard(self, parent):
        self._current_screen = "leaderboard"
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        tk.Label(wrap, text="\U0001F947 Leaderboard", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w", pady=(0, 4))
        tk.Label(wrap, text="Net worth of every player, broken down by in-game year.", bg=th.BG,
                  fg=th.GREY, font=th.FONT_SMALL).pack(anchor="w", pady=(0, 10))

        rows = []  # (username, id, year, net_worth)
        for u in gd.all_users():
            path = os.path.join(SAVE_DIR, u.get("save_file", ""))
            if not os.path.exists(path):
                continue
            try:
                data = GameState.load(path)
            except Exception:
                continue
            nby = data.networth_by_year or {str(data.year): data.net_worth()}
            for year, nw in nby.items():
                rows.append((u["username"], u["id"], year, nw))
        rows.sort(key=lambda r: (-r[3]))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Board.Treeview", background=th.BG_PANEL, fieldbackground=th.BG_PANEL,
                        foreground=th.WHITE, rowheight=26, font=th.FONT_SMALL, borderwidth=0)
        style.configure("Board.Treeview.Heading", background=th.BG_PANEL_2, foreground=th.NEON_GREEN,
                        font=th.FONT_BOLD)

        cols = ("rank", "username", "id", "year", "net_worth")
        tree = ttk.Treeview(wrap, columns=cols, show="headings", style="Board.Treeview", height=18)
        for c, label, w in [("rank", "#", 50), ("username", "Player", 180), ("id", "User ID", 100),
                             ("year", "Year", 80), ("net_worth", "Net Worth", 200)]:
            tree.heading(c, text=label)
            tree.column(c, width=w, anchor="w")
        tree.pack(fill="both", expand=True)

        if not rows:
            tk.Label(wrap, text="No players yet.", bg=th.BG, fg=th.GREY, font=th.FONT_SMALL).pack(
                anchor="w", pady=10)
        for i, (uname, uid, year, nw) in enumerate(rows, start=1):
            is_me = uid == self.user.get("id")
            iid = tree.insert("", "end", values=(i, uname + ("  (you)" if is_me else ""), uid, year, fmt_money(nw)))
            tree.tag_configure(iid, foreground=th.NEON_YELLOW if is_me else th.WHITE)
            tree.item(iid, tags=(iid,))

    # ------------------------------------------------------------------
    # SCREEN: SETTINGS
    # ------------------------------------------------------------------
    def _screen_settings(self, parent):
        self._current_screen = "settings"
        gs = self.gs
        wrap = tk.Frame(parent, bg=th.BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=14)

        tk.Label(wrap, text="\u2699\uFE0F Settings", bg=th.BG, fg=th.NEON_GREEN,
                  font=th.FONT_HEADER).pack(anchor="w", pady=(0, 14))

        c = card(wrap)
        c.pack(fill="x", pady=(0, 10))

        sound_var = tk.BooleanVar(value=gs.sound_on)
        music_var = tk.BooleanVar(value=gs.music_on)

        def toggle_sound():
            gs.sound_on = sound_var.get()
            if gs.sound_on:
                self.play("click")

        def toggle_music():
            gs.music_on = music_var.get()
            sm.set_ambient_enabled(gs.music_on)

        sound_chk = tk.Checkbutton(c, text="Sound Effects", variable=sound_var, command=toggle_sound,
                                    bg=th.BG_PANEL, fg=th.WHITE, selectcolor=th.BG,
                                    activebackground=th.BG_PANEL, font=th.FONT_NORMAL)
        sound_chk.pack(anchor="w", padx=16, pady=8)
        music_chk = tk.Checkbutton(c, text="Ambient Music", variable=music_var, command=toggle_music,
                                    bg=th.BG_PANEL, fg=th.WHITE, selectcolor=th.BG,
                                    activebackground=th.BG_PANEL, font=th.FONT_NORMAL)
        music_chk.pack(anchor="w", padx=16, pady=(0, 12))

        c2 = card(wrap)
        c2.pack(fill="x", pady=10)
        tk.Label(c2, text="Account", bg=th.BG_PANEL, fg=th.NEON_CYAN, font=th.FONT_SUBHEADER).pack(
            anchor="w", padx=16, pady=(10, 6))
        tk.Label(c2, text=f"Username: {self.user.get('username')}\nUser ID: {self.user.get('id')}",
                  bg=th.BG_PANEL, fg=th.WHITE, font=th.FONT_SMALL, justify="left").pack(
            anchor="w", padx=16, pady=(0, 10))
        new_btn = tk.Button(c2, text="\u267B New Game (keep account)", command=self._new_game)
        th.style_button(new_btn, accent=th.NEON_YELLOW)
        new_btn.pack(anchor="w", padx=16, pady=6)
        save_btn = tk.Button(c2, text="\U0001F4BE Save Game", command=self.save_game)
        th.style_button(save_btn)
        save_btn.pack(anchor="w", padx=16, pady=6)
        logout_btn = tk.Button(c2, text="\U0001F6AA Logout", command=self.logout)
        th.style_button(logout_btn, accent=th.RED)
        logout_btn.pack(anchor="w", padx=16, pady=(6, 16))

        about = card(wrap)
        about.pack(fill="x", pady=10)
        tk.Label(about, text="About", bg=th.BG_PANEL, fg=th.NEON_PINK, font=th.FONT_SUBHEADER).pack(
            anchor="w", padx=16, pady=(10, 6))
        tk.Label(about, text="Shadow Market: Rise to Billionaire\nStart with \u20B910,000. "
                              "End as the richest person on Earth... if you survive.",
                  bg=th.BG_PANEL, fg=th.GREY, font=th.FONT_SMALL, justify="left").pack(
            anchor="w", padx=16, pady=(0, 14))

    def _new_game(self):
        if messagebox.askyesno("New Game", "Start a new game? Your current progress will be lost unless saved."):
            self.gs = GameState()
            self._hire_pool = []
            self.play("notify")
            self.show_screen("home")




# =============================================================================
# ENTRY POINT
# =============================================================================
def main():
    # Loop so that logging out returns to the login screen instead of
    # closing the whole program.
    while True:
        login = LoginWindow()
        login.mainloop()
        user = login.logged_in_user
        if user is None:
            break  # window closed without logging in
        app = App(user)
        app.mainloop()
        if not app.should_return_to_login:
            break


if __name__ == "__main__":
    main()