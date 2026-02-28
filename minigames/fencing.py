import tkinter as tk
from PIL import Image, ImageTk
import pygame
import os

# Mapping for Xbox Controllers
BUTTON_X = 2
BUTTON_B = 1
AXIS_X = 0


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks: joy.init()

    main_container = tk.Frame(parent_frame, bg="black")
    main_container.pack(expand=True)

    canvas = tk.Canvas(main_container, width=800, height=450, bg="#1a1a1a", highlightthickness=0)
    canvas.pack(pady=20)

    # --- IMAGE LOADING SECTION ---
    def load_img(name, size=(100, 140)):
        path = os.path.join("assets", name)
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            # Fallback placeholder if file is missing
            placeholder = Image.new('RGBA', size, color=(255, 0, 255, 100))
            return ImageTk.PhotoImage(placeholder)

    # We load the lunge assets with a much larger width (180 vs 100)
    assets = {
        "blue_idle": load_img("blue_idle.png"),
        "blue_block": load_img("blue_block.png"),
        "blue_lunge": load_img("blue_lunge.png", size=(180, 140)),  # INCREASED SIZE

        "pink_idle": load_img("pink_idle.png"),
        "pink_block": load_img("pink_block.png"),
        "pink_lunge": load_img("pink_lunge.png", size=(180, 140)),  # INCREASED SIZE

        "dead": load_img("dead.png", size=(140, 80))  # Dead is wider than tall
    }

    # Arena Decoration
    canvas.create_rectangle(0, 350, 800, 450, fill="#2c3e50", outline="")
    s_bar_a = canvas.create_rectangle(50, 20, 300, 40, fill="#2ecc71")
    s_bar_b = canvas.create_rectangle(500, 20, 750, 40, fill="#2ecc71")

    state = {
        "p1_pos": 200, "p2_pos": 600,
        "p1_stam": 100.0, "p2_stam": 100.0,
        "p1_blocking": False, "p2_blocking": False,
        "p1_lunge_timer": 0, "p2_lunge_timer": 0,
        "active": True,
        "base_reach": 60,  # Standard reach
        "lunge_reach": 160,  # Matches the new larger image width
        "prev_x1": False, "prev_x2": False
    }

    # P1 anchored South-West (grows right), P2 anchored South-East (grows left)
    p1_gfx = canvas.create_image(state["p1_pos"], 350, image=assets["blue_idle"], anchor="sw")
    p2_gfx = canvas.create_image(state["p2_pos"], 350, image=assets["pink_idle"], anchor="se")

    def check_inputs():
        if not state["active"]: return
        pygame.event.pump()

        # Stamina Regen
        state["p1_stam"] = min(100.0, state["p1_stam"] + 0.6)
        state["p2_stam"] = min(100.0, state["p2_stam"] + 0.6)

        # Player 1 Logic
        if len(joysticks) > 0:
            joy = joysticks[0]
            move_x = joy.get_axis(AXIS_X)
            if abs(move_x) > 0.1:
                state["p1_pos"] = max(20, min(state["p2_pos"] - 50, state["p1_pos"] + move_x * 7))

            state["p1_blocking"] = joy.get_button(BUTTON_B) and state["p1_stam"] > 10
            if state["p1_blocking"]: state["p1_stam"] -= 1.2

            curr_x = joy.get_button(BUTTON_X)
            if curr_x and not state["prev_x1"] and not state["p1_blocking"] and state["p1_stam"] >= 30:
                state["p1_stam"] -= 30
                state["p1_lunge_timer"] = 12
            state["prev_x1"] = curr_x

        # Player 2 Logic
        if len(joysticks) > 1:
            joy = joysticks[1]
            move_x = joy.get_axis(AXIS_X)
            if abs(move_x) > 0.1:
                state["p2_pos"] = min(780, max(state["p1_pos"] + 50, state["p2_pos"] + move_x * 7))

            state["p2_blocking"] = joy.get_button(BUTTON_B) and state["p2_stam"] > 10
            if state["p2_blocking"]: state["p2_stam"] -= 1.2

            curr_x = joy.get_button(BUTTON_X)
            if curr_x and not state["prev_x2"] and not state["p2_blocking"] and state["p2_stam"] >= 30:
                state["p2_stam"] -= 30
                state["p2_lunge_timer"] = 12
            state["prev_x2"] = curr_x

        if state["p1_lunge_timer"] > 0: state["p1_lunge_timer"] -= 1
        if state["p2_lunge_timer"] > 0: state["p2_lunge_timer"] -= 1

        update_visuals_and_collisions()
        parent_frame.after(16, check_inputs)

    def update_visuals_and_collisions():
        if not state["active"]: return

        # Select Sprites based on state
        p1_img = assets["blue_idle"]
        if state["p1_lunge_timer"] > 0:
            p1_img = assets["blue_lunge"]
        elif state["p1_blocking"]:
            p1_img = assets["blue_block"]

        p2_img = assets["pink_idle"]
        if state["p2_lunge_timer"] > 0:
            p2_img = assets["pink_lunge"]
        elif state["p2_blocking"]:
            p2_img = assets["pink_block"]

        # Update Visuals
        canvas.itemconfig(p1_gfx, image=p1_img)
        canvas.coords(p1_gfx, state["p1_pos"], 350)

        canvas.itemconfig(p2_gfx, image=p2_img)
        canvas.coords(p2_gfx, state["p2_pos"], 350)

        # Hit Detection based on current reach
        s1_tip = state["p1_pos"] + (state["lunge_reach"] if state["p1_lunge_timer"] > 0 else state["base_reach"])
        s2_tip = state["p2_pos"] - (state["lunge_reach"] if state["p2_lunge_timer"] > 0 else state["base_reach"])

        # P1 Attacks P2
        if state["p1_lunge_timer"] > 0 and s1_tip >= state["p2_pos"] - 20:
            if state["p2_blocking"]:
                state["p1_stam"] = max(0, state["p1_stam"] - 40)
                state["p1_lunge_timer"] = 0
            else:
                animate_death("P2", "BLUE TEAM")

        # P2 Attacks P1
        if state["p2_lunge_timer"] > 0 and s2_tip <= state["p1_pos"] + 20:
            if state["p1_blocking"]:
                state["p2_stam"] = max(0, state["p2_stam"] - 40)
                state["p2_lunge_timer"] = 0
            else:
                animate_death("P1", "PINK TEAM")

        # Update Stamina Bars
        canvas.coords(s_bar_a, 50, 20, 50 + (state["p1_stam"] * 2.5), 40)
        canvas.coords(s_bar_b, 500, 20, 500 + (state["p2_stam"] * 2.5), 40)

    def animate_death(loser_id, winner_name):
        state["active"] = False
        if loser_id == "P1":
            canvas.itemconfig(p1_gfx, image=assets["dead"], anchor="center")
            canvas.move(p1_gfx, 0, 30)
        else:
            canvas.itemconfig(p2_gfx, image=assets["dead"], anchor="center")
            canvas.move(p2_gfx, 0, 30)

        parent_frame.after(1500, lambda: end_game(winner_name))

    def end_game(winner):
        for widget in parent_frame.winfo_children(): widget.destroy()
        on_game_over(winner)

    check_inputs()