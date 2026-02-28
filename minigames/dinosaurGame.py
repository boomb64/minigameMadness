import tkinter as tk
import pygame
import random
import os
import time
from PIL import Image, ImageTk

# --- CONFIGURATION ---
SCALE = 2.0
CANVAS_W, CANVAS_H = int(1000 * (SCALE / 2)), int(300 * (SCALE / 2))
DINO_W, DINO_H = int(44 * SCALE), int(47 * SCALE)
CROUCH_H = int(26 * SCALE)
GROUND_Y = CANVAS_H - int(80 * (SCALE / 2))

# Colors
SKY_COLOR = "#D1F2EB"  # Light Teal Sky
SAND_COLOR = "#EDC9AF"  # Desert Sand
SAND_LINE = "#C4A484"  # Darker Sand for the edge

DINO_ASSETS = {}
TEAM_COLORS = {"A": "blue", "B": "pink"}


def load_all_assets():
    """Loads and scales all PNG images including the dead skins."""
    assets = [
        "blue_run_1", "blue_run_2", "blue_crouch", "blue_dead",
        "pink_run_1", "pink_run_2", "pink_crouch", "pink_dead",
        "cactus", "bird", "cloud"
    ]
    for name in assets:
        path = os.path.join("assets", f"{name}.png")
        if os.path.exists(path):
            if name == "cloud":
                w, h = int(90 * SCALE), int(40 * SCALE)
            else:
                # Dead skin usually uses standard Dino dimensions
                w, h = DINO_W, (CROUCH_H if "crouch" in name else DINO_H)

            img = Image.open(path).convert("RGBA").resize((w, h))
            DINO_ASSETS[name] = ImageTk.PhotoImage(img)
        else:
            print(f"Warning: Missing asset {path}")
            DINO_ASSETS[name] = None


def start_game(parent_frame, on_game_over):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    load_all_assets()

    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    GRAVITY = 0.8 * SCALE
    JUMP_POWER = -14 * (SCALE ** 0.5)

    container = tk.Frame(parent_frame, bg="black")
    container.pack(expand=True, fill="both")

    canvases = {}
    for team, color in [("A", "cyan"), ("B", "magenta")]:
        canvases[team] = tk.Canvas(container, width=CANVAS_W, height=CANVAS_H,
                                   bg=SKY_COLOR, highlightthickness=4,
                                   highlightbackground=color)
        canvases[team].pack(pady=10, padx=20)

    state = {
        "active": True,
        "speed": 7 * SCALE,
        "last_speed_tick": time.time(),
        "run_frame": 0,
        "last_anim_tick": time.time(),
        "clouds": [{"x": random.randint(0, CANVAS_W), "y": random.randint(20, 100)} for _ in range(3)],
        "A": {"y": GROUND_Y, "vy": 0, "obstacles": [], "score": 0, "crouching": False, "prev_a": False,
              "is_dead": False},
        "B": {"y": GROUND_Y, "vy": 0, "obstacles": [], "score": 0, "crouching": False, "prev_a": False,
              "is_dead": False}
    }

    def spawn_obstacle():
        obs_type = "bird" if random.random() < 0.3 else "cactus"
        y_pos = GROUND_Y - random.randint(int(45 * SCALE), int(80 * SCALE)) if obs_type == "bird" else GROUND_Y
        return {"x": CANVAS_W + random.randint(100, 400), "type": obs_type, "y": y_pos}

    for team in ["A", "B"]:
        state[team]["obstacles"].append(spawn_obstacle())

    def update():
        if not state["active"]: return

        pygame.event.pump()

        if time.time() - state["last_speed_tick"] >= 1:
            state["speed"] += 0.15 * SCALE
            state["last_speed_tick"] = time.time()

        anim_speed = max(0.05, 0.12 - (state["speed"] / SCALE) * 0.005)
        if time.time() - state["last_anim_tick"] > anim_speed:
            state["run_frame"] = 1 - state["run_frame"]
            state["last_anim_tick"] = time.time()

        for cloud in state["clouds"]:
            cloud["x"] -= (state["speed"] * 0.3)
            if cloud["x"] < -150:
                cloud["x"] = CANVAS_W + 100
                cloud["y"] = random.randint(20, 120)

        for i, team in enumerate(["A", "B"]):
            p = state[team]
            if len(joysticks) > i:
                joy = joysticks[i]
                p["crouching"] = joy.get_axis(1) > 0.5
                curr_a = joy.get_button(0)
                if curr_a and not p["prev_a"] and p["y"] >= GROUND_Y:
                    p["vy"] = JUMP_POWER
                p["prev_a"] = curr_a

            p["vy"] += GRAVITY
            p["y"] += p["vy"]
            if p["y"] > GROUND_Y:
                p["y"], p["vy"] = GROUND_Y, 0

            for obs in p["obstacles"]:
                obs["x"] -= state["speed"]

            p["obstacles"] = [o for o in p["obstacles"] if o["x"] > -100]
            if not p["obstacles"] or p["obstacles"][-1]["x"] < CANVAS_W - (300 * SCALE):
                p["obstacles"].append(spawn_obstacle())
                p["score"] += 1

            # Collision Logic
            dino_x = 60 * SCALE
            for obs in p["obstacles"]:
                if abs(obs["x"] - dino_x) < (30 * SCALE):
                    collision = False
                    if obs["type"] == "cactus" and p["y"] > GROUND_Y - (25 * SCALE):
                        collision = True
                    elif obs["type"] == "bird" and not p["crouching"]:
                        collision = True

                    if collision:
                        p["is_dead"] = True
                        render()  # Draw the dead frame
                        # Small delay so the player actually sees the dead skin
                        parent_frame.after(1000, lambda t=team: end_game(f"Team {'B' if t == 'A' else 'A'}"))
                        state["active"] = False
                        return

        render()
        parent_frame.after(16, update)

    def render():
        for team in ["A", "B"]:
            canvas = canvases[team]
            canvas.delete("all")
            p = state[team]
            color_prefix = TEAM_COLORS[team]

            # Background & Floor
            cloud_img = DINO_ASSETS.get("cloud")
            for cloud in state["clouds"]:
                if cloud_img:
                    canvas.create_image(cloud["x"], cloud["y"], image=cloud_img, anchor="center")

            sand_top = GROUND_Y + (DINO_H // 2)
            canvas.create_rectangle(0, sand_top, CANVAS_W, CANVAS_H, fill=SAND_COLOR, outline="")
            canvas.create_line(0, sand_top, CANVAS_W, sand_top, fill=SAND_LINE, width=3)

            # Sprite Selection logic including Death
            y_draw = p["y"]
            if p["is_dead"]:
                img = DINO_ASSETS.get(f"{color_prefix}_dead")
            elif p["crouching"]:
                img = DINO_ASSETS.get(f"{color_prefix}_crouch")
                y_draw += (12 * SCALE)
            else:
                frame = f"run_{state['run_frame'] + 1}"
                img = DINO_ASSETS.get(f"{color_prefix}_{frame}")

            if img:
                canvas.create_image(60 * SCALE, y_draw, image=img, anchor="center")

            for obs in p["obstacles"]:
                obs_img = DINO_ASSETS.get(obs["type"])
                if obs_img:
                    canvas.create_image(obs["x"], obs["y"], image=obs_img, anchor="center")

            canvas.create_text(CANVAS_W // 2, 40, text=f"SCORE: {p['score']}",
                               font=("Courier", int(22 * SCALE), "bold"), fill="#444")

    def end_game(winner):
        state["active"] = False
        for widget in parent_frame.winfo_children(): widget.destroy()
        on_game_over(winner)

    update()