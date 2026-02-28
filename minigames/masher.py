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
    # Win if you have +7 more mashes than the opponent
    WIN_MARGIN = 7
    state = {"balance": 0, "active": True}  # 0 is center, +7 is Team B wins, -7 is Team A wins

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
    # Cyan (Team A) on left, Magenta (Team B) on right
    bar_a = canvas.create_rectangle(0, 0, canvas_w // 2, canvas_h, fill="cyan", outline="")
    bar_b = canvas.create_rectangle(canvas_w // 2, 0, canvas_w, canvas_h, fill="magenta", outline="")

    # Center Marker
    canvas.create_line(canvas_w // 2, 0, canvas_w // 2, canvas_h, fill="white", width=3)

    def update_bar():
        # Calculate the "Split Point"
        # We map -7 to 7 range to 0 to canvas_width
        # Formula: (balance + margin) / (total_range) * width
        split_pct = (state["balance"] + WIN_MARGIN) / (WIN_MARGIN * 2)
        split_x = split_pct * canvas_w

        # Update the rectangles
        canvas.coords(bar_a, 0, 0, split_x, canvas_h)
        canvas.coords(bar_b, split_x, 0, canvas_w, canvas_h)

    def check_inputs():
        if not state["active"]: return

        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN and event.button == BUTTON_A:
                if event.joy == 0:  # Team A
                    state["balance"] -= 1
                elif event.joy == 1:  # Team B
                    state["balance"] += 1

                update_bar()

        # Check for Win
        if state["balance"] <= -WIN_MARGIN:
            end_game("Team A")
        elif state["balance"] >= WIN_MARGIN:
            end_game("Team B")
        else:
            parent_frame.after(10, check_inputs)

    def end_game(winner):
        state["active"] = False
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    # Initial call
    check_inputs()