import tkinter as tk
import pygame
import random
import time

# Xbox Button Mappings
BTN_A = 0
BTN_B = 1
BTN_X = 2
BTN_Y = 3

# Colors: (Dim Color, Lit Color)
COLORS = {
    BTN_A: ("#004400", "#00FF00"),
    BTN_B: ("#440000", "#FF0000"),
    BTN_X: ("#000044", "#0088FF"),
    BTN_Y: ("#444400", "#FFFF00")
}


def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # 2. Game State
    state = {
        "active": True,
        "round": 1,
        "max_rounds": 3,
        "sequence": [],
        "phase": "WATCH",
        "a_idx": 0,
        "b_idx": 0,
        "round_start_time": 0.0,
        "time_limit": 4.0,  # 4 Seconds to input the sequence
        "prev_a": {BTN_A: False, BTN_B: False, BTN_X: False, BTN_Y: False},
        "prev_b": {BTN_A: False, BTN_B: False, BTN_X: False, BTN_Y: False}
    }

    state["sequence"] = [random.choice([BTN_A, BTN_B, BTN_X, BTN_Y]) for _ in range(4)]

    # 3. Setup GUI
    header = tk.Label(parent_frame, text="ROUND 1: WATCH THE CENTER", font=("Arial", 24, "bold"), fg="white",
                      bg="black")
    header.pack(pady=10)

    # The new Timer Label
    timer_label = tk.Label(parent_frame, text="", font=("Courier", 28, "bold"), fg="yellow", bg="black")
    timer_label.pack(pady=5)

    arena_frame = tk.Frame(parent_frame, bg="black")
    arena_frame.pack(expand=True, fill="both")

    col_a = tk.Frame(arena_frame, bg="black")
    col_a.pack(side="left", expand=True, fill="both")

    col_center = tk.Frame(arena_frame, bg="black", highlightbackground="white", highlightthickness=2)
    col_center.pack(side="left", expand=True, fill="both", padx=20)

    col_b = tk.Frame(arena_frame, bg="black")
    col_b.pack(side="left", expand=True, fill="both")

    tk.Label(col_a, text="TEAM A", font=("Arial", 18), fg="cyan", bg="black").pack(pady=10)
    tk.Label(col_center, text="PATTERN", font=("Arial", 18), fg="white", bg="black").pack(pady=10)
    tk.Label(col_b, text="TEAM B", font=("Arial", 18), fg="magenta", bg="black").pack(pady=10)

    def draw_diamond(parent_col):
        canvas = tk.Canvas(parent_col, width=200, height=200, bg="black", highlightthickness=0)
        canvas.pack(expand=True)

        rad = 30
        cx, cy = 100, 100
        offset = 55

        a = canvas.create_oval(cx - rad, cy + offset - rad, cx + rad, cy + offset + rad, fill=COLORS[BTN_A][0])
        b = canvas.create_oval(cx + offset - rad, cy - rad, cx + offset + rad, cy + rad, fill=COLORS[BTN_B][0])
        x = canvas.create_oval(cx - offset - rad, cy - rad, cx - offset + rad, cy + rad, fill=COLORS[BTN_X][0])
        y = canvas.create_oval(cx - rad, cy - offset - rad, cx + rad, cy - offset + rad, fill=COLORS[BTN_Y][0])

        return canvas, {BTN_A: a, BTN_B: b, BTN_X: x, BTN_Y: y}

    canv_a, objs_a = draw_diamond(col_a)
    canv_center, objs_center = draw_diamond(col_center)
    canv_b, objs_b = draw_diamond(col_b)

    # 4. Logic Functions
    def flash_button(canvas, objs, button, duration=250):
        if not state["active"]: return
        obj_id = objs[button]
        canvas.itemconfig(obj_id, fill=COLORS[button][1])
        parent_frame.after(duration, lambda: reset_button(canvas, obj_id, button))

    def reset_button(canvas, obj_id, button):
        if not state["active"]: return
        canvas.itemconfig(obj_id, fill=COLORS[button][0])

    def play_pattern(index=0):
        if not state["active"]: return
        if index < len(state["sequence"]):
            btn = state["sequence"][index]
            flash_button(canv_center, objs_center, btn, duration=400)
            parent_frame.after(600, lambda: play_pattern(index + 1))
        else:
            state["phase"] = "PLAY"
            state["round_start_time"] = time.time()  # Start the timer!
            header.config(text="YOUR TURN! REPEAT THE PATTERN", fg="yellow")
            state["a_idx"] = 0
            state["b_idx"] = 0

    def start_round():
        state["phase"] = "WATCH"
        timer_label.config(text="")  # Hide timer during watch phase
        header.config(text=f"ROUND {state['round']}: WATCH THE CENTER", fg="white")
        parent_frame.after(1000, lambda: play_pattern(0))

    def check_inputs():
        if not state["active"]: return

        if state["phase"] == "PLAY":

            # --- TIMER LOGIC ---
            time_left = state["time_limit"] - (time.time() - state["round_start_time"])

            if time_left <= 0:
                timer_label.config(text="TIME: 0.0s", fg="red")

                # Time's up! Check who actually finished.
                a_done = (state["a_idx"] == len(state["sequence"]))
                b_done = (state["b_idx"] == len(state["sequence"]))

                if a_done and not b_done:
                    end_game("Team A")
                elif b_done and not a_done:
                    end_game("Team B")
                else:
                    end_game("Tie")  # Neither finished (or both didn't finish, so it's a tie)
                return
            else:
                timer_label.config(text=f"TIME: {time_left:.1f}s", fg="yellow")

            # --- INPUT LOGIC ---
            pygame.event.pump()
            buttons_to_check = [BTN_A, BTN_B, BTN_X, BTN_Y]

            # TEAM A
            if len(joysticks) > 0:
                joy_a = joysticks[0]
                for btn in buttons_to_check:
                    current_pressed = joy_a.get_button(btn)

                    if current_pressed and not state["prev_a"][btn]:
                        if state["a_idx"] < len(state["sequence"]):
                            expected = state["sequence"][state["a_idx"]]
                            if btn == expected:
                                flash_button(canv_a, objs_a, btn)
                                state["a_idx"] += 1
                            else:
                                end_game("Team B")  # Team A messed up instantly
                                return
                    state["prev_a"][btn] = current_pressed

            # TEAM B
            if len(joysticks) > 1:
                joy_b = joysticks[1]
                for btn in buttons_to_check:
                    current_pressed = joy_b.get_button(btn)

                    if current_pressed and not state["prev_b"][btn]:
                        if state["b_idx"] < len(state["sequence"]):
                            expected = state["sequence"][state["b_idx"]]
                            if btn == expected:
                                flash_button(canv_b, objs_b, btn)
                                state["b_idx"] += 1
                            else:
                                end_game("Team A")  # Team B messed up instantly
                                return
                    state["prev_b"][btn] = current_pressed

            # Check if both teams completed the sequence correctly BEFORE time ran out
            if state["a_idx"] == len(state["sequence"]) and state["b_idx"] == len(state["sequence"]):
                state["phase"] = "WATCH"
                state["round"] += 1

                if state["round"] > state["max_rounds"]:
                    end_game("Tie")  # Survived 3 rounds
                    return
                else:
                    timer_label.config(text="SUCCESS!", fg="green")
                    header.config(text="CORRECT! PREPARING NEXT ROUND...", fg="green")
                    state["sequence"].append(random.choice([BTN_A, BTN_B, BTN_X, BTN_Y]))
                    parent_frame.after(1500, start_round)

        parent_frame.after(16, check_inputs)

    def end_game(winner):
        state["active"] = False
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    parent_frame.after(500, start_round)
    check_inputs()