import tkinter as tk
import pygame
import random
import os
import time  # Added for real-time accuracy

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

    P1_COLOR, P2_COLOR, BG_COLOR = "#0074D9", "#F012BE", "#00000"

    canvas = tk.Canvas(parent_frame, width=800, height=600, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    # --- ASSET PATHING ---
    current_dir = os.path.dirname(__file__)
    asset_path = os.path.join(current_dir, "assets")

    try:
        all_files = os.listdir(asset_path)
        fish_files = [f for f in all_files if f.endswith(".png") and "hook" not in f and "run" not in f and "dead" not in f and "crouch_right" not in f and "jump_right" not in f]
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

    decoys = []
    for _ in range(150):
        fname = random.choice(decoy_pool)
        decoys.append({"img": assets[fname], "x": random.randint(30, 770), "y": random.randint(120, 570)})

    target_pos = (random.randint(100, 700), random.randint(150, 500))
    HIT_RADIUS = 25

    state = {
        "active": True,
        "timer": 5.0,
        "last_time": time.time(),  # Track exactly when the game started
        "p_pos": [[200, 350], [600, 350]],
        "p_mistakes": [0, 0],
        "prev_a": [False, False]
    }

    def update_visuals():
        canvas.delete("all")
        for i in range(100):
            canvas.create_image(decoys[i]["x"], decoys[i]["y"], image=decoys[i]["img"])
        canvas.create_image(target_pos[0], target_pos[1], image=target_img)
        for i in range(100, 150):
            canvas.create_image(decoys[i]["x"], decoys[i]["y"], image=decoys[i]["img"])

        for i in range(2):
            color = P1_COLOR if i == 0 else P2_COLOR
            x, y = state["p_pos"][i]
            canvas.create_line(x - 15, y, x + 15, y, fill=color, width=2)
            canvas.create_line(x, y - 15, x, y + 15, fill=color, width=2)
            canvas.create_oval(x - 10, y - 10, x + 10, y + 10, outline=color, width=2)

        # Stand-out Header
        canvas.create_rectangle(145, 15, 655, 95, fill="#000", outline="#39FF14", width=3)
        t_color = "white" if state["timer"] > 1.5 else "#FF4136"
        canvas.create_text(210, 55, text=f"{state['timer']:.1f}s", fill=t_color, font=("Impact", 24))
        canvas.create_text(370, 55, text="TARGET:", fill="white", font=("Impact", 22))
        canvas.create_image(520, 55, image=parent_frame.title_img)

        for i in range(2):
            ui_x = 580 if i == 0 else 610
            for m in range(3):
                m_color = "red" if state["p_mistakes"][i] > m else "#222"
                canvas.create_oval(ui_x, 30 + (m * 15), ui_x + 10, 40 + (m * 15), fill=m_color, outline="white")

    def check_inputs():
        if not state["active"]: return

        # --- ACCURATE REAL-TIME TIMER ---
        current_now = time.time()
        delta = current_now - state["last_time"]
        state["last_time"] = current_now

        state["timer"] -= delta
        if state["timer"] <= 0:
            state["timer"] = 0
            handle_timeout()
            return

        pygame.event.pump()
        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]
            lx, ly = joy.get_axis(AXIS_LX), joy.get_axis(AXIS_LY)

            if abs(lx) > 0.1: state["p_pos"][i][0] = max(10, min(790, state["p_pos"][i][0] + lx * 14))
            if abs(ly) > 0.1: state["p_pos"][i][1] = max(10, min(590, state["p_pos"][i][1] + ly * 14))

            curr_a = joy.get_button(BUTTON_A)
            if curr_a and not state["prev_a"][i]:
                px, py = state["p_pos"][i]
                tx, ty = target_pos
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