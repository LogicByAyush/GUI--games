from tkinter import *
from tkinter import messagebox

player1 = input("Enter Player 1 Name (X): ")
player2 = input("Enter Player 2 Name (O): ")

root = Tk()
root.title(f"{player1} (X) vs {player2} (O)")
root.resizable(False, False)

current_player = "X"
board = [""] * 9

winning_combinations = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6]
]

def restart_game():
    global current_player, board

    current_player = "X"
    board = [""] * 9

    for button in buttons:
        button.config(text="", state=NORMAL)

    turn_label.config(text=f"{player1}'s Turn (X)")

def check_winner():
    for combo in winning_combinations:
        a, b, c = combo
        if (
            board[a] != ""
            and board[a] == board[b]
            and board[b] == board[c]
        ):
            return board[a]
    return None

def board_full():
    return "" not in board

def game_over(message):
    answer = messagebox.askyesno(
        "Game Over",
        f"{message}\n\nDo you want to play again?"
    )

    if answer:
        restart_game()
    else:
        root.destroy()

def button_click(index):
    global current_player

    if board[index] != "":
        return

    board[index] = current_player
    buttons[index].config(text=current_player)

    winner = check_winner()

    if winner:
        winner_name = player1 if winner == "X" else player2
        game_over(f"🎉 {winner_name} Wins!")
        return

    if board_full():
        game_over("🤝 Match Draw!")
        return

    if current_player == "X":
        current_player = "O"
        turn_label.config(text=f"{player2}'s Turn (O)")
    else:
        current_player = "X"
        turn_label.config(text=f"{player1}'s Turn (X)")

buttons = []

for i in range(9):
    button = Button(
        root,
        text="",
        font=("Arial", 24),
        width=5,
        height=2,
        command=lambda i=i: button_click(i)
    )
    button.grid(row=i // 3, column=i % 3)
    buttons.append(button)

turn_label = Label(root,text=f"{player1}'s Turn (X)",font=("Arial", 14))

turn_label.grid(row=3, column=0, columnspan=3, pady=10)

root.mainloop()