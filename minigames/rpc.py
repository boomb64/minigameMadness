import tkinter as tk
import pygame

# Mapping for Xbox Controllers (Standard)
BUTTON_A = 0  # Green (Rock)
BUTTON_B = 1  # Red (Paper)
BUTTON_X = 2  # Blue (Scissors)


def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # 2. Setup GUI
    label = tk.Label(parent_frame, text="PICK YOUR MOVE IN SECRET!", font=("Arial", 24), fg="white", bg="black")
    label.pack(pady=20)

    instruction_label = tk.Label(parent_frame, text="A: Rock | B: Paper | X: Scissors", font=("Arial", 14), bg="black",
                                 fg="gray")
    instruction_label.pack()

    status_label = tk.Label(parent_frame, text="Waiting for players...", font=("Arial", 18), bg="black", fg="yellow")
    status_label.pack(pady=20)

    state = {
        "p1_choice": None,
        "p2_choice": None,
        "active": True,
        "countdown": 3,
        "moves": {0: "ROCK", 1: "PAPER", 2: "SCISSORS"}
    }

    def determine_winner():
        p1 = state["p1_choice"]
        p2 = state["p2_choice"]

        if p1 == p2:
            return "Draw!"

        # Win conditions for P1
        if (p1 == 0 and p2 == 2) or (p1 == 1 and p2 == 0) or (p1 == 2 and p2 == 1):
            return "Team A Wins!"
        else:
            return "Team B Wins!"

    def run_countdown():
        if state["countdown"] > 0:
            status_label.config(text=str(state["countdown"]), font=("Arial", 48), fg="red")
            state["countdown"] -= 1
            parent_frame.after(600, run_countdown)
        else:
            winner_text = determine_winner()
            final_display = f"A: {state['moves'][state['p1_choice']]} vs B: {state['moves'][state['p2_choice']]}\n\n{winner_text}"
            end_game(final_display)

    def check_inputs():
        if not state["active"]: return

        pygame.event.pump()

        # Check Player 1 (Team A)
        if state["p1_choice"] is None and len(joysticks) > 0:
            for btn in [BUTTON_A, BUTTON_B, BUTTON_X]:
                if joysticks[0].get_button(btn):
                    state["p1_choice"] = btn

        # Check Player 2 (Team B)
        if state["p2_choice"] is None and len(joysticks) > 1:
            for btn in [BUTTON_A, BUTTON_B, BUTTON_X]:
                if joysticks[1].get_button(btn):
                    state["p2_choice"] = btn

        # Update Status
        ready_text = ""
        if state["p1_choice"] is not None: ready_text += "P1 READY "
        if state["p2_choice"] is not None: ready_text += "| P2 READY"

        if ready_text:
            status_label.config(text=ready_text)

        # If both chose, start countdown
        if state["p1_choice"] is not None and state["p2_choice"] is not None:
            state["active"] = False
            run_countdown()
        else:
            parent_frame.after(16, check_inputs)

    def end_game(winner_msg):
        # Pause briefly so players can see the result before the frame clears
        parent_frame.after(2000, lambda: cleanup(winner_msg))

    def cleanup(winner_msg):
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner_msg)

    # Start the input polling loop
    check_inputs()