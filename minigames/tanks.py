import tkinter as tk
import pygame
import math
import random

# Mapping for Xbox Controllers
BUTTON_A = 0
AXIS_LX = 0
AXIS_LY = 1


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # Constants
    WIDTH, HEIGHT = 800, 500
    GROUND_Y = 400
    GRAVITY = 0.25
    P1_COLOR, P2_COLOR = "#0074D9", "#F012BE"

    canvas = tk.Canvas(parent_frame, width=WIDTH, height=HEIGHT, bg="#87CEEB", highlightthickness=0)
    canvas.pack()

    # Setup Deformable Terrain
    terrain = [GROUND_Y] * WIDTH

    state = {
        "active": True,
        "tanks": [
            {"x": 100, "angle": -45, "color": P1_COLOR, "prev_a": False},
            {"x": 700, "angle": -135, "color": P2_COLOR, "prev_a": False}
        ],
        "bullets": [],
        "explosions": []
    }

    def fire_bullet(idx):
        t = state["tanks"][idx]
        rad = math.radians(t["angle"])
        speed = 13  # Slightly faster for better feel

        # Start at the end of the barrel
        barrel_len = 25
        start_x = t["x"] + math.cos(rad) * barrel_len
        start_y = (terrain[int(t["x"])] - 20) + math.sin(rad) * barrel_len

        state["bullets"].append({
            "x": start_x,
            "y": start_y,
            "vx": math.cos(rad) * speed,
            "vy": math.sin(rad) * speed,
            "owner": idx
        })

    def create_explosion(x, y):
        radius = 40
        state["explosions"].append({"x": x, "y": y, "r": radius, "life": 12})
        for tx in range(max(0, int(x - radius)), min(WIDTH, int(x + radius))):
            dist = abs(tx - x)
            depth = math.sqrt(max(0, radius ** 2 - dist ** 2))
            if y + depth > terrain[tx]:
                terrain[tx] = max(terrain[tx], y + depth)

    def update_physics():
        if not state["active"]: return

        for b in state["bullets"][:]:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            b["vy"] += GRAVITY

            # Bullet vs Bullet
            for other in state["bullets"]:
                if b != other and math.hypot(b["x"] - other["x"], b["y"] - other["y"]) < 12:
                    create_explosion(b["x"], b["y"])
                    if b in state["bullets"]: state["bullets"].remove(b)
                    if other in state["bullets"]: state["bullets"].remove(other)
                    break

            # Bullet vs Terrain
            if 0 <= int(b["x"]) < WIDTH:
                if b["y"] >= terrain[int(b["x"])]:
                    create_explosion(b["x"], b["y"])
                    if b in state["bullets"]: state["bullets"].remove(b)
                    continue

            # Bullet vs Tanks
            for i, tank in enumerate(state["tanks"]):
                if math.hypot(b["x"] - tank["x"], b["y"] - (terrain[int(tank["x"])] - 15)) < 25:
                    end_game(f"Player {2 if i == 0 else 1} Wins!")
                    return

            if b["y"] > HEIGHT or b["x"] < 0 or b["x"] > WIDTH:
                if b in state["bullets"]: state["bullets"].remove(b)

        # Explosion Radius vs Tanks
        for exp in state["explosions"]:
            for i, tank in enumerate(state["tanks"]):
                if math.hypot(exp["x"] - tank["x"], exp["y"] - terrain[int(tank["x"])]) < exp["r"]:
                    end_game(f"Player {2 if i == 0 else 1} Wins!")
                    return
            exp["life"] -= 1
            if exp["life"] <= 0: state["explosions"].remove(exp)

    def draw():
        canvas.delete("all")

        # Terrain
        points = [0, HEIGHT]
        for x in range(WIDTH): points.extend([x, terrain[x]])
        points.extend([WIDTH, HEIGHT])
        canvas.create_polygon(points, fill="#5d4037", outline="#3e2723")

        # Tanks
        for t in state["tanks"]:
            tx = int(t["x"])
            ty = terrain[tx]

            # 1. Treads (Darker version of player color)
            canvas.create_oval(tx - 22, ty - 8, tx + 22, ty + 2, fill="#333333")

            # 2. Main Hull
            canvas.create_rectangle(tx - 20, ty - 18, tx + 20, ty - 5, fill=t["color"], outline="black")

            # 3. Turret (Top part)
            canvas.create_oval(tx - 12, ty - 25, tx + 12, ty - 12, fill=t["color"], outline="black")

            # 4. Rotating Barrel
            rad = math.radians(t["angle"])
            bx, by = tx + math.cos(rad) * 28, (ty - 20) + math.sin(rad) * 28
            canvas.create_line(tx, ty - 20, bx, by, fill="black", width=6)

        # Bullets
        for b in state["bullets"]:
            canvas.create_oval(b["x"] - 4, b["y"] - 4, b["x"] + 4, b["y"] + 4, fill="black")

        # Explosions
        for e in state["explosions"]:
            canvas.create_oval(e["x"] - e["r"], e["y"] - e["r"], e["x"] + e["r"], e["y"] + e["r"],
                               fill="orange", outline="yellow", width=2)

    def game_loop():
        if not state["active"]: return
        pygame.event.pump()

        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]

            # Movement
            move = joy.get_axis(AXIS_LX)
            if abs(move) > 0.1:
                state["tanks"][i]["x"] = max(25, min(WIDTH - 25, state["tanks"][i]["x"] + move * 3.5))

            # Aiming (Clamped between -180 and 0)
            aim = joy.get_axis(AXIS_LY)
            if abs(aim) > 0.1:
                state["tanks"][i]["angle"] = max(-180, min(0, state["tanks"][i]["angle"] + aim * 2.5))

            # Firing
            btn = joy.get_button(BUTTON_A)
            if btn and not state["tanks"][i]["prev_a"]:
                fire_bullet(i)
            state["tanks"][i]["prev_a"] = btn

        update_physics()
        draw()
        parent_frame.after(16, game_loop)

    def end_game(winner):
        state["active"] = False
        on_game_over(winner)

    game_loop()