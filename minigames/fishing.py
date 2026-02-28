import tkinter as tk
import pygame
import random

# Mapping for Xbox Controllers
BUTTON_A = 0
AXIS_LEFT_STICK_Y = 1


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    P1_COLOR = "#0074D9"  # Blue
    P2_COLOR = "#F012BE"  # Pink
    BG_COLOR = "#001f3f"  # Deep Sea Blue
    ZONE_COLOR = "#2ECC40"

    canvas = tk.Canvas(parent_frame, width=800, height=500, bg=BG_COLOR, highlightthickness=0)
    canvas.pack(pady=20)

    # State: [x, y, speed, direction]
    state = {
        "active": True,
        "phase": ["fishing", "fishing"],
        "p_pos": [250, 250],
        "p_target": [250, 250],
        "p_target_vel": [2, -2],
        "p_progress": [0.0, 0.0],
        "win_goal": 3.0,
        "fish_list": [
            [[random.randint(0, 350), random.randint(150, 450), random.randint(2, 4), 1] for _ in range(3)],
            [[random.randint(450, 800), random.randint(150, 450), random.randint(2, 4), -1] for _ in range(3)]
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
                canvas.create_line(x_center, 0, x_center, hook_y, fill="white", width=1)
                canvas.create_arc(x_center - 5, hook_y, x_center + 5, hook_y + 15, start=180, extent=180, style="arc",
                                  outline="silver", width=3)

                for fish in state["fish_list"][i]:
                    fish[0] += fish[2] * fish[3]  # Move X

                    # WRAP AROUND WITH RANDOM HEIGHT RESET
                    if i == 0 and fish[0] > 380:  # P1 wrap
                        fish[0] = random.randint(-50, 0)
                        fish[1] = random.randint(150, 450)  # New Height
                    if i == 1 and fish[0] < 420:  # P2 wrap
                        fish[0] = random.randint(800, 850)
                        fish[1] = random.randint(150, 450)  # New Height

                    f_x, f_y = fish[0], fish[1]
                    canvas.create_oval(f_x - 15, f_y - 8, f_x + 15, f_y + 8, fill="#7FDBFF")
                    eye_x = f_x + (10 * fish[3])
                    canvas.create_oval(eye_x - 2, f_y - 3, eye_x + 2, f_y + 1, fill="black")

                    # Collision (Mouth to Hook)
                    if abs(f_y - hook_y) < 18 and abs(f_x - x_center) < 15:
                        state["phase"][i] = "reeling"

            else:
                # REELING PHASE
                canvas.create_text(x_center, 50, text="STEADY...", fill="white", font=("Arial", 16, "bold"))
                canvas.create_rectangle(x_center - 25, 120, x_center + 25, 380, outline="white", width=2)

                z_y = state["p_target"][i]
                canvas.create_rectangle(x_center - 23, z_y - 25, x_center + 23, z_y + 25, fill=ZONE_COLOR)

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
                state["p_pos"][i] += axis_val * 7

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
            end_game("Player 1 (Blue)")
        elif state["p_progress"][1] >= state["win_goal"]:
            end_game("Player 2 (Pink)")
        else:
            parent_frame.after(16, check_inputs)

    def end_game(winner):
        state["active"] = False
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    check_inputs()