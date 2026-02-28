import tkinter as tk
import pygame
import random
import os
import time

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

    P1_COLOR, P2_COLOR, BG_COLOR = "#0074D9", "#F012BE", "#020205"
    ALIEN_COLOR = "#2ECC40"

    canvas = tk.Canvas(parent_frame, width=800, height=600, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    # --- ASSETS ---
    current_dir = os.path.dirname(__file__)
    asset_path = os.path.join(current_dir, "assets")

    try:
        # Ships are now 1/5th size (one step smaller than 1/4)
        p1_img = tk.PhotoImage(file=os.path.join(asset_path, "blue_ship.png")).subsample(5, 5)
        p2_img = tk.PhotoImage(file=os.path.join(asset_path, "pink_ship.png")).subsample(5, 5)
        parent_frame.space_assets = {"p1": p1_img, "p2": p2_img}
    except Exception as e:
        print(f"Asset Error: {e}")
        on_game_over("Asset Error")
        return

    state = {
        "active": True,
        "timer": 10.0,
        "last_time": time.time(),
        "p_active": [True, True],
        "p_exploding": [0.0, 0.0],  # Countdown for explosion effect
        "p_pos": [[200, 520], [600, 520]],
        "p_score": [0, 0],
        "p_bullets": [[], []],
        "p_cooldown": [0, 0],
        "enemies": [],
        "spawn_timer": 0
    }

    def draw_pixel_alien(canvas, x, y):
        # Increased pixel size 'p' from 3 to 4 for bigger aliens
        p = 4
        pixels = [
            (-2, -3), (2, -3), (-1, -2), (1, -2),
            (-3, -1), (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1), (3, -1),
            (-4, 0), (-3, 0), (-1, 0), (0, 0), (1, 0), (3, 0), (4, 0),
            (-4, 1), (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
            (-3, 2), (3, 2), (-4, 3), (-2, 3), (2, 3), (4, 3)
        ]
        for dx, dy in pixels:
            canvas.create_rectangle(x + dx * p, y + dy * p, x + (dx + 1) * p, y + (dy + 1) * p, fill=ALIEN_COLOR,
                                    outline="")

    def draw_explosion(canvas, x, y, color, progress):
        # Progress goes from 0.5 down to 0
        size = (0.5 - progress) * 100
        for _ in range(8):
            rx = x + random.uniform(-size, size)
            ry = y + random.uniform(-size, size)
            canvas.create_rectangle(rx - 2, ry - 2, rx + 2, ry + 2, fill=random.choice([color, "white", "orange"]))

    def update_visuals():
        canvas.delete("all")

        # Stars
        for i in range(25):
            rx, ry = (i * 37) % 800, (i * 89) % 600
            canvas.create_oval(rx, ry, rx + 2, ry + 2, fill="#444444")

        # Bullets
        for i in range(2):
            color = P1_COLOR if i == 0 else P2_COLOR
            for b in state["p_bullets"][i]:
                canvas.create_rectangle(b[0] - 2, b[1], b[0] + 2, b[1] + 12, fill=color, outline="white")

        # Aliens
        for e in state["enemies"]:
            draw_pixel_alien(canvas, e[0], e[1])

        # Ships / Explosions
        for i in range(2):
            color = P1_COLOR if i == 0 else P2_COLOR
            if state["p_exploding"][i] > 0:
                draw_explosion(canvas, state["p_pos"][i][0], state["p_pos"][i][1], color, state["p_exploding"][i])
            elif state["p_active"][i]:
                img = parent_frame.space_assets["p1" if i == 0 else "p2"]
                canvas.create_image(state["p_pos"][i][0], state["p_pos"][i][1], image=img)

        # UI Header
        canvas.create_rectangle(200, 10, 600, 75, fill="#000", outline="#39FF14", width=2)
        t_color = "white" if state["timer"] > 2.0 else "#FF4136"
        canvas.create_text(400, 30, text=f"{state['timer']:.1f}s", fill=t_color, font=("Impact", 24))
        canvas.create_text(280, 45, text=f"P1: {state['p_score'][0]}", fill=P1_COLOR, font=("Arial", 16, "bold"))
        canvas.create_text(520, 45, text=f"P2: {state['p_score'][1]}", fill=P2_COLOR, font=("Arial", 16, "bold"))

    def check_inputs():
        if not state["active"]: return

        now = time.time()
        delta = now - state["last_time"]
        state["last_time"] = now

        state["timer"] -= delta

        # Explosion Logic
        for i in range(2):
            if state["p_exploding"][i] > 0:
                state["p_exploding"][i] -= delta
                if state["p_exploding"][i] <= 0:
                    resolve_winner()
                    return

        if state["timer"] <= 0 or (not state["p_active"][0] and not state["p_active"][1]):
            resolve_winner()
            return

        pygame.event.pump()
        for i in range(min(len(joysticks), 2)):
            if not state["p_active"][i] or state["p_exploding"][i] > 0: continue
            joy = joysticks[i]

            lx, ly = joy.get_axis(AXIS_LX), joy.get_axis(AXIS_LY)
            if abs(lx) > 0.1: state["p_pos"][i][0] = max(20, min(780, state["p_pos"][i][0] + lx * 12))
            if abs(ly) > 0.1: state["p_pos"][i][1] = max(100, min(560, state["p_pos"][i][1] + ly * 12))

            curr_a = joy.get_button(BUTTON_A)
            if curr_a and state["p_cooldown"][i] <= 0:
                state["p_bullets"][i].append([state["p_pos"][i][0], state["p_pos"][i][1] - 25])
                state["p_cooldown"][i] = 0.2

            if state["p_cooldown"][i] > 0:
                state["p_cooldown"][i] -= delta

        # Enemies Spawn
        state["spawn_timer"] -= delta
        if state["spawn_timer"] <= 0:
            state["enemies"].append([random.randint(50, 750), -30, random.uniform(-3, 3)])
            state["spawn_timer"] = 0.32

            # Bullet Update
        for i in range(2):
            for b in state["p_bullets"][i][:]:
                b[1] -= 16
                if b[1] < -20: state["p_bullets"][i].remove(b)

        # Alien Update & Collision
        for e in state["enemies"][:]:
            e[1] += 5.5
            e[0] += e[2]
            if e[1] > 650: state["enemies"].remove(e)

            # Player Hitbox (Area check)
            for i in range(2):
                if state["p_active"][i] and state["p_exploding"][i] == 0:
                    dist = ((e[0] - state["p_pos"][i][0]) ** 2 + (e[1] - state["p_pos"][i][1]) ** 2) ** 0.5
                    if dist < 28:  # Increased hitbox because aliens are bigger
                        state["p_active"][i] = False
                        state["p_exploding"][i] = 0.5  # Start 0.5s explosion

            # Bullet Hitbox
            for i in range(2):
                for b in state["p_bullets"][i][:]:
                    dist_b = ((e[0] - b[0]) ** 2 + (e[1] - b[1]) ** 2) ** 0.5
                    if dist_b < 22:
                        state["p_score"][i] += 1
                        if e in state["enemies"]: state["enemies"].remove(e)
                        if b in state["p_bullets"][i]: state["p_bullets"][i].remove(b)

        update_visuals()
        parent_frame.after(16, check_inputs)

    def resolve_winner():
        state["active"] = False
        s1, s2 = state["p_score"]
        # If someone exploded, they lose immediately regardless of score
        if state["p_exploding"][0] > 0 or not state["p_active"][0]:
            winner = "Team B"
        elif state["p_exploding"][1] > 0 or not state["p_active"][1]:
            winner = "Team A"
        else:
            if s1 > s2:
                winner = "Team A"
            elif s2 > s1:
                winner = "Team B"
            else:
                winner = "Tie"
        on_game_over(winner)

    check_inputs()