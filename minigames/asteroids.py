import tkinter as tk
import pygame
import math
import random
import time

# --- Xbox Controller Mapping ---
BUTTON_A = 0
AXIS_LEFT_STICK_X = 0  # -1.0 Left, 1.0 Right
AXIS_LEFT_STICK_Y = 1  # -1.0 Up, 1.0 Down


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    canvas_w = 800
    canvas_h = 600
    game_duration = 10.0

    state = {
        "active": True,
        "start_time": time.time(),
        "bullets": [],
        "asteroids": [],
        "ships": {
            "Team A": {"x": 370, "y": 300, "dx": 0, "dy": 0, "angle": 180, "score": 0, "alive": True, "prev_a": False,
                       "color": "cyan", "joy_idx": 0},
            "Team B": {"x": 430, "y": 300, "dx": 0, "dy": 0, "angle": 0, "score": 0, "alive": True, "prev_a": False,
                       "color": "magenta", "joy_idx": 1}
        }
    }

    canvas = tk.Canvas(parent_frame, width=canvas_w, height=canvas_h, bg="black", highlightthickness=0)
    canvas.pack(expand=True)

    ui_text = canvas.create_text(canvas_w // 2, 30, text="10.0 | A: 0 | B: 0", fill="white",
                                 font=("Courier", 20, "bold"))

    # --- Helper Functions ---
    def spawn_edge_asteroid():
        """Spawns a slow, large asteroid at the edge."""
        edge = random.choice(["top", "bottom", "left", "right"])
        speed_min, speed_max = 0.3, 1.0  # SLOWED DOWN

        if edge == "top":
            x, y = random.uniform(0, canvas_w), -40
            dx, dy = random.uniform(-1, 1), random.uniform(speed_min, speed_max)
        elif edge == "bottom":
            x, y = random.uniform(0, canvas_w), canvas_h + 40
            dx, dy = random.uniform(-1, 1), random.uniform(-speed_max, -speed_min)
        elif edge == "left":
            x, y = -40, random.uniform(0, canvas_h)
            dx, dy = random.uniform(speed_min, speed_max), random.uniform(-1, 1)
        else:  # right
            x, y = canvas_w + 40, random.uniform(0, canvas_h)
            dx, dy = random.uniform(-speed_max, -speed_min), random.uniform(-1, 1)

        return {
            "x": x, "y": y, "dx": dx, "dy": dy,
            "radius": random.randint(20, 30),  # Guaranteed large
            "id": canvas.create_oval(0, 0, 0, 0, outline="gray", width=2)
        }

    def spawn_split_asteroid(x, y, parent_radius):
        """Spawns a smaller asteroid bursting from a destroyed one."""
        return {
            "x": x, "y": y,
            "dx": random.uniform(-2.0, 2.0),  # Bursts out faster
            "dy": random.uniform(-2.0, 2.0),
            "radius": parent_radius // 2,
            "id": canvas.create_oval(0, 0, 0, 0, outline="gray", width=2)
        }

    def draw_ship(ship):
        rad = math.radians(ship["angle"])
        x1 = ship["x"] + math.cos(rad) * 20
        y1 = ship["y"] + math.sin(rad) * 20
        x2 = ship["x"] + math.cos(rad + 2.5) * 15
        y2 = ship["y"] + math.sin(rad + 2.5) * 15
        x3 = ship["x"] + math.cos(rad - 2.5) * 15
        y3 = ship["y"] + math.sin(rad - 2.5) * 15
        return [x1, y1, x2, y2, x3, y3]

    # Initialize Graphics
    for _ in range(12):  # Start with fewer rocks since they split now
        ast = spawn_edge_asteroid()
        ast["x"] += ast["dx"] * random.uniform(0, 50)
        ast["y"] += ast["dy"] * random.uniform(0, 50)
        state["asteroids"].append(ast)

    ship_gfx = {
        "Team A": canvas.create_polygon(0, 0, 0, 0, 0, 0, outline="cyan", fill="", width=2),
        "Team B": canvas.create_polygon(0, 0, 0, 0, 0, 0, outline="magenta", fill="", width=2)
    }

    def update_game():
        if not state["active"]: return

        time_left = max(0, game_duration - (time.time() - state["start_time"]))
        pygame.event.pump()

        # A. Process Inputs & Physics for Ships
        for team, ship in state["ships"].items():
            if not ship["alive"]: continue

            joy_idx = ship["joy_idx"]
            if joy_idx < len(joysticks):
                joy = joysticks[joy_idx]

                # Analog Direction and Thrust
                joy_x = joy.get_axis(AXIS_LEFT_STICK_X)
                joy_y = joy.get_axis(AXIS_LEFT_STICK_Y)
                magnitude = math.hypot(joy_x, joy_y)

                # Deadzone check so resting stick doesn't fire thrusters
                if magnitude > 0.2:
                    # Set rotation to stick angle
                    ship["angle"] = math.degrees(math.atan2(joy_y, joy_x))

                    # Apply thrust based on how hard the stick is pushed
                    thrust = magnitude * 0.4
                    rad = math.radians(ship["angle"])
                    ship["dx"] += math.cos(rad) * thrust
                    ship["dy"] += math.sin(rad) * thrust

                # Shooting
                current_a = joy.get_button(BUTTON_A)
                if current_a and not ship["prev_a"]:
                    rad = math.radians(ship["angle"])
                    state["bullets"].append({
                        "x": ship["x"] + math.cos(rad) * 20,
                        "y": ship["y"] + math.sin(rad) * 20,
                        "dx": math.cos(rad) * 12,
                        "dy": math.sin(rad) * 12,
                        "owner": team,
                        "life": 40,
                        "id": canvas.create_oval(0, 0, 0, 0, fill=ship["color"])
                    })
                ship["prev_a"] = current_a

            # Apply friction and wrap ships
            ship["dx"] *= 0.95  # Increased friction so you can stop easier
            ship["dy"] *= 0.95
            ship["x"] = (ship["x"] + ship["dx"]) % canvas_w
            ship["y"] = (ship["y"] + ship["dy"]) % canvas_h
            canvas.coords(ship_gfx[team], *draw_ship(ship))

        # B. Process Bullets
        for b in state["bullets"][:]:
            b["x"] = (b["x"] + b["dx"]) % canvas_w
            b["y"] = (b["y"] + b["dy"]) % canvas_h
            b["life"] -= 1
            if b["life"] <= 0:
                canvas.delete(b["id"])
                state["bullets"].remove(b)
            else:
                canvas.coords(b["id"], b["x"] - 2, b["y"] - 2, b["x"] + 2, b["y"] + 2)

        # C. Process Asteroids & Collisions
        new_asteroids = []
        for ast in state["asteroids"][:]:
            ast["x"] += ast["dx"]
            ast["y"] += ast["dy"]

            # Remove and replace if it drifts way off screen
            if ast["x"] < -100 or ast["x"] > canvas_w + 100 or ast["y"] < -100 or ast["y"] > canvas_h + 100:
                canvas.delete(ast["id"])
                state["asteroids"].remove(ast)
                new_asteroids.append(spawn_edge_asteroid())
                continue

            canvas.coords(ast["id"], ast["x"] - ast["radius"], ast["y"] - ast["radius"], ast["x"] + ast["radius"],
                          ast["y"] + ast["radius"])

            # Asteroid vs Bullet
            hit = False
            for b in state["bullets"][:]:
                dist = math.hypot(ast["x"] - b["x"], ast["y"] - b["y"])
                if dist < ast["radius"]:
                    state["ships"][b["owner"]]["score"] += 1
                    canvas.delete(b["id"])
                    if b in state["bullets"]: state["bullets"].remove(b)
                    hit = True
                    break

            if hit:
                canvas.delete(ast["id"])
                state["asteroids"].remove(ast)

                # Split mechanics
                if ast["radius"] >= 20:  # If it's a large asteroid
                    new_asteroids.append(spawn_split_asteroid(ast["x"], ast["y"], ast["radius"]))
                    new_asteroids.append(spawn_split_asteroid(ast["x"], ast["y"], ast["radius"]))

                # Always spawn a new edge one to replace the destroyed rock (keeps the swarm full)
                new_asteroids.append(spawn_edge_asteroid())
                continue

            # Asteroid vs Ship
            for team, ship in state["ships"].items():
                if ship["alive"]:
                    dist = math.hypot(ast["x"] - ship["x"], ast["y"] - ship["y"])
                    if dist < ast["radius"] + 10:
                        ship["alive"] = False
                        canvas.delete(ship_gfx[team])

        state["asteroids"].extend(new_asteroids)

        # D. Update UI
        score_a = state["ships"]["Team A"]["score"]
        score_b = state["ships"]["Team B"]["score"]
        canvas.itemconfig(ui_text, text=f"{time_left:.1f}s | A: {score_a} | B: {score_b}")

        # E. Win/Loss Conditions
        a_dead = not state["ships"]["Team A"]["alive"]
        b_dead = not state["ships"]["Team B"]["alive"]

        if a_dead and not b_dead:
            end_game("Team B")
        elif b_dead and not a_dead:
            end_game("Team A")
        elif a_dead and b_dead:
            end_game("Tie")
        elif time_left <= 0:
            if score_a > score_b:
                end_game("Team A")
            elif score_b > score_a:
                end_game("Team B")
            else:
                end_game("Tie")
        else:
            parent_frame.after(16, update_game)

    def end_game(winner):
        state["active"] = False
        canvas.destroy()
        for widget in parent_frame.winfo_children():
            widget.destroy()

        if winner == "Tie":
            winner = random.choice(["Team A", "Team B"])

        on_game_over(winner)

    update_game()