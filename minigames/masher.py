import tkinter as tk
import pygame

# Mapping for Xbox Controllers
BUTTON_A = 0


def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # 2. Game Logic Settings
    WIN_MARGIN = 7
    state = {
        "balance": 0,
        "active": True,
        "prev_a": False,  # Tracks previous button state for Team A
        "prev_b": False  # Tracks previous button state for Team B
    }

    # 3. Setup GUI
    label = tk.Label(parent_frame, text="MASH 'A' TO OVERPOWER!", font=("Arial", 24, "bold"), fg="white", bg="black")
    label.pack(pady=20)

    # The Visual Bar
    canvas_w = 500
    canvas_h = 50
    canvas = tk.Canvas(parent_frame, width=canvas_w, height=canvas_h, bg="#333", highlightthickness=2,
                       highlightbackground="white")
    canvas.pack(pady=40)

    # The two halves of the bar
    bar_a = canvas.create_rectangle(0, 0, canvas_w // 2, canvas_h, fill="magenta", outline="")
    bar_b = canvas.create_rectangle(canvas_w // 2, 0, canvas_w, canvas_h, fill="cyan", outline="")

    # Center Marker
    canvas.create_line(canvas_w // 2, 0, canvas_w // 2, canvas_h, fill="white", width=3)

    def update_bar():
        # Map the balance (-7 to 7) to the canvas width
        split_pct = (state["balance"] + WIN_MARGIN) / (WIN_MARGIN * 2)
        split_x = split_pct * canvas_w

        canvas.coords(bar_a, 0, 0, split_x, canvas_h)
        canvas.coords(bar_b, split_x, 0, canvas_w, canvas_h)

    def update_game():
        if not state["active"]: return

        # A. Handle Inputs (Direct Polling like Pong)
        pygame.event.pump()

        # Handle Team A (Joy 0)
        if len(joysticks) > 0:
            current_a = joysticks[0].get_button(BUTTON_A)
            # Only trigger on the "press down" action (current is True, previous was False)
            if current_a and not state["prev_a"]:
                state["balance"] -= 1
            state["prev_a"] = current_a

        # Handle Team B (Joy 1)
        if len(joysticks) > 1:
            current_b = joysticks[1].get_button(BUTTON_A)
            if current_b and not state["prev_b"]:
                state["balance"] += 1
            state["prev_b"] = current_b

        # B. Update UI
        update_bar()

        # C. Check for Win
        if state["balance"] <= -WIN_MARGIN:
            end_game("Team A")
        elif state["balance"] >= WIN_MARGIN:
            end_game("Team B")
        else:
            parent_frame.after(16, update_game)  # ~60 FPS

    def end_game(winner):
        state["active"] = False
        canvas.destroy()
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    # Initial call
    update_game()