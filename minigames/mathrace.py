import tkinter as tk
import pygame
import random
import math

# Mapping for Xbox Controllers
BUTTON_A = 0
BUTTON_B = 1  # Added B button for backspace
AXIS_LX = 0
AXIS_LY = 1


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # Colors
    P1_COLOR = "#0074D9"  # Blue
    P2_COLOR = "#F012BE"  # Pink
    BG_COLOR = "#111111"

    canvas = tk.Canvas(parent_frame, width=800, height=600, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    # Grid Setup
    keys = [
        ["1", "2", "3"],
        ["4", "5", "6"],
        ["7", "8", "9"],
        ["BACK", "0", "SUBMIT"]
    ]

    def generate_problem():
        op = random.choice(['+', '-', '*', '/'])
        if op == '+':
            a, b = random.randint(1, 20), random.randint(1, 20)
            ans = a + b
        elif op == '-':
            a = random.randint(10, 30)
            b = random.randint(1, a)
            ans = a - b
        elif op == '*':
            a, b = random.randint(2, 9), random.randint(2, 9)
            ans = a * b
        else:  # Division (Ensures whole numbers)
            b = random.randint(2, 6)
            ans = random.randint(2, 8)
            a = ans * b
        return f"{a} {op.replace('*', 'x').replace('/', '÷')} {b}", str(ans)

    problem_text, correct_answer = generate_problem()

    state = {
        "active": True,
        "timer": 5.0,
        "p_input": ["", ""],
        "p_cursor": [[0, 0], [0, 0]],
        "p_cooldown": [0, 0],
        "prev_a": [False, False],
        "prev_b": [False, False]  # Added state for B button edge detection
    }

    def update_visuals():
        canvas.delete("all")

        # Header
        canvas.create_text(400, 50, text=problem_text, fill="white", font=("Courier", 48, "bold"))

        # Timer
        t_color = "white" if state["timer"] > 1.5 else "#FF4136"
        canvas.create_text(400, 110, text=f"{state['timer']:.1f}s", fill=t_color, font=("Impact", 30))

        # Controls Hint
        canvas.create_text(400, 560, text="A: SELECT | B: BACKSPACE", fill="gray", font=("Arial", 10))

        for p_idx in range(2):
            x_offset = 200 if p_idx == 0 else 600
            p_color = P1_COLOR if p_idx == 0 else P2_COLOR

            # Input Area
            canvas.create_rectangle(x_offset - 80, 150, x_offset + 80, 190, outline="white", width=2)
            canvas.create_text(x_offset, 170, text=state["p_input"][p_idx], fill="white", font=("Arial", 22, "bold"))

            # Keypad
            for r in range(4):
                for c in range(3):
                    kx = x_offset - 70 + (c * 70)
                    ky = 260 + (r * 70)

                    is_selected = (state["p_cursor"][p_idx][0] == r and state["p_cursor"][p_idx][1] == c)
                    bg = p_color if is_selected else "#222222"
                    txt_color = "white" if is_selected else "#888888"

                    canvas.create_rectangle(kx - 30, ky - 30, kx + 30, ky + 30, fill=bg, outline="white", width=1)

                    label = keys[r][c]
                    if label == "BACK": label = "←"
                    if label == "SUBMIT": label = "✔"

                    canvas.create_text(kx, ky, text=label, fill=txt_color, font=("Arial", 16, "bold"))

    def check_inputs():
        if not state["active"]: return
        pygame.event.pump()

        state["timer"] -= 0.016
        if state["timer"] <= 0:
            end_game("Tie")
            return

        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]

            # 1. Cursor Navigation
            if state["p_cooldown"][i] > 0:
                state["p_cooldown"][i] -= 1
            else:
                lx, ly = joy.get_axis(AXIS_LX), joy.get_axis(AXIS_LY)
                moved = False
                if ly < -0.5:
                    state["p_cursor"][i][0] = (state["p_cursor"][i][0] - 1) % 4
                    moved = True
                elif ly > 0.5:
                    state["p_cursor"][i][0] = (state["p_cursor"][i][0] + 1) % 4
                    moved = True
                if lx < -0.5:
                    state["p_cursor"][i][1] = (state["p_cursor"][i][1] - 1) % 3
                    moved = True
                elif lx > 0.5:
                    state["p_cursor"][i][1] = (state["p_cursor"][i][1] + 1) % 3
                    moved = True

                if moved:
                    state["p_cooldown"][i] = 10

                    # 2. Select Button (A)
            curr_a = joy.get_button(BUTTON_A)
            if curr_a and not state["prev_a"][i]:
                row, col = state["p_cursor"][i]
                val = keys[row][col]

                if val == "BACK":
                    state["p_input"][i] = state["p_input"][i][:-1]
                elif val == "SUBMIT":
                    if state["p_input"][i] == correct_answer:
                        end_game("Team A" if i == 0 else "Team B")
                    else:
                        end_game("Team B" if i == 0 else "Team A")
                else:
                    if len(state["p_input"][i]) < 4:
                        state["p_input"][i] += val
            state["prev_a"][i] = curr_a

            # 3. Direct Backspace Button (B)
            curr_b = joy.get_button(BUTTON_B)
            if curr_b and not state["prev_b"][i]:
                # Simply remove the last character
                state["p_input"][i] = state["p_input"][i][:-1]
            state["prev_b"][i] = curr_b

        update_visuals()
        parent_frame.after(16, check_inputs)

    def end_game(winner):
        state["active"] = False
        on_game_over(winner)

    check_inputs()