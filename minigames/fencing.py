import tkinter as tk
import pygame

# Mapping for Xbox Controllers (Standard)
BUTTON_X = 2  # Attack
BUTTON_B = 1  # Block
AXIS_X = 0  # Left Stick Horizontal


def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # 2. Setup GUI - Centering logic
    # We use a container frame to ensure the game sits in the middle of the screen
    main_container = tk.Frame(parent_frame, bg="black")
    main_container.pack(expand=True)

    canvas = tk.Canvas(main_container, width=800, height=450, bg="#1a1a1a", highlightthickness=0)
    canvas.pack(pady=20)

    # Arena Decoration
    canvas.create_rectangle(0, 350, 800, 450, fill="#2c3e50", outline="")
    for i in range(0, 800, 100):
        canvas.create_line(i, 350, i + 25, 350, fill="gray", width=2)

    # Stamina Bars
    s_bar_a = canvas.create_rectangle(50, 20, 300, 40, fill="#2ecc71")
    s_bar_b = canvas.create_rectangle(500, 20, 750, 40, fill="#2ecc71")

    state = {
        "p1_pos": 200, "p2_pos": 600,
        "p1_stam": 100.0, "p2_stam": 100.0,
        "p1_blocking": False, "p2_blocking": False,
        "p1_lunge_timer": 0, "p2_lunge_timer": 0,
        "active": True,
        "p1_angle": 0, "p2_angle": 0,  # For the falling animation
        "base_reach": 30, "lunge_reach": 95,
        "prev_x1": False, "prev_x2": False
    }

    # Fencer Graphics
    p1_gfx = canvas.create_rectangle(190, 250, 210, 350, fill="#3498db", outline="white")
    p2_gfx = canvas.create_rectangle(590, 250, 610, 350, fill="#e74c3c", outline="white")
    p1_sword = canvas.create_line(210, 290, 240, 290, fill="#f1c40f", width=4)
    p2_sword = canvas.create_line(590, 290, 560, 290, fill="#f1c40f", width=4)

    def check_inputs():
        if not state["active"]: return
        pygame.event.pump()

        # Passive Stamina Regen
        state["p1_stam"] = min(100.0, state["p1_stam"] + 0.5)
        state["p2_stam"] = min(100.0, state["p2_stam"] + 0.5)

        if state["p1_lunge_timer"] > 0: state["p1_lunge_timer"] -= 1
        if state["p2_lunge_timer"] > 0: state["p2_lunge_timer"] -= 1

        # Player 1 (Team A)
        if len(joysticks) > 0:
            move_x = joysticks[0].get_axis(AXIS_X)
            if abs(move_x) > 0.1:
                state["p1_pos"] = max(20, min(state["p2_pos"] - 30, state["p1_pos"] + move_x * 8))

            state["p1_blocking"] = joysticks[0].get_button(BUTTON_B) and state["p1_stam"] > 5
            if state["p1_blocking"]: state["p1_stam"] -= 1.3

            curr_x = joysticks[0].get_button(BUTTON_X)
            if curr_x and not state["prev_x1"] and not state["p1_blocking"] and state["p1_stam"] >= 25:
                state["p1_stam"] -= 25
                state["p1_lunge_timer"] = 10
            state["prev_x1"] = curr_x

        # Player 2 (Team B)
        if len(joysticks) > 1:
            move_x = joysticks[1].get_axis(AXIS_X)
            if abs(move_x) > 0.1:
                state["p2_pos"] = min(780, max(state["p1_pos"] + 30, state["p2_pos"] + move_x * 8))

            state["p2_blocking"] = joysticks[1].get_button(BUTTON_B) and state["p2_stam"] > 5
            if state["p2_blocking"]: state["p2_stam"] -= 1.3

            curr_x = joysticks[1].get_button(BUTTON_X)
            if curr_x and not state["prev_x2"] and not state["p2_blocking"] and state["p2_stam"] >= 25:
                state["p2_stam"] -= 25
                state["p2_lunge_timer"] = 10
            state["prev_x2"] = curr_x

        update_visuals_and_collisions()
        parent_frame.after(16, check_inputs)

    def update_visuals_and_collisions():
        if not state["active"]: return

        # Update Visuals
        p1_r = state["lunge_reach"] if state["p1_lunge_timer"] > 0 else state["base_reach"]
        s1_tip = state["p1_pos"] + 10 + p1_r
        canvas.coords(p1_gfx, state["p1_pos"] - 10, 250, state["p1_pos"] + 10, 350)
        canvas.coords(p1_sword, state["p1_pos"] + 10, 290, s1_tip, 290)
        canvas.itemconfig(p1_gfx, fill="#2980b9" if state["p1_blocking"] else "#3498db")

        p2_r = state["lunge_reach"] if state["p2_lunge_timer"] > 0 else state["base_reach"]
        s2_tip = state["p2_pos"] - 10 - p2_r
        canvas.coords(p2_gfx, state["p2_pos"] - 10, 250, state["p2_pos"] + 10, 350)
        canvas.coords(p2_sword, state["p2_pos"] - 10, 290, s2_tip, 290)
        canvas.itemconfig(p2_gfx, fill="#c0392b" if state["p2_blocking"] else "#e74c3c")

        # Collision Logic
        if state["p1_lunge_timer"] > 0 and s1_tip >= state["p2_pos"] - 10:
            if state["p2_blocking"]:
                state["p1_stam"] = max(0, state["p1_stam"] - 35)  # Parry penalty
                state["p1_lunge_timer"] = 0
            else:
                animate_death("P2", "TEAM A")

        if state["p2_lunge_timer"] > 0 and s2_tip <= state["p1_pos"] + 10:
            if state["p1_blocking"]:
                state["p2_stam"] = max(0, state["p2_stam"] - 35)
                state["p2_lunge_timer"] = 0
            else:
                animate_death("P1", "TEAM B")

        # Update Stamina Bars
        canvas.coords(s_bar_a, 50, 20, 50 + (state["p1_stam"] * 2.5), 40)
        canvas.coords(s_bar_b, 500, 20, 500 + (state["p2_stam"] * 2.5), 40)

    def animate_death(loser_id, winner_name):
        state["active"] = False
        if loser_id == "P1":
            canvas.itemconfig(p1_gfx, fill="gray")
            canvas.coords(p1_gfx, state["p1_pos"] - 50, 330, state["p1_pos"] + 50, 350)  # Fall over
        else:
            canvas.itemconfig(p2_gfx, fill="gray")
            canvas.coords(p2_gfx, state["p2_pos"] - 50, 330, state["p2_pos"] + 50, 350)

        parent_frame.after(1500, lambda: end_game(winner_name))

    def end_game(winner):
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    check_inputs()