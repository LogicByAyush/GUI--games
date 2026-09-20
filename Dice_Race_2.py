import tkinter as tk
import random

class DiceGame:
    def __init__(self, root):
        self.root=root
        self.root.title("Dice Race Game")
        self.root.geometry("700x650")

        self.players=[]
        self.scores=[]
        self.winners=[]

        self.setup_screen()

    def setup_screen(self):
        tk.Label(
            self.root,
            text="🎲 Dice Race Game 🎲",
            font=("Arial",18)
        ).pack(pady=10)

        tk.Label(
            self.root,
            text="How many players?"
        ).pack()

        self.player_entry=tk.Entry(self.root)
        self.player_entry.pack()

        tk.Label(
            self.root,
            text="Final Score"
        ).pack()

        self.target_entry=tk.Entry(self.root)
        self.target_entry.pack()

        tk.Button(
            self.root,
            text="Start Game",
            command=self.start_game
        ).pack(pady=10)

    def start_game(self):
        count=int(self.player_entry.get())
        self.target=int(self.target_entry.get())
        self.clear()
        self.name_entries=[]

        tk.Label(
            self.root,
            text="Enter Player Names",
            font=("Arial",15)
        ).pack()

        for i in range(count):
            e=tk.Entry(self.root)
            e.insert(0,f"Player {i+1}")
            e.pack()
            self.name_entries.append(e)

        tk.Button(
            self.root,
            text="Start",
            command=self.create_game
        ).pack(pady=10)

    def create_game(self):
        if hasattr(self,"name_entries"):
            self.players=[]

            for e in self.name_entries:
                self.players.append(e.get())

        self.scores=[0]*len(self.players)
        self.winners=[]
        self.turn=0
        self.clear()

        self.turn_label=tk.Label(
            self.root,
            text="",
            font=("Arial",16)
        )
        self.turn_label.pack(pady=10)
        self.player_frame=tk.Frame(self.root)
        self.player_frame.pack(pady=20)
        self.player_labels=[]
        self.roll_buttons=[]

        for i in range(len(self.players)):
            frame=tk.Frame(self.player_frame)
            frame.grid(
                row=0,
                column=i,
                padx=15
            )
            lbl=tk.Label(
                frame,
                text=f"⚪\n{self.players[i]}",
                font=("Arial",13),
                width=10,
                height=3,
                relief="ridge"
            )
            lbl.pack()
            btn=tk.Button(
                frame,
                text=f"Roll {self.players[i]} 🎲",
                command=lambda x=i:self.player_roll(x)
            )
            btn.pack()

            self.player_labels.append(lbl)
            self.roll_buttons.append(btn)

        self.dice_label=tk.Label(
            self.root,
            text="Dice : -",
            font=("Arial",30)
        )
        self.dice_label.pack(pady=10)
        self.score_label=tk.Label(
            self.root,
            text="",
            font=("Arial",12)
        )
        self.score_label.pack()
        self.update_screen()

    def player_roll(self,player):
        if player!=self.turn:
            return

        self.animate_dice(player)

    def animate_dice(self,player):
        self.disable_buttons()
        count=0
        def rolling():
            nonlocal count
            if count<5:
                self.dice_label.config(
                    text=f"🎲 {random.randint(1,6)}"
                )
                count+=1
                self.root.after(
                    100,
                    rolling
                )
            else:
                self.final_roll(player)
        rolling()

    def final_roll(self,player):
        dice=random.randint(1,6)
        self.scores[player]+=dice
        self.dice_label.config(
            text=f"🎲 {dice}"
        )
        if self.scores[player]>=self.target:
            if player not in self.winners:
                self.winners.append(player)

        if len(self.winners)==len(self.players):
            self.game_over()
            return

        self.next_player()
        self.enable_buttons()
        self.update_screen()

    def disable_buttons(self):
        for b in self.roll_buttons:
            b.config(
                state="disabled"
            )

    def enable_buttons(self):
        for i,b in enumerate(self.roll_buttons):
            if i in self.winners:
                b.config(
                    state="disabled"
                )
            else:
                b.config(
                    state="normal"
                )

    def next_player(self):
        self.turn+=1
        if self.turn>=len(self.players):
            self.turn=0

        while self.turn in self.winners:
            self.turn+=1
            if self.turn>=len(self.players):
                self.turn=0

    def update_screen(self):
        self.turn_label.config(
            text=f"🎲 Turn : {self.players[self.turn]}"
        )

        for i in range(len(self.players)):
            if i in self.winners:
                pos=self.winners.index(i)+1
                self.player_labels[i].config(
                    text=f"🏆 {pos}\n{self.players[i]}"
                )

            elif i==self.turn:
                self.player_labels[i].config(
                    text=f"🎲\n{self.players[i]}"
                )
            else:
                self.player_labels[i].config(
                    text=f"⚪\n{self.players[i]}"
                )

        text="========== SCORE BOARD ==========\n\n"

        for i in self.winners:
            pos=self.winners.index(i)+1
            text+=(
                f"{pos} Position : "
                f"{self.players[i]} "
                f"({self.scores[i]}) 🏆\n"
            )
        text+="\n"

        for i in range(len(self.players)):
            if i not in self.winners:
                text+=(
                    f"{self.players[i]} : "
                    f"{self.scores[i]}\n"
                )

        text+="================================"

        self.score_label.config(
            text=text
        )

    def game_over(self):
        self.disable_buttons()
        result="🏁 GAME OVER 🏁\n\n"

        for i,p in enumerate(self.winners):
            result+=(
                f"{i+1} Position : "
                f"{self.players[p]} "
                f"({self.scores[p]})\n"
            )

        self.turn_label.config(
            text=result
        )

        tk.Button(
            self.root,
            text="🔄 Play Again",
            font=("Arial",14),
            command=self.play_again
        ).pack(pady=20)

    def play_again(self):
        self.scores=[0]*len(self.players)
        self.winners=[]
        self.turn=0
        self.clear()
        self.create_game()

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

root=tk.Tk()
game=DiceGame(root)
root.mainloop()