import tkinter as tk
import pygame
import random
import math
from PIL import Image, ImageTk
import os

# Mapping for Xbox Controllers
AXIS_X = 0


def start_game(parent_frame, on_game_over):
    # 1. Anchor the path to the directory where this script lives
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 2. Attach sprites to parent_frame to prevent Tkinter garbage collection
    parent_frame.sprites = {"blue": {}, "pink": {}}

    def load_all_assets():
        """Attempts to load images with absolute pathing."""
        colors = ["blue", "pink"]
        poses = ["crouch_left", "jump_left", "crouch_right", "jump_right"]

        for color in colors:
            for pose in poses:
                # Use BASE_DIR to build the absolute path
                file_path = os.path.join(BASE_DIR, "assets", f"{color}_{pose}.png")
                if os.path.exists(file_path):
                    try:
                        # Resampling.LANCZOS added for cleaner scaling
                        img = Image.open(file_path).convert("RGBA").resize((60, 60), Image.Resampling.LANCZOS)
                        parent_frame.sprites[color][pose] = ImageTk.PhotoImage(img)
                    except Exception as e:
                        print(f"Error rendering {file_path}: {e}")
                else:
                    print(f"FILE NOT FOUND: {file_path}")

    # Load assets securely onto the frame before starting
    load_all_assets()

    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks: joy.init()

    # Game Settings
    CANVAS_W, CANVAS_H = 350, 500
    WIN_HEIGHT, GRAVITY, JUMP_STRENGTH, MOVE_SPEED = 2500, 0.6, -15, 9

    state = {
        "active": True,
        "frame": 0,
        "A": {"x": 175, "y": 400, "vy": 0, "cam": 0, "platforms": [], "color": "blue", "facing": "right"},
        "B": {"x": 175, "y": 400, "vy": 0, "cam": 0, "platforms": [], "color": "pink", "facing": "right"},
    }

    def gen_platforms():
        plist = [{"x": 175, "y": 450, "m": False, "off": 0}]
        for i in range(1, 40):
            plist.append({
                "x": random.randint(60, CANVAS_W - 60),
                "y": 450 - (i * 90),
                "m": i > 5 and random.random() > 0.4,
                "off": random.uniform(0, 6.28),
                "speed": 0.05 + (i * 0.002),
            })
        return plist

    state["A"]["platforms"] = gen_platforms()
    state["B"]["platforms"] = gen_platforms()

    container = tk.Frame(parent_frame, bg="black")
    container.pack(expand=True)

    canvas_a = tk.Canvas(container, width=CANVAS_W, height=CANVAS_H, bg="#050510", highlightthickness=2,
                         highlightbackground="cyan")
    canvas_a.pack(side="left", padx=10, pady=20)

    canvas_b = tk.Canvas(container, width=CANVAS_W, height=CANVAS_H, bg="#100510", highlightthickness=2,
                         highlightbackground="magenta")
    canvas_b.pack(side="right", padx=10, pady=20)

    def update_game():
        # CRASH FIX: If the game is inactive or the container is gone, STOP immediately
        if not state["active"] or not container.winfo_exists():
            return

        state["frame"] += 1
        pygame.event.pump()

        for i, p_key in enumerate(["A", "B"]):
            p = state[p_key]
            p["vy"] += GRAVITY
            p["y"] += p["vy"]

            if len(joysticks) > i:
                axis_val = joysticks[i].get_axis(AXIS_X)
                p["x"] += axis_val * MOVE_SPEED
                if axis_val > 0.2:
                    p["facing"] = "right"
                elif axis_val < -0.2:
                    p["facing"] = "left"
            p["x"] %= CANVAS_W

            for plt in p["platforms"]:
                cx = plt["x"] + (math.sin(state["frame"] * plt.get("speed", 0) + plt["off"]) * 70 if plt["m"] else 0)
                if p["vy"] > 0 and (plt["y"] < p["y"] + 20 < plt["y"] + 30) and (cx - 45 < p["x"] < cx + 45):
                    p["vy"] = JUMP_STRENGTH
            if p["y"] < p["cam"] + 200: p["cam"] = p["y"] - 200

        try:
            render(canvas_a, "A")
            render(canvas_b, "B")
        except tk.TclError:  # Safety for when window closes
            return

        for team in ["A", "B"]:
            p = state[team]
            # --- Output correct win strings ---
            if p["y"] < -WIN_HEIGHT:
                winner_str = "Blue Wins" if team == "A" else "Pink Wins"
                end_game(winner_str)
                return
            if p["y"] > p["cam"] + CANVAS_H:
                winner_str = "Pink Wins" if team == "A" else "Blue Wins"
                end_game(winner_str)
                return

        parent_frame.after(16, update_game)

    def render(canvas, key):
        if not canvas.winfo_exists(): return
        canvas.delete("all")
        p = state[key]
        off = p["cam"]

        # Finish line & Platforms
        canvas.create_rectangle(0, -WIN_HEIGHT - off, CANVAS_W, -WIN_HEIGHT - off + 20, fill="yellow")
        for plt in p["platforms"]:
            px = plt["x"] + (math.sin(state["frame"] * plt.get("speed", 0) + plt["off"]) * 70 if plt["m"] else 0)
            py = plt["y"] - off
            if -20 < py < CANVAS_H + 20:
                canvas.create_rectangle(px - 30, py, px + 30, py + 8, fill="#3498db" if plt["m"] else "white",
                                        outline="gray")

        # Sprite logic
        pose = "jump" if p["vy"] < 0 else "crouch"
        sprite_key = f"{pose}_{p['facing']}"

        # Pull from the attached dictionary
        img_obj = parent_frame.sprites[p["color"]].get(sprite_key)

        if img_obj:
            canvas.create_image(p["x"], p["y"] - off, image=img_obj, anchor="center")
        else:
            # RECTANGLE FALLBACK
            canvas.create_rectangle(p["x"] - 15, (p["y"] - off) - 15, p["x"] + 15, (p["y"] - off) + 15, fill=p["color"],
                                    outline="white")

    def end_game(winner):
        state["active"] = False
        if container.winfo_exists():
            container.destroy()
        on_game_over(winner)

    update_game()