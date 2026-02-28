#DONT EDIT THIS. USE IT AS A TEMPLATE FOR EACH MINIGAME YOU MAKE. MAKE EACH MINIGAME WITHIN IN "minigames" FOLDER

import tkinter as tk

def start_game(parent_frame, on_game_over):
    """
    parent_frame: The Tkinter frame where the game lives.
    on_game_over: A callback function to send the winner back to the handler.
    """
    label = tk.Label(parent_frame, text="Mash 'A' to Win!", font=("Arial", 20))
    label.pack(pady=20)

    # Example: Simple button win
    def win(team_name):
        # Clear the frame for the next game
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(team_name)

    tk.Button(parent_frame, text="Team A", command=lambda: win("Team A")).pack(side="left", padx=50)
    tk.Button(parent_frame, text="Team B", command=lambda: win("Team B")).pack(side="right", padx=50)