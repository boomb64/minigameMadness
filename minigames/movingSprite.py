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

    P1_COLOR, P2_COLOR, BG_COLOR = "#0074D9", "#F012BE", "#000000"

    canvas = tk.Canvas(parent_frame, width=800, height=600, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    # --- ASSET PATHING ---
    current_dir = os.path.dirname(__file__)
    asset_path = os.path.join(current_dir, "assets")

    try:
        all_files = os.listdir(asset_path)
        # Filters for basic fish sprites
        fish_files = [f for f in all_files if f.endswith(
            ".png") and "hook" not in f and "run" not in f and "dead" not in f and "crouch_right" not in f and "jump_right" not in f]
    except FileNotFoundError:
        on_game_over("Path Error")
        return

    target_filename = random.choice(fish_files)
    decoy_pool = [f for f in fish_files if f != target_filename]

    parent_frame.hidden_assets = {}
    for f in fish_files:
        parent_frame.hidden_assets[f] = tk.PhotoImage(file=os.path.join(asset_path, f)).subsample(4, 4)

    parent_frame.title_img = tk.PhotoImage(file=os.path.join(asset_path, target_filename)).subsample(5, 5)

    assets = parent_frame.hidden_assets
    target_img = assets[target_filename]

    # Initialize Decoyst with slow random velocities
    decoys = []
    for _ in range(150):
        fname = random.choice(decoy_pool)
        decoys.append({
            "img": assets[fname],
            "x": random.randint(30, 770),
            "y": random.randint(120, 570),
            "vx": random.uniform(-1, 1) * 55,
            "vy": random.uniform(-1, 1) * 55
        })

    HIT_RADIUS = 25

    state = {
        "active": True,
        "timer": 5.0,
        "last_time": time.time(),
        "p_pos": [[200, 350], [600, 350]],
        "p_mistakes": [0, 0],
        "prev_a": [False, False],
        "target_x": random.randint(100, 700),
        "target_y": random.randint(150, 500),
        "target_vx": random.uniform(-1, 1) * 55,
        "target_vy": random.uniform(-1, 1) * 55
    }

    def update_visuals():
        canvas.delete("all")

        # 1. Background school
        for i in range(75):
            d = decoys[i]
            canvas.create_image(d["x"], d["y"], image=d["img"])

        # 2. THE TARGET
        canvas.create_image(state["target_x"], state["target_y"], image=target_img)

        # 3. Foreground school
        for i in range(75, 100):
            d = decoys[i]
            canvas.create_image(d["x"], d["y"], image=d["img"])

        # 4. Outlined Cursors (Drawn above fish but below header)
        for i in range(2):
            color = P1_COLOR if i == 0 else P2_COLOR
            x, y = state["p_pos"][i]

            # --- WHITE OUTLINE LAYER ---
            canvas.create_line(x - 17, y, x + 17, y, fill="white", width=4)
            canvas.create_line(x, y - 17, x, y + 17, fill="white", width=4)
            canvas.create_oval(x - 12, y - 12, x + 12, y + 12, outline="white", width=4)

            # --- COLORED CENTER LAYER ---
            canvas.create_line(x - 15, y, x + 15, y, fill=color, width=2)
            canvas.create_line(x, y - 15, x, y + 15, fill=color, width=2)
            canvas.create_oval(x - 10, y - 10, x + 10, y + 10, outline=color, width=2)

        # 5. Header (On top of everything)
        canvas.create_rectangle(145, 15, 655, 95, fill="#000", outline="#39FF14", width=3)
        t_color = "white" if state["timer"] > 1.5 else "#FF4136"
        canvas.create_text(210, 55, text=f"{state['timer']:.1f}s", fill=t_color, font=("Impact", 24))
        canvas.create_text(370, 55, text="TARGET:", fill="white", font=("Impact", 22))
        canvas.create_image(520, 55, image=parent_frame.title_img)

        # Mistakes UI
        for i in range(2):
            ui_x = 580 if i == 0 else 610
            for m in range(3):
                m_color = "red" if state["p_mistakes"][i] > m else "#222"
                canvas.create_oval(ui_x, 30 + (m * 15), ui_x + 10, 40 + (m * 15), fill=m_color, outline="white")

    def check_inputs():
        if not state["active"]: return

        current_now = time.time()
        delta = current_now - state["last_time"]
        state["last_time"] = current_now

        state["timer"] -= delta
        if state["timer"] <= 0:
            state["timer"] = 0
            handle_timeout()
            return

        # Bounce Physics
        for d in decoys:
            d["x"] += d["vx"] * delta
            d["y"] += d["vy"] * delta
            if d["x"] < 20 or d["x"] > 780: d["vx"] *= -1
            if d["y"] < 110 or d["y"] > 580: d["vy"] *= -1

        state["target_x"] += state["target_vx"] * delta
        state["target_y"] += state["target_vy"] * delta
        if state["target_x"] < 20 or state["target_x"] > 780: state["target_vx"] *= -1
        if state["target_y"] < 110 or state["target_y"] > 580: state["target_vy"] *= -1

        pygame.event.pump()
        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]
            lx, ly = joy.get_axis(AXIS_LX), joy.get_axis(AXIS_LY)

            if abs(lx) > 0.1: state["p_pos"][i][0] = max(10, min(790, state["p_pos"][i][0] + lx * 15))
            if abs(ly) > 0.1: state["p_pos"][i][1] = max(10, min(590, state["p_pos"][i][1] + ly * 15))

            curr_a = joy.get_button(BUTTON_A)
            if curr_a and not state["prev_a"][i]:
                px, py = state["p_pos"][i]
                tx, ty = state["target_x"], state["target_y"]
                dist = ((px - tx) ** 2 + (py - ty) ** 2) ** 0.5
                if dist <= HIT_RADIUS:
                    end_game("Team A" if i == 0 else "Team B")
                    return
                else:
                    state["p_mistakes"][i] += 1
                    if state["p_mistakes"][i] >= 3:
                        end_game("Team B" if i == 0 else "Team A")
                        return
            state["prev_a"][i] = curr_a

        update_visuals()
        parent_frame.after(16, check_inputs)

    def handle_timeout():
        m1, m2 = state["p_mistakes"]
        if m1 < m2:
            end_game("Team A")
        elif m2 < m1:
            end_game("Team B")
        else:
            end_game("Tie")

    def end_game(winner):
        state["active"] = False
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    check_inputs()