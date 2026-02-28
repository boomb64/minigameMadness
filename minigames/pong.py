import tkinter as tk
import pygame

# Constants for Xbox Controller
AXIS_LEFT_STICK_Y = 1

def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # 2. Game Settings
    canvas_width = 600
    canvas_height = 400
    paddle_w = 10
    paddle_h = 60
    ball_size = 10
    paddle_speed = 7
    border_thickness = 2

    # Game State
    state = {
        "active": True,
        "ball_x": canvas_width // 2,
        "ball_y": canvas_height // 2,
        "ball_dx": 4,
        "ball_dy": 4,
        "paddle_a_y": canvas_height // 2 - paddle_h // 2,
        "paddle_b_y": canvas_height // 2 - paddle_h // 2
    }

    # 3. Setup GUI
    canvas = tk.Canvas(parent_frame, width=canvas_width, height=canvas_height, bg="black", highlightthickness=0)
    canvas.pack(expand=True)

    # DRAW THE BOUNDING BOX
    canvas.create_rectangle(
        0, 0, canvas_width, canvas_height,
        outline="white", width=border_thickness
    )

    # Draw initial objects
    ball_gfx = canvas.create_oval(0, 0, ball_size, ball_size, fill="white")
    paddle_a_gfx = canvas.create_rectangle(20, 0, 20 + paddle_w, paddle_h, fill="cyan")
    paddle_b_gfx = canvas.create_rectangle(canvas_width - 30, 0, canvas_width - 30 + paddle_w, paddle_h, fill="magenta")

    def update_game():
        if not state["active"]: return

        # A. Handle Inputs
        pygame.event.pump()
        if len(joysticks) > 0:
            val_a = joysticks[0].get_axis(AXIS_LEFT_STICK_Y)
            state["paddle_a_y"] += val_a * paddle_speed
        if len(joysticks) > 1:
            val_b = joysticks[1].get_axis(AXIS_LEFT_STICK_Y)
            state["paddle_b_y"] += val_b * paddle_speed

        # B. Constrain Paddles
        state["paddle_a_y"] = max(border_thickness, min(canvas_height - paddle_h - border_thickness, state["paddle_a_y"]))
        state["paddle_b_y"] = max(border_thickness, min(canvas_height - paddle_h - border_thickness, state["paddle_b_y"]))

        # C. Ball Physics
        state["ball_x"] += state["ball_dx"]
        state["ball_y"] += state["ball_dy"]

        # Wall Bounce
        if state["ball_y"] <= border_thickness or state["ball_y"] >= canvas_height - ball_size - border_thickness:
            state["ball_dy"] *= -1

        # D. Paddle Collision with 1.5x Speed Multiplier
        # Left Paddle (Team A)
        if state["ball_x"] <= 30 and state["paddle_a_y"] < state["ball_y"] + ball_size < state["paddle_a_y"] + paddle_h:
            state["ball_dx"] *= -1.1 # Reverse and accelerate
            state["ball_dy"] *= 1.1  # Accelerate vertical speed too
            state["ball_x"] = 31     # Prevent getting stuck in paddle

        # Right Paddle (Team B)
        if state["ball_x"] >= canvas_width - 40 and state["paddle_b_y"] < state["ball_y"] + ball_size < state["paddle_b_y"] + paddle_h:
            state["ball_dx"] *= -1.1 # Reverse and accelerate
            state["ball_dy"] *= 1.1  # Accelerate vertical speed too
            state["ball_x"] = canvas_width - 41

        # E. Scoring
        if state["ball_x"] < 0:
            end_game("Team B")
            return
        elif state["ball_x"] > canvas_width:
            end_game("Team A")
            return

        # F. Update Graphics
        canvas.coords(ball_gfx, state["ball_x"], state["ball_y"], state["ball_x"] + ball_size, state["ball_y"] + ball_size)
        canvas.coords(paddle_a_gfx, 20, state["paddle_a_y"], 20 + paddle_w, state["paddle_a_y"] + paddle_h)
        canvas.coords(paddle_b_gfx, canvas_width - 30, state["paddle_b_y"], canvas_width - 30 + paddle_w, state["paddle_b_y"] + paddle_h)

        parent_frame.after(16, update_game)

    def end_game(winner):
        state["active"] = False
        canvas.destroy()
        on_game_over(winner)

    update_game()