import tkinter as tk
from tkinter import ttk
import random
import os
from datetime import datetime
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
HISTORY_FILE = "history.csv"
HISTORY_COLUMNS = ["DateTime", "Level", "Secret", "Result", "MovesUsed", "Score", "Guesses"]

LEVEL_RANGE = {"easy": (1, 50), "medium": (1, 100), "hard": (1, 500)}
LEVEL_BASE_SCORE = {"easy": 50, "medium": 100, "hard": 200}

secret = None
moves = 10
level_selected = False
last_guesses = []
all_guesses = []
current_level = None
start_time = None


# ---------------------------------------------------------------------------
# PANDAS HELPERS
# ---------------------------------------------------------------------------
def load_history():
    """Load history.csv as a DataFrame, creating it if it doesn't exist."""
    if not os.path.exists(HISTORY_FILE):
        df = pd.DataFrame(columns=HISTORY_COLUMNS)
        df.to_csv(HISTORY_FILE, index=False)
        return df
    try:
        return pd.read_csv(HISTORY_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=HISTORY_COLUMNS)


def save_record(level, secret_num, result, moves_used, score, guesses):
    """Append one game record to history.csv using pandas."""
    df = load_history()
    new_row = {
        "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Level": level,
        "Secret": secret_num,
        "Result": result,
        "MovesUsed": moves_used,
        "Score": score,
        "Guesses": " -> ".join(map(str, guesses)),
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(HISTORY_FILE, index=False)
    return df


def get_best_score():
    df = load_history()
    wins = df[df["Result"] == "Win"]
    if wins.empty:
        return 0
    return int(wins["Score"].max())


def get_top_10():
    df = load_history()
    wins = df[df["Result"] == "Win"].copy()
    if wins.empty:
        return wins
    wins.sort_values(by="Score", ascending=False, inplace=True)
    return wins.head(10).reset_index(drop=True)


def calculate_score(level, moves_left):
    """Higher difficulty + fewer moves used => higher score."""
    base = LEVEL_BASE_SCORE[level]
    return int(base * (moves_left + 1) / 10 * 10)


# ---------------------------------------------------------------------------
# GAME LOGIC
# ---------------------------------------------------------------------------
def start_game(level):
    global secret, moves, level_selected, last_guesses, all_guesses, current_level, start_time

    low, high = LEVEL_RANGE[level]
    secret = random.randint(low, high)
    moves = 10
    level_selected = True
    last_guesses = []
    all_guesses = []
    current_level = level
    start_time = datetime.now()

    info_label.config(text=f"Guess a number between {low} and {high}")
    move_label.config(text=f"Moves Left: {moves}")
    history_label.config(text="Last 3 Guesses: None")
    result_label.config(text="")
    guess_btn.config(state="normal")
    guess_entry.delete(0, tk.END)
    guess_entry.focus()
    refresh_best_score()


def end_game(result):
    """Called on win or loss to persist the record and refresh UI."""
    moves_used = 10 - moves if result == "Win" else 10
    score = calculate_score(current_level, moves) if result == "Win" else 0
    save_record(current_level, secret, result, moves_used, score, all_guesses)
    refresh_best_score()
    guess_btn.config(state="disabled")


def check_guess(event=None):
    global moves, last_guesses

    if not level_selected:
        result_label.config(text="⚠ Please select a level first!")
        return

    try:
        guess = int(guess_entry.get())
    except ValueError:
        result_label.config(text="❌ Enter a valid number!")
        return

    last_guesses.append(guess)
    all_guesses.append(guess)

    if len(last_guesses) > 3:
        last_guesses.pop(0)

    history_label.config(
        text="Last 3 Guesses: " + ", ".join(map(str, last_guesses))
    )

    diff = abs(secret - guess)

    if diff == 0:
        result_label.config(text="🎉 Congratulations! You Won!")
        end_game("Win")
        return

    elif diff <= 5:
        hint = "🎯 Extremely Close!"
    elif diff <= 10:
        hint = "🔥 Very Close!"
    elif diff <= 20:
        hint = "🔥 Close!"
    elif diff <= 50:
        hint = "🌤️ Far"
    else:
        hint = "📡 Very Far!"

    if guess < secret:
        result_label.config(text=f"{hint} ↑ Try Higher")
    else:
        result_label.config(text=f"{hint} ↓ Try Lower")

    moves -= 1
    move_label.config(text=f"Moves Left: {moves}")

    if moves == 0:
        result_label.config(text=f"😢 You Lost! Number was {secret}")
        end_game("Loss")

    guess_entry.delete(0, tk.END)


def restart_game():
    global secret, moves, level_selected, last_guesses, all_guesses, current_level

    secret = None
    moves = 10
    level_selected = False
    last_guesses = []
    all_guesses = []
    current_level = None

    info_label.config(text="Choose a level to start")
    move_label.config(text="Moves Left: 10")
    history_label.config(text="Last 3 Guesses: None")
    result_label.config(text="")
    guess_btn.config(state="normal")
    guess_entry.delete(0, tk.END)
    refresh_best_score()


def refresh_best_score():
    best_score_label.config(text=f"🏆 Best Score: {get_best_score()}")


# ---------------------------------------------------------------------------
# HISTORY / LEADERBOARD WINDOW
# ---------------------------------------------------------------------------
def show_history():
    top = tk.Toplevel(root)
    top.title("📜 Top 10 Leaderboard")
    top.geometry("560x400")
    top.resizable(False, False)

    tk.Label(
        top, text="🏆 Top 10 Best Scores", font=("Arial", 15, "bold")
    ).pack(pady=10)

    top10 = get_top_10()

    columns = ("Rank", "DateTime", "Level", "Secret", "MovesUsed", "Score")
    tree = ttk.Treeview(top, columns=columns, show="headings", height=10)

    widths = {"Rank": 45, "DateTime": 140, "Level": 70, "Secret": 60, "MovesUsed": 90, "Score": 70}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=widths[col], anchor="center")

    if top10.empty:
        tk.Label(
            top, text="No wins recorded yet. Play a game to get on the board!",
            font=("Arial", 11)
        ).pack(pady=20)
    else:
        for i, row in top10.iterrows():
            tree.insert(
                "", "end",
                values=(i + 1, row["DateTime"], row["Level"], row["Secret"],
                        row["MovesUsed"], row["Score"])
            )
        tree.pack(pady=10, padx=10, fill="both", expand=True)

    tk.Button(top, text="Close", command=top.destroy).pack(pady=10)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
