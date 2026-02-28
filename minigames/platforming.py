import tkinter as tk
import pygame
import random
import math
import time

# Xbox Mapping
STICK_X = 0
BUTTON_A = 0


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks: joy.init()

    # Constants
    CANVAS_W, CANVAS_H = 800, 600
    GRAVITY = 0.8
    JUMP_STRENGTH = -15
    MOVE_SPEED = 7
    PLAYER_SIZE = 28
    LAYER_SPACING = 120
    TOTAL_LAYERS = 12
    GAME_TIMEOUT = 10

    # --- PROCEDURAL MAP ---
    platforms = []
    moving_platforms = []
    platforms.append({"x": 0, "y": 550, "w": 800, "h": 50})  # Start Floor

    for i in range(1, TOTAL_LAYERS + 1):
        y_pos = 550 - (i * LAYER_SPACING)
        width = random.randint(180, 350)
        x_pos = random.randint(50, 750 - width)

        if random.random() < 0.25 and i > 2:
            moving_platforms.append({
                "x_start": x_pos, "y": y_pos, "w": 160, "h": 20,
                "range": random.randint(100, 200),
                "speed": random.uniform(0.02, 0.04),
                "offset": random.uniform(0, 6), "curr_x": x_pos
            })
        else:
            platforms.append({"x": x_pos, "y": y_pos, "w": width, "h": 20})

    goal_y = 550 - ((TOTAL_LAYERS + 1) * LAYER_SPACING)
    platforms.append({"x": 0, "y": goal_y, "w": 800, "h": 80, "is_goal": True})

    state = {
        "active": True, "camera_y": 0, "frame_count": 0, "start_time": time.time(),
        "Team A": {"x": 200, "y": 500, "vx": 0, "vy": 0, "color": "blue", "on_ground": False, "prev_a": False},
        "Team B": {"x": 600, "y": 500, "vx": 0, "vy": 0, "color": "pink", "on_ground": False, "prev_a": False}
    }

    canvas = tk.Canvas(parent_frame, width=CANVAS_W, height=CANVAS_H, bg="#050510", highlightthickness=0)
    canvas.pack(expand=True)

    def resolve_collision(p, all_plats):
        p["on_ground"] = False
        for (x, y, w, h) in all_plats:
            if p["x"] + PLAYER_SIZE > x and p["x"] < x + w:
                # 1. LANDING (Top)
                if p["vy"] >= 0:
                    if (p["y"] + PLAYER_SIZE - p["vy"]) <= y + 12 and (p["y"] + PLAYER_SIZE) >= y:
                        p["y"] = y - PLAYER_SIZE
                        p["vy"] = 0
                        p["on_ground"] = True
                        return
                # 2. BONKING (Bottom)
                elif p["vy"] < 0:
                    if (p["y"] - p["vy"]) >= (y + h - 12) and p["y"] <= (y + h):
                        p["y"] = y + h
                        p["vy"] = 0
                        return

    def update():
        if not state["active"]: return
        state["frame_count"] += 1
        pygame.event.pump()

        elapsed = time.time() - state["start_time"]
        time_left = max(0, GAME_TIMEOUT - elapsed)

        if time_left <= 0:
            winner = "Team A" if state["Team A"]["y"] < state["Team B"]["y"] else "Team B"
            end_game(winner if state["Team A"]["y"] != state["Team B"]["y"] else "Tie")
            return

        for m in moving_platforms:
            m["curr_x"] = m["x_start"] + math.sin(state["frame_count"] * m["speed"] + m["offset"]) * m["range"]

        all_plats = [(p["x"], p["y"], p["w"], p["h"]) for p in platforms]
        all_plats += [(m["curr_x"], m["y"], m["w"], m["h"]) for m in moving_platforms]

        # Leader Tracking
        leader_y = min(state["Team A"]["y"], state["Team B"]["y"])

        for i, team in enumerate(["Team A", "Team B"]):
            p = state[team]
            joy = joysticks[i] if i < len(joysticks) else None
            if joy:
                axis = joy.get_axis(STICK_X)
                p["vx"] = axis * MOVE_SPEED if abs(axis) > 0.1 else 0
                btn_a = joy.get_button(BUTTON_A)
                if btn_a and not p["prev_a"] and p["on_ground"]:
                    p["vy"] = JUMP_STRENGTH
                p["prev_a"] = btn_a

            p["vy"] += GRAVITY
            p["x"] = max(0, min(CANVAS_W - PLAYER_SIZE, p["x"] + p["vx"]))
            p["y"] += p["vy"]
            resolve_collision(p, all_plats)

            if p["y"] <= goal_y + 40:
                end_game(team)
                return

        # Camera Physics
        target_cam = -(leader_y - 350)
        state["camera_y"] += (target_cam - state["camera_y"]) * 0.1
        cy = state["camera_y"]

        # Elimination Check
        for team in ["Team A", "Team B"]:
            p = state[team]
            if p["y"] + cy > CANVAS_H:
                end_game("Team B" if team == "Team A" else "Team A")
                return

        # --- RENDERING ---
        canvas.delete("all")

        # 1. World Layer (Platforms & Players) - Drawn First
        for p in platforms:
            color = "gold" if "is_goal" in p else "#333b4d"
            canvas.create_rectangle(p["x"], p["y"] + cy, p["x"] + p["w"], p["y"] + p["h"] + cy, fill=color,
                                    outline="white")

        for m in moving_platforms:
            canvas.create_rectangle(m["curr_x"], m["y"] + cy, m["curr_x"] + m["w"], m["y"] + m["h"] + cy,
                                    fill="#445566", outline="cyan", width=2)

        for team in ["Team A", "Team B"]:
            p = state[team]
            canvas.create_rectangle(p["x"], p["y"] + cy, p["x"] + PLAYER_SIZE, p["y"] + PLAYER_SIZE + cy,
                                    fill=p["color"], outline="white", width=2)

        # 2. HUD Layer (Timer) - Drawn Last to stay on Top
        canvas.create_rectangle(0, 0, 800, 60, fill="black", outline="white", width=2)
        timer_color = "red" if time_left < 3 else "white"
        canvas.create_text(400, 30, text=f"TIME: {time_left:.1f}s", fill=timer_color, font=("Courier", 22, "bold"))

        parent_frame.after(16, update)

    def end_game(winner):
        state["active"] = False
        canvas.destroy()
        on_game_over(winner)

    update()