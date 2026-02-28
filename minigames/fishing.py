import tkinter as tk
import pygame
import random
import os

# Mapping for Xbox Controllers
BUTTON_A = 0
AXIS_LEFT_STICK_Y = 1


def flip_image(img):
    """Manually mirrors a PhotoImage across the Y-axis."""
    flipped = tk.PhotoImage(width=img.width(), height=img.height())
    for x in range(img.width()):
        # Copy column x to column width-x-1
        flipped.tk.call(flipped, 'copy', img, '-from', x, 0, x + 1, img.height(), '-to', img.width() - x - 1, 0)
    return flipped


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # Colors
    P1_COLOR = "#0074D9"  # Blue
    P2_COLOR = "#F012BE"  # Pink
    BG_COLOR = "#001f3f"  # Deep Sea Blue
    ZONE_COLOR = "#2ECC40"

    canvas = tk.Canvas(parent_frame, width=800, height=500, bg=BG_COLOR, highlightthickness=0)
    canvas.pack(pady=20)

    # --- ASSET LOADING ---
    asset_path = os.path.join("minigames", "assets")

    try:
        # Load and shrink base variants
        cyan = tk.PhotoImage(file=os.path.join(asset_path, "cyan_fish.png")).subsample(4, 4)
        green = tk.PhotoImage(file=os.path.join(asset_path, "green_fish.png")).subsample(4, 4)
        orange = tk.PhotoImage(file=os.path.join(asset_path, "orange_fish.png")).subsample(4, 4)
        purple = tk.PhotoImage(file=os.path.join(asset_path, "purple_fish.png")).subsample(4, 4)

        # Create flipped versions
        cyan_f, green_f, orange_f, purple_f = flip_image(cyan), flip_image(green), flip_image(orange), flip_image(
            purple)

        parent_frame.fishing_assets = {
            "hook_p1": tk.PhotoImage(file=os.path.join(asset_path, "blue_hook.png")).subsample(3, 3),
            "hook_p2": tk.PhotoImage(file=os.path.join(asset_path, "pink_hook.png")).subsample(3, 3),
            # Side-specific logic: [Cyan, Green, Orange, Purple]
            # Side 0 (Left): C, G, P normal, Orange Mirrored
            "p1_fish": [cyan, green, orange_f, purple],
            # Side 1 (Right): Orange normal, C, G, P Mirrored
            "p2_fish": [cyan_f, green_f, orange, purple_f]
        }
        assets = parent_frame.fishing_assets
        SPRITE_H = assets["hook_p1"].height()
    except Exception as e:
        print(f"ASSET ERROR: {e}")
        on_game_over("Asset Error")
        return

    # Game State
    state = {
        "active": True,
        "phase": ["fishing", "fishing"],
        "p_pos": [150, 150],
        "p_target": [250, 250],
        "p_target_vel": [2, -2],
        "p_progress": [0.0, 0.0],
        "win_goal": 3.0,
        "fish_list": [
            [[random.randint(0, 350), random.randint(150, 450), random.randint(2, 4), 1, random.randint(0, 3)] for _ in
             range(3)],
            [[random.randint(450, 800), random.randint(150, 450), random.randint(2, 4), -1, random.randint(0, 3)] for _
             in range(3)]
        ]
    }

    def update_visuals():
        canvas.delete("all")
        canvas.create_line(400, 0, 400, 500, fill="#333333", width=2)

        for i in range(2):
            x_center = 200 if i == 0 else 600
            color = P1_COLOR if i == 0 else P2_COLOR

            if state["phase"][i] == "fishing":
                hook_y = state["p_pos"][i]
                if (hook_y - SPRITE_H) > 0:
                    canvas.create_line(x_center, 0, x_center, hook_y - SPRITE_H, fill="white", width=1)

                hook_img = assets["hook_p1"] if i == 0 else assets["hook_p2"]
                canvas.create_image(x_center, hook_y, image=hook_img, anchor="s")

                for fish in state["fish_list"][i]:
                    fish[0] += fish[2] * fish[3]

                    if i == 0 and fish[0] > 380:
                        fish[0], fish[1], fish[4] = random.randint(-50, 0), random.randint(150, 450), random.randint(0,
                                                                                                                     3)
                    if i == 1 and fish[0] < 420:
                        fish[0], fish[1], fish[4] = random.randint(800, 850), random.randint(150, 450), random.randint(
                            0, 3)

                    # Select side-appropriate image
                    side_key = "p1_fish" if i == 0 else "p2_fish"
                    fish_img = assets[side_key][fish[4]]
                    canvas.create_image(fish[0], fish[1], image=fish_img)

                    # NOSE HITBOX: Higher hitbox on hook, center-front of fish
                    hitbox_y = hook_y - 15
                    nose_x = fish[0] + (15 * fish[3])
                    if abs(fish[1] - hitbox_y) < 18 and abs(nose_x - x_center) < 15:
                        state["phase"][i] = "reeling"

            else:
                # REELING PHASE
                canvas.create_text(x_center, 50, text="STEADY...", fill="white", font=("Arial", 16, "bold"))
                canvas.create_rectangle(x_center - 25, 120, x_center + 25, 380, outline="white", width=2)
                z_y = state["p_target"][i]
                canvas.create_rectangle(x_center - 23, z_y - 25, x_center + 23, z_y + 25, fill=ZONE_COLOR)

                # Player Tension Dot (Clamped inside visuals)
                dot_y = state["p_pos"][i]
                canvas.create_oval(x_center - 10, dot_y - 10, x_center + 10, dot_y + 10, fill=color, outline="white")

                prog_w = (state["p_progress"][i] / state["win_goal"]) * 160
                canvas.create_rectangle(x_center - 80, 420, x_center + 80, 435, outline="white")
                canvas.create_rectangle(x_center - 80, 420, x_center - 80 + prog_w, 435, fill=ZONE_COLOR)

    def check_inputs():
        if not state["active"]: return
        pygame.event.pump()
        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]
            axis_val = joy.get_axis(AXIS_LEFT_STICK_Y)
            if abs(axis_val) > 0.1:
                state["p_pos"][i] += axis_val * 8

            # --- DYNAMIC CLAMPING ---
            # Keeps the hook/dot from escaping its context
            if state["phase"][i] == "fishing":
                state["p_pos"][i] = max(50, min(480, state["p_pos"][i]))
            else:
                # Reeling bar is 120 to 380. We clamp dot to stay inside.
                state["p_pos"][i] = max(130, min(370, state["p_pos"][i]))

            if state["phase"][i] == "reeling":
                state["p_target"][i] += state["p_target_vel"][i]
                if state["p_target"][i] < 155 or state["p_target"][i] > 345:
                    state["p_target_vel"][i] *= -1
                if random.random() < 0.02:
                    state["p_target_vel"][i] = random.choice([-4, -3, 3, 4])

                if abs(state["p_pos"][i] - state["p_target"][i]) < 25:
                    state["p_progress"][i] += 0.016
                else:
                    state["p_progress"][i] = max(0, state["p_progress"][i] - 0.002)

        update_visuals()
        if state["p_progress"][0] >= state["win_goal"]:
            end_game("Team A")
        elif state["p_progress"][1] >= state["win_goal"]:
            end_game("Team B")
        else:
            parent_frame.after(16, check_inputs)

    def end_game(winner):
        state["active"] = False
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    check_inputs()