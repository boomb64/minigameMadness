import tkinter as tk
import importlib
import os


class GameHandler:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Race: Mini-Game Station")
        self.root.geometry("600x400")

        self.game_frame = tk.Frame(self.root)
        self.game_frame.pack(expand=True, fill="both")

        self.games_dir = "minigames"
        self.game_list = [f[:-3] for f in os.listdir(self.games_dir) if f.endswith(".py") and f != "__init__.py"]
        self.current_game_index = 0

        self.start_next_game()

    def start_next_game(self):
        if self.current_game_index >= len(self.game_list):
            print("All games finished!")
            return

        # Dynamically import the next game module
        module_name = f"{self.games_dir}.{self.game_list[self.current_game_index]}"
        game_module = importlib.import_module(module_name)
        importlib.reload(game_module)  # Vital for testing changes live

        # Launch the game
        game_module.start_game(self.game_frame, self.handle_winner)

    def handle_winner(self, winner):
        print(f"WINNER: {winner}")
        # --- THIS IS WHERE YOU PUSH TO YOUR VOLTAGE CONTROLLER / DATABASE ---
        # e.g., db.collection('race').document('status').update({f'{winner}_boost': True})

        self.current_game_index += 1
        self.start_next_game()


if __name__ == "__main__":
    root = tk.Tk()
    app = GameHandler(root)
    root.mainloop()