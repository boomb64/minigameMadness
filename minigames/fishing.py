import tkinter as tk
import pygame
import random
import os

# Mapping for Xbox Controllers (Standard)
BUTTON_A = 0
AXIS_LEFT_STICK_Y = 1  # Vertical movement


def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # Colors as requested
    P1_COLOR = "#0074D9"  # Blue
    P2_COLOR = "#F012BE"  # Pink
    BG_COLOR = "#001f3f"  # Deep Sea Blue
    ZONE_COLOR = "#2ECC40"  # Green sweet spot

    # Setup Canvas for visuals
    canvas = tk.Canvas(parent_frame, width=800, height=500, bg=BG_COLOR, highlightthickness=0)
    canvas.pack(pady=20)

    # --- ASSET LOADING ---
    asset_path = os.path.join("minigames", "assets")

    # We store images in a dict attached to the frame to prevent garbage collection
    try:
        parent_frame.fishing_assets = {
            "hook_p1": tk.PhotoImage(file=os.path.join(asset_path, "blue_hook.png")),
            "hook_p2": tk.PhotoImage(file=os.path.join(asset_path, "pink_hook.png")),
            # Use subsample(2, 2) to shrink the fish to 50% size. Adjust numbers if still too big.
            "fish_variants": [
                tk.PhotoImage(file=os.path.join(asset_path, "cyan_fish.png")).subsample(2, 2),
                tk.PhotoImage(file=os.path.join(asset_path, "green_fish.png")).subsample(2, 2),
                tk.PhotoImage(file=os.path.join(asset_path, "orange_fish.png")).subsample(2, 2),
                tk.PhotoImage(file=os.path.join(asset_path, "purple_fish.png")).subsample(2, 2)
            ]
        }
        assets = parent_frame.fishing_assets
    except Exception as e:
        print(f"CRITICAL ERROR LOADING ASSETS: {e}")
        print(f"Ensure PNG files exist in: {os.path.abspath(asset_path)}")
        on_game_over("Asset Error")
        return

    # Game State
    # fish entry: [x, y, speed, direction, image_index]
    state = {
        "active": True,
        "phase": ["fishing", "fishing"],  # Phases: 'fishing' or 'reeling'
        "p_pos": [250, 250],  # Vertical position of hooks
        "p_target": [250, 250],  # Reeling green zones
        "p_target_vel": [2, -2],  # Random drifting velocity for zones
        "p_progress": [0.0, 0.0],  # Progress toward win_goal
        "win_goal": 3.0,  # Seconds required in zone
        "prev_a": [False, False],
        # Generate initial fish with random color variants
        "fish_list": [
            [[random.randint(0, 350), random.randint(150, 450), random.randint(2, 4), 1, random.randint(0, 3)] for _ in
             range(3)],  # P1 Fish
            [[random.randint(450, 800), random.randint(150, 450), random.randint(2, 4), -1, random.randint(0, 3)] for _
             in range(3)]  # P2 Fish
        ]
    }

    def update_visuals():
        canvas.delete("all")

        # Draw Center Divider
        canvas.create_line(400, 0, 400, 500, fill="#333333", width=2)

        for i in range(2):
            x_center = 200 if i == 0 else 600
            color = P1_COLOR if i == 0 else P2_COLOR

            if state["phase"][i] == "fishing":
                # --- PHASE 1: HUNTING ---
                hook_y = state["p_pos"][i]

                # REQ: Get rid of the code-generated line.
                # canvas.create_line(x_center, 0, x_center, hook_y, fill="white", width=1)

                # DRAW HOOK SPRITE
                # REQ: Hook image has a line included, so move image up.
                # We do this by anchoring "s" (South/Bottom) at hook_y.
                # The image's hook is at the bottom, and its line extends up automatically.
                hook_img = assets["hook_p1"] if i == 0 else assets["hook_p2"]
                canvas.create_image(x_center, hook_y, image=hook_img, anchor="s")

                # DRAW AND MOVE FISH
                for fish in state["fish_list"][i]:
                    fish[0] += fish[2] * fish[3]  # Move X based on speed * direction

                    # Wrap around logic with random height and color reset
                    if i == 0 and fish[0] > 380:  # P1 right boundary
                        fish[0] = random.randint(-50, 0)
                        fish[1] = random.randint(150, 450)  # New Height
                        fish[4] = random.randint(0, 3)  # New random color variant
                    if i == 1 and fish[0] < 420:  # P2 left boundary
                        fish[0] = random.randint(800, 850)
                        fish[1] = random.randint(150, 450)  # New Height
                        fish[4] = random.randint(0, 3)  # New random color variant

                    f_x, f_y = fish[0], fish[1]

                    # DRAW FISH SPRITE
                    # Since images are WAAAY too big, we are using the pre-shrunk assets.
                    fish_img = assets["fish_variants"][fish[4]]
                    canvas.create_image(f_x, f_y, image=fish_img)

                    # COLLISION DETECTION (Touch mouth to hook)
                    # Tightened collision window slightly since fish are smaller.
                    if abs(f_y - hook_y) < 15 and abs(f_x - x_center) < 15:
                        state["phase"][i] = "reeling"

            else:
                # --- PHASE 2: REELING (The Meter) ---
                canvas.create_text(x_center, 50, text="STEADY...", fill="white", font=("Arial", 16, "bold"))

                # Draw Meter Background
                canvas.create_rectangle(x_center - 25, 120, x_center + 25, 380, outline="white", width=2)

                # Draw Moving "Sweet Spot" Zone
                z_y = state["p_target"][i]
                canvas.create_rectangle(x_center - 23, z_y - 25, x_center + 23, z_y + 25, fill=ZONE_COLOR)

                # Draw Player Tension Dot
                dot_y = state["p_pos"][i]
                canvas.create_oval(x_center - 10, dot_y - 10, x_center + 10, dot_y + 10, fill=color, outline="white")

                # Draw Progress Bar
                prog_w = (state["p_progress"][i] / state["win_goal"]) * 160
                canvas.create_rectangle(x_center - 80, 420, x_center + 80, 435, outline="white")
                canvas.create_rectangle(x_center - 80, 420, x_center - 80 + prog_w, 435, fill=ZONE_COLOR)

    def check_inputs():
        if not state["active"]: return

        # A. Refresh internal Pygame state
        pygame.event.pump()

        # B. Process Inputs for available joysticks
        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]

            # 1. Handle Hook Movement (Vertical Axis)
            axis_val = joy.get_axis(AXIS_LEFT_STICK_Y)
            if abs(axis_val) > 0.1:  # Deadzone
                state["p_pos"][i] += axis_val * 7  # Movement speed

            # Keep hooks within screen bounds
            state["p_pos"][i] = max(130, min(370, state["p_pos"][i]))

            # 2. Handle Reeling Logic (Phase 2 only)
            if state["phase"][i] == "reeling":
                # Move the Green Zone based on its velocity
                state["p_target"][i] += state["p_target_vel"][i]

                # Bounce zone off top/bottom of meter
                if state["p_target"][i] < 155 or state["p_target"][i] > 345:
                    state["p_target_vel"][i] *= -1

                # Occasionally introduce randomness to zone movement (2% chance per frame)
                if random.random() < 0.02:
                    state["p_target_vel"][i] = random.choice([-4, -3, 3, 4])

                # Check if player dot is within the "Sweet Spot" (±25 pixels)
                if abs(state["p_pos"][i] - state["p_target"][i]) < 25:
                    # Increment progress (approx 16ms passed)
                    state["p_progress"][i] += 0.016
                else:
                    # Slow penalty: Progress slowly slips away if you're out of the zone
                    state["p_progress"][i] = max(0, state["p_progress"][i] - 0.002)

        update_visuals()

        # C. Check for Winner (Returns standardized "Team A" or "Team B")
        if state["p_progress"][0] >= state["win_goal"]:
            end_game("Team A")
        elif state["p_progress"][1] >= state["win_goal"]:
            end_game("Team B")
        else:
            # Re-run this check every 16ms (~60 FPS polling)
            parent_frame.after(16, check_inputs)

    def end_game(winner):
        state["active"] = False
        # Clean up widgets
        for widget in parent_frame.winfo_children():
            widget.destroy()
        # Signal handler back to main runner
        on_game_over(winner)

    # Start the input polling loop
    check_inputs()