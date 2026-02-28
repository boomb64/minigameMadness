import tkinter as tk
import pygame
import random
import math

# Mapping for Xbox Controllers
BUTTON_A = 0
AXIS_LX = 0


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # Constants
    WIDTH, HEIGHT = 800, 700
    GRAVITY = 0.35
    BOUNCE = 0.55
    PEG_RADIUS = 4
    TOKEN_RADIUS = 10
    P1_COLOR, P2_COLOR = "#0074D9", "#F012BE"

    # SLOT CONFIG: [multiplier, bg_color, text_color, width_weight]
    # The center 100x is now "shrunk" with a weight of 0.6 instead of 1.0
    SLOT_CONFIG = [
        (1, "#FF0000", "white", 1.0), (10, "#FF8C00", "black", 1.0), (30, "#FFFF00", "black", 1.0),
        (50, "#00FF00", "black", 1.0), (70, "#B10DC9", "white", 1.0),
        (100, "#FFFFFF", "black", 0.6),  # SHRUNK CENTER
        (70, "#B10DC9", "white", 1.0), (50, "#00FF00", "black", 1.0), (30, "#FFFF00", "black", 1.0),
        (10, "#FF8C00", "black", 1.0), (1, "#FF0000", "white", 1.0)
    ]

    total_weight = sum(s[3] for s in SLOT_CONFIG)
    pixel_per_weight = WIDTH / total_weight

    canvas = tk.Canvas(parent_frame, width=WIDTH, height=HEIGHT, bg="#050505", highlightthickness=0)
    canvas.pack()

    # Peg Grid
    pegs = []
    rows, cols = 12, 16
    for r in range(rows):
        for c in range(cols):
            offset = (WIDTH / cols) / 2 if r % 2 == 0 else 0
            px = (c * (WIDTH / cols)) + offset
            py = 150 + (r * 40)
            if 20 < px < WIDTH - 20:
                pegs.append({"x": px, "y": py})

    state = {
        "active": True,
        "timer": 5.0,
        "p_tokens_left": [3, 3],
        "p_scores": [0, 0],
        "p_x": [200, 600],
        "falling_tokens": [],
        "prev_a": [False, False],
        "game_ending": False
    }

    def update_physics():
        if not state["active"]: return

        if state["timer"] > 0:
            state["timer"] -= 0.016
        else:
            state["timer"] = 0
            state["p_tokens_left"] = [0, 0]

        for t in state["falling_tokens"][:]:
            t["vy"] += GRAVITY
            t["x"] += t["vx"]
            t["y"] += t["vy"]

            if t["x"] < TOKEN_RADIUS or t["x"] > WIDTH - TOKEN_RADIUS:
                t["vx"] *= -BOUNCE
                t["x"] = max(TOKEN_RADIUS, min(WIDTH - TOKEN_RADIUS, t["x"]))

            for p in pegs:
                dx, dy = t["x"] - p["x"], t["y"] - p["y"]
                dist = math.hypot(dx, dy)
                if dist < (TOKEN_RADIUS + PEG_RADIUS):
                    angle = math.atan2(dy, dx)
                    t["x"] = p["x"] + (TOKEN_RADIUS + PEG_RADIUS) * math.cos(angle)
                    t["y"] = p["y"] + (TOKEN_RADIUS + PEG_RADIUS) * math.sin(angle)
                    speed = math.hypot(t["vx"], t["vy"]) * BOUNCE
                    t["vx"] = math.cos(angle) * speed + random.uniform(-0.6, 0.6)
                    t["vy"] = math.sin(angle) * speed

            if t["y"] > HEIGHT - 70:
                # Calculate bucket based on weighted widths
                current_x = 0
                bucket_idx = 0
                for i, s in enumerate(SLOT_CONFIG):
                    w = s[3] * pixel_per_weight
                    if current_x <= t["x"] <= current_x + w:
                        bucket_idx = i
                        break
                    current_x += w

                state["p_scores"][t["owner"]] += SLOT_CONFIG[bucket_idx][0]
                state["falling_tokens"].remove(t)

        if state["timer"] <= 0 and len(state["falling_tokens"]) == 0:
            determine_winner()

    def determine_winner():
        if state["game_ending"]: return
        state["game_ending"] = True
        s1, s2 = state["p_scores"]
        winner = "Blue Wins!" if s1 > s2 else "Pink Wins!" if s2 > s1 else "It's a Tie!"
        state["active"] = False
        on_game_over(winner)

    def draw():
        canvas.delete("all")

        # Weighted Color Slots
        current_x = 0
        for i, (mult, bg_color, text_color, weight) in enumerate(SLOT_CONFIG):
            w = weight * pixel_per_weight
            canvas.create_rectangle(current_x, HEIGHT - 70, current_x + w, HEIGHT, fill=bg_color, outline="black")
            canvas.create_text(current_x + w / 2, HEIGHT - 35, text=f"{mult}X", fill=text_color,
                               font=("Impact", 16 if weight < 1 else 18, "bold"))
            current_x += w

        # Pegs
        for p in pegs:
            canvas.create_oval(p["x"] - PEG_RADIUS, p["y"] - PEG_RADIUS, p["x"] + PEG_RADIUS, p["y"] + PEG_RADIUS,
                               fill="white")

        # Shrunk Timer (Reduced from 45 to 28 font)
        t_color = "white" if state["timer"] > 1.5 else "#FF4136"
        canvas.create_text(WIDTH / 2, 35, text=f"{state['timer']:.1f}", fill=t_color, font=("Impact", 28))

        # Players
        for i in range(2):
            color = P1_COLOR if i == 0 else P2_COLOR
            if state["p_tokens_left"][i] > 0 and state["timer"] > 0:
                canvas.create_oval(state["p_x"][i] - TOKEN_RADIUS, 80, state["p_x"][i] + TOKEN_RADIUS, 100, fill=color,
                                   outline="white")
                canvas.create_text(state["p_x"][i], 70, text=f"{state['p_tokens_left'][i]} LEFT", fill="white",
                                   font=("Arial", 9, "bold"))

        # Falling Tokens
        for t in state["falling_tokens"]:
            color = P1_COLOR if t["owner"] == 0 else P2_COLOR
            canvas.create_oval(t["x"] - TOKEN_RADIUS, t["y"] - TOKEN_RADIUS, t["x"] + TOKEN_RADIUS,
                               t["y"] + TOKEN_RADIUS, fill=color, outline="white", width=2)

        # Scoreboard
        canvas.create_text(100, 25, text=f"BLUE: {state['p_scores'][0]}", fill=P1_COLOR, font=("Impact", 20))
        canvas.create_text(WIDTH - 100, 25, text=f"PINK: {state['p_scores'][1]}", fill=P2_COLOR, font=("Impact", 20))

    def game_loop():
        if not state["active"]: return
        pygame.event.pump()
        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]
            move = joy.get_axis(AXIS_LX)
            if abs(move) > 0.1:
                state["p_x"][i] = max(TOKEN_RADIUS, min(WIDTH - TOKEN_RADIUS, state["p_x"][i] + move * 9))

            btn = joy.get_button(BUTTON_A)
            if btn and not state["prev_a"][i] and state["timer"] > 0 and state["p_tokens_left"][i] > 0:
                state["falling_tokens"].append({"x": state["p_x"][i], "y": 90, "vx": 0, "vy": 0, "owner": i})
                state["p_tokens_left"][i] -= 1
            state["prev_a"][i] = btn

        update_physics()
        draw()
        parent_frame.after(16, game_loop)

    game_loop()