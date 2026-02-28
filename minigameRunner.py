import tkinter as tk
import importlib
import os
import random
import pygame


class GameHandler:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Race: Mini-Game Station")
        self.root.geometry("800x600")
        self.root.configure(bg="black")

        # Initialize Pygame for calibration
        pygame.init()
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joy in self.joysticks:
            joy.init()

        self.game_frame = tk.Frame(self.root, bg="black")
        self.game_frame.pack(expand=True, fill="both")

        self.games_dir = "minigames"
        self.refresh_game_list()

        # Start the flow
        self.show_calibration()

    def refresh_game_list(self):
        """Finds all games and shuffles them for a random loop."""
        self.game_list = [f[:-3] for f in os.listdir(self.games_dir) if f.endswith(".py") and f != "__init__.py"]
        random.shuffle(self.game_list)
        self.current_game_index = 0

    def clear_frame(self):
        for widget in self.game_frame.winfo_children():
            widget.destroy()

    def show_calibration(self):
        self.clear_frame()
        self.ready_state = {"Team A": False, "Team B": False}

        tk.Label(self.game_frame, text="CONTROLLER CALIBRATION", font=("Arial", 30, "bold"), fg="white",
                 bg="black").pack(pady=40)

        self.status_a = tk.Label(self.game_frame, text="Team A: PRESS 'A' TO READY", font=("Arial", 20), fg="red",
                                 bg="black")
        self.status_a.pack(pady=10)

        self.status_b = tk.Label(self.game_frame, text="Team B: PRESS 'A' TO READY", font=("Arial", 20), fg="red",
                                 bg="black")
        self.status_b.pack(pady=10)

        self.check_calibration_input()

    def check_calibration_input(self):
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 0:  # Button A
                if event.joy == 0:
                    self.ready_state["Team A"] = True
                    self.status_a.config(text="Team A: READY!", fg="green")
                if event.joy == 1:
                    self.ready_state["Team B"] = True
                    self.status_b.config(text="Team B: READY!", fg="green")

        if self.ready_state["Team A"] and self.ready_state["Team B"]:
            self.root.after(1000, lambda: self.start_countdown(3))
        else:
            self.root.after(20, self.check_calibration_input)

    def start_countdown(self, count):
        self.clear_frame()
        if count > 0:
            lbl = tk.Label(self.game_frame, text=str(count), font=("Arial", 100, "bold"), fg="yellow", bg="black")
            lbl.pack(expand=True)
            self.root.after(1000, lambda: self.start_countdown(count - 1))
        else:
            self.start_next_game()

    def start_next_game(self):
        self.clear_frame()

        # Infinite Loop Logic
        if self.current_game_index >= len(self.game_list):
            self.refresh_game_list()  # Re-shuffle and restart

        module_name = f"{self.games_dir}.{self.game_list[self.current_game_index]}"
        game_module = importlib.import_module(module_name)
        importlib.reload(game_module)

        # Launch module
        game_module.start_game(self.game_frame, self.handle_winner)

    def handle_winner(self, winner):
        print(f"WINNER: {winner}")

        # Display Winner Briefly
        self.clear_frame()
        tk.Label(self.game_frame, text=f"{winner} WINS!", font=("Arial", 50, "bold"), fg="gold", bg="black").pack(
            expand=True)

        # Move to next game after 2 seconds
        self.current_game_index += 1
        self.root.after(2000, self.show_calibration)


if __name__ == "__main__":
    root = tk.Tk()
    app = GameHandler(root)
    root.mainloop()