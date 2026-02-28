import tkinter as tk
from PIL import Image, ImageTk
import pygame
import math
import random
import time
import os

# --- Xbox Controller Mapping ---
BUTTON_A = 0
AXIS_LEFT_STICK_X = 0
AXIS_LEFT_STICK_Y = 1


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # --- Robust Path Resolution ---
    current_file_path = os.path.abspath(__file__)
    base_dir = os.path.dirname(current_file_path)
    assets_dir = os.path.join(base_dir, "assets")

    canvas_w = 800
    canvas_h = 600
    game_duration = 10.0

    state = {
        "active": True,
        "game_finished": False,
        "start_time": time.time(),
        "bullets": [],
        "asteroids": [],
        "stars": [],
        "ships": {
            "Team A": {"x": 300, "y": 300, "dx": 0, "dy": 0, "angle": 0, "score": 0, "alive": True, "prev_a": False,
                       "color": "blue", "joy_idx": 0, "img_name": "blue_ship.png"},
            "Team B": {"x": 500, "y": 300, "dx": 0, "dy": 0, "angle": 180, "score": 0, "alive": True, "prev_a": False,
                       "color": "pink", "joy_idx": 1, "img_name": "pink_ship.png"}
        }
    }

    canvas = tk.Canvas(parent_frame, width=canvas_w, height=canvas_h, bg="black", highlightthickness=0)
    canvas.pack(expand=True)

    # --- Load and Scale Sprites (1/8 Scale + 90deg CCW Rotate) ---
    ship_base_images = {}
    for team, ship in state["ships"].items():
        try:
            full_path = os.path.join(assets_dir, ship["img_name"])
            full_img = Image.open(full_path).convert("RGBA")
            new_w = max(1, full_img.width // 8)
            new_h = max(1, full_img.height // 8)
            resized = full_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            # Rotate 90 CCW to align the nose with the engine's 0-degree (East) vector
            ship_base_images[team] = resized.rotate(-90, expand=True)
        except Exception as e:
            print(f"FAILED TO LOAD {ship['img_name']}: {e}")
            ship_base_images[team] = Image.new("RGBA", (25, 25), (0, 0, 0, 0))

    # --- Twinkling Starfield (Reduced count) ---
    for _ in range(15):
        x, y = random.randint(0, canvas_w), random.randint(0, canvas_h)
        star_id = canvas.create_oval(x, y, x + 2, y + 2, fill="yellow", outline="")
        state["stars"].append({"id": star_id, "blink_timer": random.randint(20, 100)})

    ui_text = canvas.create_text(canvas_w // 2, 30, text="10.0 | Blue: 0 | Pink: 0", fill="white",
                                 font=("Courier", 20, "bold"))

    def spawn_asteroid(radius=None, x=None, y=None, is_edge=True):
        if is_edge:
            edge = random.choice(["top", "bottom", "left", "right"])
            if edge == "top":
                x, y = random.uniform(0, canvas_w), -40
            elif edge == "bottom":
                x, y = random.uniform(0, canvas_w), canvas_h + 40
            elif edge == "left":
                x, y = -40, random.uniform(0, canvas_h)
            else:
                x, y = canvas_w + 40, random.uniform(0, canvas_h)
            dx, dy = random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)
            rad = random.randint(25, 35)
        else:
            dx, dy = random.uniform(-2.5, 2.5), random.uniform(-2.5, 2.5)
            rad = radius

        return {
            "x": x, "y": y, "dx": dx, "dy": dy, "radius": rad,
            "id": canvas.create_oval(0, 0, 0, 0, outline="gray", width=2)
        }

    for _ in range(8):
        ast = spawn_asteroid()
        # Removed the line overwriting x and y so they safely spawn at the edges!
        state["asteroids"].append(ast)

    ship_canvas_ids = {
        "Team A": canvas.create_image(300, 300, anchor="center"),
        "Team B": canvas.create_image(500, 300, anchor="center")
    }
    persistent_tk_images = {"Team A": None, "Team B": None}

    def update_game():
        if not state["active"] or state["game_finished"]:
            return

        time_left = max(0, game_duration - (time.time() - state["start_time"]))
        pygame.event.pump()

        # Twinkle stars
        for star in state["stars"]:
            star["blink_timer"] -= 1
            if star["blink_timer"] <= 0:
                cur = canvas.itemcget(star["id"], "state")
                canvas.itemconfig(star["id"], state="hidden" if cur == "normal" else "normal")
                star["blink_timer"] = random.randint(30, 90)

        # Update Ships
        for team, ship in state["ships"].items():
            if not ship["alive"]: continue

            if ship["joy_idx"] < len(joysticks):
                joy = joysticks[ship["joy_idx"]]
                jx, jy = joy.get_axis(AXIS_LEFT_STICK_X), joy.get_axis(AXIS_LEFT_STICK_Y)
                if math.hypot(jx, jy) > 0.2:
                    ship["angle"] = math.degrees(math.atan2(jy, jx))
                    rad = math.radians(ship["angle"])
                    ship["dx"] += math.cos(rad) * 0.5
                    ship["dy"] += math.sin(rad) * 0.5

                if joy.get_button(BUTTON_A) and not ship["prev_a"]:
                    rad = math.radians(ship["angle"])
                    # Bullet Offset: Centered at nose
                    state["bullets"].append({
                        "x": ship["x"] + math.cos(rad) * 20,
                        "y": ship["y"] + math.sin(rad) * 20,
                        "dx": math.cos(rad) * 12, "dy": math.sin(rad) * 12,
                        "owner": team, "life": 45,
                        "id": canvas.create_oval(0, 0, 0, 0, fill=ship["color"], outline="white")
                    })
                ship["prev_a"] = joy.get_button(BUTTON_A)

            ship["dx"] *= 0.94
            ship["dy"] *= 0.94
            ship["x"] = (ship["x"] + ship["dx"]) % canvas_w
            ship["y"] = (ship["y"] + ship["dy"]) % canvas_h

            rotated_pil = ship_base_images[team].rotate(-ship["angle"], expand=True)
            tk_img = ImageTk.PhotoImage(rotated_pil)
            persistent_tk_images[team] = tk_img
            canvas.itemconfig(ship_canvas_ids[team], image=tk_img)
            canvas.coords(ship_canvas_ids[team], ship["x"], ship["y"])

        # Update Bullets
        for b in state["bullets"][:]:
            b["x"] = (b["x"] + b["dx"]) % canvas_w
            b["y"] = (b["y"] + b["dy"]) % canvas_h
            b["life"] -= 1
            if b["life"] <= 0:
                canvas.delete(b["id"])
                state["bullets"].remove(b)
            else:
                canvas.coords(b["id"], b["x"] - 4, b["y"] - 4, b["x"] + 4, b["y"] + 4)

        # Update Asteroids & Collision
        new_list = []
        for ast in state["asteroids"][:]:
            ast["x"] = (ast["x"] + ast["dx"]) % canvas_w
            ast["y"] = (ast["y"] + ast["dy"]) % canvas_h
            canvas.coords(ast["id"], ast["x"] - ast["radius"], ast["y"] - ast["radius"],
                          ast["x"] + ast["radius"], ast["y"] + ast["radius"])

            hit = False
            for b in state["bullets"][:]:
                if math.hypot(ast["x"] - b["x"], ast["y"] - b["y"]) < ast["radius"]:
                    state["ships"][b["owner"]]["score"] += 1
                    canvas.delete(b["id"])
                    if b in state["bullets"]: state["bullets"].remove(b)
                    hit = True
                    break

            if hit:
                if ast["radius"] > 15:
                    new_list.append(spawn_asteroid(ast["radius"] // 2, ast["x"], ast["y"], False))
                    new_list.append(spawn_asteroid(ast["radius"] // 2, ast["x"], ast["y"], False))
                canvas.delete(ast["id"])
                state["asteroids"].remove(ast)
                state["asteroids"].append(spawn_asteroid())
                continue

            for team, ship in state["ships"].items():
                if ship["alive"] and math.hypot(ast["x"] - ship["x"], ast["y"] - ship["y"]) < ast["radius"] + 10:
                    ship["alive"] = False
                    canvas.delete(ship_canvas_ids[team])

        state["asteroids"].extend(new_list)

        score_a, score_b = state["ships"]["Team A"]["score"], state["ships"]["Team B"]["score"]
        canvas.itemconfig(ui_text, text=f"{time_left:.1f}s | Blue: {score_a} | Pink: {score_b}")

        # Win/Loss Logic
        a_dead, b_dead = not state["ships"]["Team A"]["alive"], not state["ships"]["Team B"]["alive"]
        if (a_dead or b_dead or time_left <= 0) and not state["game_finished"]:
            state["game_finished"] = True
            if a_dead and not b_dead:
                winner = "Team B"
            elif b_dead and not a_dead:
                winner = "Team A"
            elif score_a > score_b:
                winner = "Team A"
            elif score_b > score_a:
                winner = "Team B"
            else:
                winner = "Tie"

            parent_frame.after(1, lambda: end_game(winner))
            return

        if state["active"] and not state["game_finished"]:
            parent_frame.after(16, update_game)

    def end_game(winner):
        state["active"] = False
        canvas.delete("all")
        canvas.config(bg="black")

        txt, clr = "Tie", "yellow"
        if winner == "Team A":
            txt, clr = "Blue Wins", "blue"
        elif winner == "Team B":
            txt, clr = "Pink Wins", "pink"

        canvas.create_text(canvas_w // 2, canvas_h // 2, text=txt, fill=clr, font=("Courier", 60, "bold"))

        # 3 second display before return
        parent_frame.after(3000, lambda: cleanup_and_exit(winner))

    def cleanup_and_exit(winner):
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    update_game()