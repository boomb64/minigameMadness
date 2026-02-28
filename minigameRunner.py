import tkinter as tk
import importlib
import os
import random
import pygame
import socket

# --- NETWORK CONFIGURATION ---
# Replace these with the static IPs of your Raspberry Pis
PI_IPS = {
    "Team A": "10.35.147.5",  # Blue Car Pi
    "Team B": "192.168.1.11"  # Pink Car Pi
}
UDP_PORT = 5005


class GameHandler:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Race: Mini-Game Station")
        self.root.geometry("800x600")
        self.root.configure(bg="black")

        # Initialize Pygame for controllers
        pygame.init()
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joy in self.joysticks:
            joy.init()

        # Persistent Stats (Wins Counter)
        self.total_wins = {"Team A": 0, "Team B": 0}

        # UI Layout
        self.header = tk.Frame(self.root, bg="#111", height=50)
        self.header.pack(side="top", fill="x")

        # Applied Color Rule: Team A = Blue, Team B = Pink
        self.score_label = tk.Label(
            self.header,
            text="Team A: 0  |  Team B: 0",
            font=("Courier", 18, "bold"),
            fg="yellow", bg="#111"
        )
        self.score_label.pack(pady=10)

        self.game_frame = tk.Frame(self.root, bg="black")
        self.game_frame.pack(expand=True, fill="both")

        self.games_dir = "minigames"
        self.game_list = []
        self.current_game_index = 0

        self.show_calibration()

    def send_win_network_signal(self, winner):
        """Sends a UDP packet to the winning car's Pi to increment its permanent speed."""
        if winner in PI_IPS:
            try:
                ip = PI_IPS[winner]
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(b"WIN", (ip, UDP_PORT))
                print(f"NETWORK: Win signal sent to {winner} at {ip}")
            except Exception as e:
                print(f"NETWORK ERROR: Could not reach {winner} - {e}")

    def update_score_display(self):
        self.score_label.config(text=f"Team A: {self.total_wins['Team A']}  |  Team B: {self.total_wins['Team B']}")

    def refresh_game_list(self):
        all_games = [f[:-3] for f in os.listdir(self.games_dir) if f.endswith(".py") and f != "__init__.py"]
        last_game = self.game_list[-1] if self.game_list else None
        random.shuffle(all_games)
        if len(all_games) > 1 and all_games[0] == last_game:
            all_games.append(all_games.pop(0))
        self.game_list = all_games
        self.current_game_index = 0

    def clear_frame(self):
        for widget in self.game_frame.winfo_children():
            widget.destroy()

    def show_calibration(self):
        self.clear_frame()
        self.ready_state = {"Team A": False, "Team B": False}
        tk.Label(self.game_frame, text="INITIAL SETUP", font=("Arial", 32, "bold"), fg="white", bg="black").pack(
            pady=40)

        # Color Rule applied to calibration
        self.status_a = tk.Label(self.game_frame, text="Team A (BLUE): PRESS 'A'", font=("Arial", 22), fg="dodger blue",
                                 bg="black")
        self.status_a.pack(pady=20)
        self.status_b = tk.Label(self.game_frame, text="Team B (PINK): PRESS 'A'", font=("Arial", 22), fg="pink",
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
            self.refresh_game_list()
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
        if self.current_game_index >= len(self.game_list):
            self.refresh_game_list()
        module_name = f"{self.games_dir}.{self.game_list[self.current_game_index]}"
        game_module = importlib.import_module(module_name)
        importlib.reload(game_module)
        game_module.start_game(self.game_frame, self.handle_winner)

    def handle_winner(self, winner):
        self.clear_frame()
        if winner == "Tie":
            tk.Label(self.game_frame, text="IT'S A TIE!", font=("Arial", 48, "bold"), fg="yellow", bg="black").pack(
                expand=True)
        else:
            if winner in self.total_wins:
                self.total_wins[winner] += 1
                self.update_score_display()

                # --- NEW: PUSH WIN TO HARDWARE VIA NETWORK ---
                self.send_win_network_signal(winner)

            color = "dodger blue" if winner == "Team A" else "pink"
            tk.Label(self.game_frame, text=f"{winner.upper()} SCORES!", font=("Arial", 48, "bold"), fg=color,
                     bg="black").pack(expand=True)

        self.current_game_index += 1
        self.root.after(2000, self.launch_game)


if __name__ == "__main__":
    root = tk.Tk()
    app = GameHandler(root)
    root.mainloop()