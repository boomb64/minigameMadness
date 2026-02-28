import tkinter as tk
import importlib
import os
import random
import pygame
import socket

# --- NETWORK CONFIGURATION ---
PI_IPS = {
    "Team A": "10.35.147.5",  # Blue Car Pi
    "Team B": "192.168.1.11"  # Pink Car Pi
}
UDP_PORT = 5005


class GameHandler:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Race: minigameRunner.py")
        self.root.geometry("850x750")
        self.root.configure(bg="black")

        pygame.init()
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joy in self.joysticks:
            joy.init()

        self.total_wins = {"Team A": 0, "Team B": 0}
        self.games_dir = "minigames"

        # Weighted Random System
        self.game_weights = {}
        self.initialize_weights()

        # UI Layout
        self.header = tk.Frame(self.root, bg="#111", height=60)
        self.header.pack(side="top", fill="x")

        self.score_label = tk.Label(
            self.header,
            text="Team A: 0  |  Team B: 0",
            font=("Courier", 22, "bold"),
            fg="yellow", bg="#111"
        )
        self.score_label.pack(pady=10)

        self.game_frame = tk.Frame(self.root, bg="black")
        self.game_frame.pack(expand=True, fill="both")

        self.show_calibration()

    def initialize_weights(self):
        """Finds all games and sets their initial priority."""
        if not os.path.exists(self.games_dir):
            os.makedirs(self.games_dir)

        all_games = [f[:-3] for f in os.listdir(self.games_dir) if f.endswith(".py") and f != "__init__.py"]
        for game in all_games:
            if game not in self.game_weights:
                self.game_weights[game] = 10

    def pick_next_game(self):
        """Weighted selection: resets winner weight to 1, increases others by 1."""
        self.initialize_weights()
        population = list(self.game_weights.keys())
        weights = list(self.game_weights.values())

        if not population:
            print("ERROR: No minigames found in the /minigames folder!")
            return None

        selection = random.choices(population, weights=weights, k=1)[0]

        # Slow Weight Pressure: Make others slightly more likely next time
        for game in self.game_weights:
            if game == selection:
                self.game_weights[game] = 1
            else:
                self.game_weights[game] += 1  # Increments by only 1 now

        return selection

    def send_win_network_signal(self, winner):
        if winner in PI_IPS:
            try:
                ip = PI_IPS[winner]
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(b"WIN", (ip, UDP_PORT))
                print(f"NETWORK: Win signal sent to {winner}")
            except Exception as e:
                print(f"NETWORK ERROR: {e}")

    def update_score_display(self):
        self.score_label.config(text=f"Team A: {self.total_wins['Team A']}  |  Team B: {self.total_wins['Team B']}")

    def clear_frame(self):
        for widget in self.game_frame.winfo_children():
            widget.destroy()

    def show_calibration(self):
        self.clear_frame()
        self.ready_state = {"Team A": False, "Team B": False}
        tk.Label(self.game_frame, text="INITIAL SETUP", font=("Arial", 32, "bold"), fg="white", bg="black").pack(
            pady=40)

        self.status_a = tk.Label(self.game_frame, text="Team A (BLUE): PRESS 'A'", font=("Arial", 22), fg="#0074D9",
                                 bg="black")
        self.status_a.pack(pady=20)
        self.status_b = tk.Label(self.game_frame, text="Team B (PINK): PRESS 'A'", font=("Arial", 22), fg="#F012BE",
                                 bg="black")
        self.status_b.pack(pady=20)
        self.check_calibration_input()

    def check_calibration_input(self):
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                if event.joy == 0:
                    self.ready_state["Team A"] = True
                    self.status_a.config(text="Team A: CONNECTED", fg="cyan")
                if event.joy == 1:
                    self.ready_state["Team B"] = True
                    self.status_b.config(text="Team B: CONNECTED", fg="magenta")

        if self.ready_state["Team A"] and self.ready_state["Team B"]:
            self.root.after(1000, lambda: self.start_one_time_countdown(3))
        else:
            self.root.after(20, self.check_calibration_input)

    def start_one_time_countdown(self, count):
        self.clear_frame()
        if count > 0:
            lbl = tk.Label(self.game_frame, text=str(count), font=("Arial", 120, "bold"), fg="white", bg="black")
            lbl.pack(expand=True)
            self.root.after(1000, lambda: self.start_one_time_countdown(count - 1))
        else:
            self.launch_game()

    def launch_game(self):
        self.clear_frame()
        current_game = self.pick_next_game()

        if not current_game: return

        module_name = f"{self.games_dir}.{current_game}"
        game_module = importlib.import_module(module_name)
        importlib.reload(game_module)

        game_module.start_game(self.game_frame, self.handle_winner)

    def handle_winner(self, winner):
        self.clear_frame()

        # Support for different winner string formats
        if "Player 1" in winner or "Blue" in winner: winner = "Team A"
        if "Player 2" in winner or "Pink" in winner: winner = "Team B"

        if "Tie" in winner:
            tk.Label(self.game_frame, text="IT'S A TIE!", font=("Arial", 48, "bold"), fg="yellow", bg="black").pack(
                expand=True)
        else:
            if winner in self.total_wins:
                self.total_wins[winner] += 1
                self.update_score_display()
                self.send_win_network_signal(winner)

            color = "#0074D9" if winner == "Team A" else "#F012BE"
            tk.Label(self.game_frame, text=f"{winner.upper()} SCORES!", font=("Arial", 48, "bold"), fg=color,
                     bg="black").pack(expand=True)

        self.root.after(2500, self.launch_game)


if __name__ == "__main__":
    root = tk.Tk()
    app = GameHandler(root)
    root.mainloop()