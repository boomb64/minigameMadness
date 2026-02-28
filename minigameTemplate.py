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

    state = {"A": 0, "B": 0, "win_threshold": 20, "active": True}

    def update_scores():
        score_label.config(text=f"Team A: {state['A']} | Team B: {state['B']}")

    def check_inputs():
        if not state["active"]: return

        # Process Pygame Events
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                # Controller 0 = Team A, Controller 1 = Team B
                if event.joy == 0 and event.button == BUTTON_A:
                    state["A"] += 1
                elif event.joy == 1 and event.button == BUTTON_A:
                    state["B"] += 1

                update_scores()

        # Check for Winner
        if state["A"] >= state["win_threshold"]:
            end_game("Team A")
        elif state["B"] >= state["win_threshold"]:
            end_game("Team B")
        else:
            # Re-run this check every 10ms (approx 100fps polling)
            parent_frame.after(10, check_inputs)

    def end_game(winner):
        state["active"] = False
        # Clear frame and signal the handler
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    # Start the input polling loop
    check_inputs()