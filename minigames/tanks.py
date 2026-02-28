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

    # 1. Setup Deformable Terrain (List of Y-values for every X pixel)
    terrain = [GROUND_Y] * WIDTH

    state = {
        "active": True,
        "tanks": [
            {"x": 100, "angle": -45, "color": P1_COLOR, "prev_a": False},
            {"x": 700, "angle": -135, "color": P2_COLOR, "prev_a": False}
        ],
        "bullets": [],  # List of {x, y, vx, vy, owner}
        "explosions": []  # List of {x, y, r, life}
    }

    def fire_bullet(idx):
        t = state["tanks"][idx]
        # Calculate start pos based on angle
        rad = math.radians(t["angle"])
        # High speed for "fairly quick" flight
        speed = 12
        state["bullets"].append({
            "x": t["x"],
            "y": terrain[int(t["x"])] - 15,
            "vx": math.cos(rad) * speed,
            "vy": math.sin(rad) * speed,
            "owner": idx
        })

    def create_explosion(x, y):
        radius = 35
        state["explosions"].append({"x": x, "y": y, "r": radius, "life": 10})

        # Deform Terrain: Lower the ground within the radius
        for tx in range(max(0, int(x - radius)), min(WIDTH, int(x + radius))):
            dist = abs(tx - x)
            # Circular carve depth
            depth = math.sqrt(max(0, radius ** 2 - dist ** 2))
            if y + depth > terrain[tx]:
                terrain[tx] = max(terrain[tx], y + depth)

    def update_physics():
        if not state["active"]: return

        # Update Bullets
        for b in state["bullets"][:]:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            b["vy"] += GRAVITY

            # 1. Check Bullet vs Bullet (Midair)
            for other in state["bullets"]:
                if b != other:
                    if math.hypot(b["x"] - other["x"], b["y"] - other["y"]) < 10:
                        create_explosion(b["x"], b["y"])
                        if b in state["bullets"]: state["bullets"].remove(b)
                        if other in state["bullets"]: state["bullets"].remove(other)
                        break

            # 2. Check Bullet vs Terrain
            if 0 <= int(b["x"]) < WIDTH:
                if b["y"] >= terrain[int(b["x"])]:
                    create_explosion(b["x"], b["y"])
                    if b in state["bullets"]: state["bullets"].remove(b)
                    continue

            # 3. Check Bullet vs Tanks (Direct Hit)
            for i, tank in enumerate(state["tanks"]):
                if math.hypot(b["x"] - tank["x"], b["y"] - terrain[int(tank["x"])]) < 20:
                    end_game(f"Player {2 if i == 0 else 1} Wins!")
                    return

            # Out of bounds
            if b["y"] > HEIGHT or b["x"] < 0 or b["x"] > WIDTH:
                if b in state["bullets"]: state["bullets"].remove(b)

        # Check Explosion Radius vs Tanks
        for exp in state["explosions"]:
            for i, tank in enumerate(state["tanks"]):
                if math.hypot(exp["x"] - tank["x"], exp["y"] - terrain[int(tank["x"])]) < exp["r"]:
                    end_game(f"Player {2 if i == 0 else 1} Wins!")
                    return
            exp["life"] -= 1
            if exp["life"] <= 0: state["explosions"].remove(exp)

    def draw():
        canvas.delete("all")

        # Draw Terrain
        points = [0, HEIGHT]
        for x in range(WIDTH):
            points.extend([x, terrain[x]])
        points.extend([WIDTH, HEIGHT])
        canvas.create_polygon(points, fill="#654321", outline="#3d2b1f")

        # Draw Tanks
        for t in state["tanks"]:
            tx = int(t["x"])
            ty = terrain[tx]
            # Body
            canvas.create_rectangle(tx - 15, ty - 10, tx + 15, ty, fill=t["color"])
            # Barrel
            rad = math.radians(t["angle"])
            bx, by = tx + math.cos(rad) * 20, (ty - 5) + math.sin(rad) * 20
            canvas.create_line(tx, ty - 5, bx, by, fill="black", width=4)

        # Draw Bullets
        for b in state["bullets"]:
            canvas.create_oval(b["x"] - 3, b["y"] - 3, b["x"] + 3, b["y"] + 3, fill="black")

        # Draw Explosions
        for e in state["explosions"]:
            canvas.create_oval(e["x"] - e["r"], e["y"] - e["r"], e["x"] + e["r"], e["y"] + e["r"], fill="orange",
                               outline="red")

    def game_loop():
        if not state["active"]: return
        pygame.event.pump()

        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]
            # Tank Movement (Left/Right)
            move = joy.get_axis(AXIS_LX)
            if abs(move) > 0.1:
                state["tanks"][i]["x"] = max(20, min(WIDTH - 20, state["tanks"][i]["x"] + move * 4))

            # Aiming (Up/Down)
            aim = joy.get_axis(AXIS_LY)
            if abs(aim) > 0.1:
                state["tanks"][i]["angle"] += aim * 3

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