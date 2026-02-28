import tkinter as tk
import importlib
import os
import random
import pygame
import socket
import threading
import time

# --- NETWORK CONFIGURATION ---
PI_IPS = {
    "Team A": "10.35.147.5",  # Blue Car Pi
    "Team B": "10.35.147.199"  # Pink Car Pi
}
UDP_PORT = 5005


class GameHandler:
    def __init__(self, root):
        self.root = root
        self.root.title("Hardware Race Hub: minigameRunner.py")
        self.root.attributes("-fullscreen", True)  # Fullscreen for the hackathon
        self.root.configure(bg="black")

        pygame.init()
        pygame.joystick.init()
        self.refresh_joysticks()

        self.total_wins = {"Team A": 0, "Team B": 0}
        self.current_power = 0.4  # Starts low
        self.games_dir = "minigames"
        self.game_weights = {}
        self.initialize_weights()

        # UI Layout
        self.header = tk.Frame(self.root, bg="#111", height=80)
        self.header.pack(side="top", fill="x")

        self.score_label = tk.Label(
            self.header,
            text="BLUE: 0  |  PINK: 0",
            font=("Courier", 28, "bold"),
            fg="yellow", bg="#111"
        )
        self.score_label.pack(pady=15)

        self.game_frame = tk.Frame(self.root, bg="black")
        self.game_frame.pack(expand=True, fill="both")

        # --- START NETWORK DRIVE THREAD ---
        self.drive_active = True
        self.drive_thread = threading.Thread(target=self.network_drive_loop, daemon=True)
        self.drive_thread.start()

        self.show_calibration()

    def refresh_joysticks(self):
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joy in self.joysticks:
            joy.init()
        print(f"HUB: {len(self.joysticks)} Controllers detected.")

    def network_drive_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        def apply_deadzone(value, deadzone=0.20):
            return 0.0 if abs(value) < deadzone else value

        while self.drive_active:
            pygame.event.pump()

            # --- TEAM A (BLUE CAR) - Using Joystick 0 ---
            if len(self.joysticks) > 0:
                joy_x = apply_deadzone(self.joysticks[3].get_axis(0))
                joy_y = apply_deadzone(self.joysticks[3].get_axis(1))

                l_a, r_a = 0, 0
                if joy_y < -0.2:
                    l_a, r_a = -self.current_power, -self.current_power  # Forward
                elif joy_y > 0.2:
                    l_a, r_a = self.current_power, self.current_power  # Backward

                if joy_x > 0.2:
                    r_a = 0  # Turn Right
                elif joy_x < -0.2:
                    l_a = 0  # Turn Left

                packet = f"{l_a:.2f},{r_a:.2f}".encode('utf-8')
                try:
                    sock.sendto(packet, (PI_IPS["Team A"], UDP_PORT))
                except:
                    pass

            # --- TEAM B (PINK CAR) - Using Joystick 1 ---
            if len(self.joysticks) > 1:
                joy_x = apply_deadzone(self.joysticks[2].get_axis(0))
                joy_y = apply_deadzone(self.joysticks[2].get_axis(1))

                l_b, r_b = 0.0, 0.0
                # FIXED: Changed l_b to match r_b so they spin the same way for straight flight
                if joy_y < -0.2:
                    l_b, r_b = -self.current_power, -self.current_power  # Forward
                elif joy_y > 0.2:
                    l_b, r_b = self.current_power, self.current_power  # Backward

                if joy_x > 0.2:
                    r_b = 0  # Turn Right
                elif joy_x < -0.2:
                    l_b = 0  # Turn Left

                # Note: If the motor is physically wired backwards,
                # you can flip the sign here: f"{-l_b:.2f},{r_b:.2f}"
                packet = f"{l_b:.2f},{r_b:.2f}".encode('utf-8')
                try:
                    sock.sendto(packet, (PI_IPS["Team B"], UDP_PORT))
                except:
                    pass

            time.sleep(0.02)

    def initialize_weights(self):
        if not os.path.exists(self.games_dir): os.makedirs(self.games_dir)
        all_games = [f[:-3] for f in os.listdir(self.games_dir) if f.endswith(".py") and f != "__init__.py"]
        for game in all_games:
            if game not in self.game_weights: self.game_weights[game] = 10

    def pick_next_game(self):
        if getattr(self, 'game_deck', None) is None or len(self.game_deck) == 0:
            self.game_deck = [
                f[:-3] for f in os.listdir(self.games_dir)
                if f.endswith(".py") and f != "__init__.py"
            ]
            random.shuffle(self.game_deck)
        return self.game_deck.pop() if self.game_deck else None

    def handle_winner(self, winner):
        self.clear_frame()

        if "Tie" in winner:
            msg = "Tie"
            color = "yellow"
        else:
            if "Player 1" in winner or "Blue" in winner or "Team A" in winner:
                winner_team = "Team A"
                msg = "Blue Wins"
                color = "#0074D9"
            else:
                winner_team = "Team B"
                msg = "Pink Wins"
                color = "#F012BE"

            self.total_wins[winner_team] += 1

            # Ramp up power globally on win, maxing out at 1.0 (100%)
            if self.current_power < 1.0:
                self.current_power = round(self.current_power + 0.1, 2)

            self.update_score_display()
            self.send_win_network_signal(winner_team)

        tk.Label(
            self.game_frame,
            text=msg,
            font=("Impact", 60),
            fg=color,
            bg="black"
        ).pack(expand=True)

        self.root.after(2000, self.launch_game)

    def send_win_network_signal(self, winner):
        if winner in PI_IPS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(b"WIN", (PI_IPS[winner], UDP_PORT))
            except Exception as e:
                print(f"WIN SIGNAL ERROR: {e}")

    def update_score_display(self):
        self.score_label.config(text=f"BLUE: {self.total_wins['Team A']}  |  PINK: {self.total_wins['Team B']}")

    def clear_frame(self):
        for widget in self.game_frame.winfo_children(): widget.destroy()

    def show_calibration(self):
        self.clear_frame()
        self.ready_state = {"Team A": False, "Team B": False}
        tk.Label(self.game_frame, text="CAR HARDWARE LINK", font=("Courier", 32, "bold"), fg="white", bg="black").pack(
            pady=40)

        self.status_a = tk.Label(self.game_frame, text="BLUE CAR (Joy 0): PRESS A", font=("Arial", 22), fg="#0074D9",
                                 bg="black")
        self.status_a.pack(pady=20)
        self.status_b = tk.Label(self.game_frame, text="PINK CAR (Joy 1): PRESS A", font=("Arial", 22), fg="#F012BE",
                                 bg="black")
        self.status_b.pack(pady=20)
        self.check_calibration_input()

    def check_calibration_input(self):
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == 0:
                if event.joy == 0:
                    self.ready_state["Team A"] = True
                    self.status_a.config(text="BLUE LINKED", fg="cyan")
                if event.joy == 1:
                    self.ready_state["Team B"] = True
                    self.status_b.config(text="PINK LINKED", fg="magenta")

        if self.ready_state["Team A"] and self.ready_state["Team B"]:
            self.root.after(1000, lambda: self.start_one_time_countdown(3))
        else:
            self.root.after(20, self.check_calibration_input)

    def start_one_time_countdown(self, count):
        self.clear_frame()
        if count > 0:
            tk.Label(self.game_frame, text=str(count), font=("Impact", 150), fg="white", bg="black").pack(expand=True)
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


if __name__ == "__main__":
    root = tk.Tk()
    app = GameHandler(root)
    root.mainloop()