root = tk.Tk()
root.title("Number Guessing Game")
root.geometry("500x560")
root.resizable(False, False)

title = tk.Label(root, text="🎯 Number Guessing Game", font=("Arial", 18, "bold"))
title.pack(pady=10)

best_score_label = tk.Label(root, text="🏆 Best Score: 0", font=("Arial", 11, "bold"), fg="#b8860b")
best_score_label.pack(pady=2)

info_label = tk.Label(root, text="Choose a level to start", font=("Arial", 12))
info_label.pack(pady=5)

level_frame = tk.Frame(root)
level_frame.pack(pady=10)

easy_btn = tk.Button(level_frame, text="Easy (1-50)", width=12, command=lambda: start_game("easy"))
easy_btn.grid(row=0, column=0, padx=5)

medium_btn = tk.Button(level_frame, text="Medium (1-100)", width=12, command=lambda: start_game("medium"))
medium_btn.grid(row=0, column=1, padx=5)

hard_btn = tk.Button(level_frame, text="Hard (1-500)", width=12, command=lambda: start_game("hard"))
hard_btn.grid(row=0, column=2, padx=5)

move_label = tk.Label(root, text="Moves Left: 10", font=("Arial", 12, "bold"))
move_label.pack(pady=10)

guess_entry = tk.Entry(root, font=("Arial", 14), justify="center")
guess_entry.pack(pady=10)
guess_entry.bind("<Return>", check_guess)

guess_btn = tk.Button(root, text="Guess", font=("Arial", 12), command=check_guess)
guess_btn.pack(pady=5)

history_label = tk.Label(root, text="Last 3 Guesses: None", font=("Arial", 11))
history_label.pack(pady=15)

result_label = tk.Label(root, text="", font=("Arial", 13, "bold"))
result_label.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

restart_btn = tk.Button(btn_frame, text="🔄 Restart Game", font=("Arial", 12), command=restart_game)
restart_btn.grid(row=0, column=0, padx=5)

history_btn = tk.Button(btn_frame, text="📜 History (Top 10)", font=("Arial", 12), command=show_history)
history_btn.grid(row=0, column=1, padx=5)

refresh_best_score()

root.mainloop()