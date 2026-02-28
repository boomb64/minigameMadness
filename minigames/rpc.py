import tkinter as tk
import pygame

# Mapping for Xbox Controllers
BUTTON_A = 0  # Rock
BUTTON_B = 1  # Paper
BUTTON_X = 2  # Scissors


def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # 2. Setup GUI
    # Using a main container to easily clear the screen for the end sequence
    main_container = tk.Frame(parent_frame, bg="black")
    main_container.pack(expand=True, fill="both")

    label = tk.Label(main_container, text="PICK YOUR MOVE!", font=("Courier", 30, "bold"), fg="white", bg="black")
    label.pack(pady=60)

    status_label = tk.Label(main_container, text="Waiting for players...", font=("Courier", 20), bg="black",
                            fg="yellow")
    status_label.pack(pady=20)

    instruction_label = tk.Label(main_container, text="A: Rock | B: Paper | X: Scissors", font=("Courier", 14),
                                 bg="black", fg="gray")
    instruction_label.pack(side="bottom", pady=40)

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
            return "Tie"

        # Win conditions: Rock(0) beats Sci(2), Paper(1) beats Rock(0), Sci(2) beats Paper(1)
        if (p1 == 0 and p2 == 2) or (p1 == 1 and p2 == 0) or (p1 == 2 and p2 == 1):
            return "Team A"  # Player 1 (Blue)
        else:
            return "Team B"  # Player 2 (Pink)

    def run_countdown():
        if state["countdown"] > 0:
            status_label.config(text=str(state["countdown"]), font=("Courier", 80, "bold"), fg="cyan")
            state["countdown"] -= 1
            parent_frame.after(800, run_countdown)
        else:
            status_label.config(text="SHOOT!", fg="white")
            parent_frame.after(400, end_game)

    def check_inputs():
        if not state["active"]: return

        pygame.event.pump()

        # Check Player 1 (Blue)
        if state["p1_choice"] is None and len(joysticks) > 0:
            for btn in [BUTTON_A, BUTTON_B, BUTTON_X]:
                if joysticks[0].get_button(btn):
                    state["p1_choice"] = btn

        # Check Player 2 (Pink)
        if state["p2_choice"] is None and len(joysticks) > 1:
            for btn in [BUTTON_A, BUTTON_B, BUTTON_X]:
                if joysticks[1].get_button(btn):
                    state["p2_choice"] = btn

        # Visual feedback for choices
        if state["p1_choice"] is not None and state["p2_choice"] is None:
            status_label.config(text="P1 READY...", fg="blue")
        elif state["p2_choice"] is not None and state["p1_choice"] is None:
            status_label.config(text="P2 READY...", fg="pink")
        elif state["p1_choice"] is not None and state["p2_choice"] is not None:
            status_label.config(text="BOTH READY!", fg="green")
            state["active"] = False
            parent_frame.after(500, run_countdown)
            return

        parent_frame.after(16, check_inputs)

    def end_game():
        winner = determine_winner()

        # CLEAR SCREEN (Pac-Man Style)
        for widget in main_container.winfo_children():
            widget.destroy()

        # SETUP FINAL DISPLAY (Per instructions)
        final_msg = ""
        text_color = "yellow"

        if winner == "Team A":
            final_msg = "Blue Wins"
            text_color = "blue"
        elif winner == "Team B":
            final_msg = "Pink Wins"
            text_color = "pink"
        else:
            final_msg = "Tie"
            text_color = "yellow"

        # Show winner text in center of black screen
        tk.Label(main_container, text=final_msg, font=("Courier", 60, "bold"),
                 fg=text_color, bg="black").place(relx=0.5, rely=0.5, anchor="center")

        # Final cleanup and return after 3 seconds
        parent_frame.after(3000, lambda: cleanup_and_exit(winner))

    def cleanup_and_exit(winner_text):
        state["active"] = False
        # Destroy all remaining widgets in the parent frame
        for widget in parent_frame.winfo_children():
            widget.destroy()
        # Trigger the runner's game-over callback
        on_game_over(winner_text)

    # Start the input polling loop
    check_inputs()