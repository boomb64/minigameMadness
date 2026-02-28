import tkinter as tk
import pygame

# Mapping for Xbox Controllers (Standard)
BUTTON_A = 0

def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # 2. Setup GUI
    label = tk.Label(parent_frame, text="MASH 'A' TO WIN!", font=("Arial", 24), fg="white", bg="black")
    label.pack(pady=20)

    score_label = tk.Label(parent_frame, text="Team A: 0 | Team B: 0", font=("Arial", 18), bg="black", fg="yellow")
    score_label.pack()

    # Added prev_a and prev_b for edge detection
    state = {
        "A": 0,
        "B": 0,
        "win_threshold": 20,
        "active": True,
        "prev_a": False,
        "prev_b": False
    }

    def update_scores():
        score_label.config(text=f"Team A: {state['A']} | Team B: {state['B']}")

    def check_inputs():
        if not state["active"]: return

        # A. Refresh internal Pygame state
        pygame.event.pump()

        # B. Direct Polling for Team A (Joy 0)
        if len(joysticks) > 0:
            current_a = joysticks[0].get_button(BUTTON_A)
            # Edge detection: True NOW, False BEFORE
            if current_a and not state["prev_a"]:
                state["A"] += 1
            state["prev_a"] = current_a

        # C. Direct Polling for Team B (Joy 1)
        if len(joysticks) > 1:
            current_b = joysticks[1].get_button(BUTTON_A)
            if current_b and not state["prev_b"]:
                state["B"] += 1
            state["prev_b"] = current_b

        update_scores()

        # D. Check for Winner
        if state["A"] >= state["win_threshold"]:
            end_game("Team A")
        elif state["B"] >= state["win_threshold"]:
            end_game("Team B")
        else:
            # Re-run this check every 16ms (~60 FPS polling)
            parent_frame.after(16, check_inputs)

    def end_game(winner):
        state["active"] = False
        # Clear frame and signal the handler
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    # Start the input polling loop
    check_inputs()