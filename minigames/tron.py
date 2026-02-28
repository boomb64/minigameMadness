import tkinter as tk
import pygame
import time

# Mapping for Xbox Controllers
AXIS_LX = 0
AXIS_LY = 1


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # Style
    P1_COLOR, P2_COLOR, BG_COLOR = "#0074D9", "#F012BE", "#050505"
    GRID_SIZE = 8

    canvas = tk.Canvas(parent_frame, width=800, height=600, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    state = {
        "active": True,
        "timer": 10.0,
        "last_time": time.time(),
        # Body format: [(head_x, head_y), (tail_x, tail_y)]
        "p1_body": [(152, 304), (144, 304)],
        "p1_vel": [GRID_SIZE, 0],

        "p2_body": [(648, 304), (656, 304)],
        "p2_vel": [-GRID_SIZE, 0],

        "trail_p1": set(),
        "trail_p2": set(),
        "game_ending": False
    }

    def update_visuals():
        canvas.delete("all")

        # --- ARENA BORDER ---
        canvas.create_rectangle(0, 0, 800, 600, outline="white", width=4)

        # Draw Trails
        for tx, ty in state["trail_p1"]:
            canvas.create_rectangle(tx, ty, tx + GRID_SIZE, ty + GRID_SIZE, fill="#001f3f", outline=P1_COLOR)
        for tx, ty in state["trail_p2"]:
            canvas.create_rectangle(tx, ty, tx + GRID_SIZE, ty + GRID_SIZE, fill="#2b0022", outline=P2_COLOR)

        # Draw 2-Segment Bikes (White heads, colored outlines)
        for i in range(2):
            body = state["p1_body"] if i == 0 else state["p2_body"]
            color = P1_COLOR if i == 0 else P2_COLOR
            for segment in body:
                canvas.create_rectangle(segment[0], segment[1], segment[0] + GRID_SIZE, segment[1] + GRID_SIZE,
                                        fill="white", outline=color)

        # Header UI
        canvas.create_rectangle(300, 10, 500, 60, fill="black", outline="#39FF14", width=2)
        t_color = "white" if state["timer"] > 2.0 else "#FF4136"
        canvas.create_text(400, 35, text=f"{state['timer']:.1f}s", fill=t_color, font=("Impact", 24))

    def check_inputs():
        if not state["active"]: return

        now = time.time()
        delta = now - state["last_time"]
        state["last_time"] = now

        state["timer"] -= delta
        if state["timer"] <= 0:
            end_game("Tie")
            return

        pygame.event.pump()
        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]
            lx, ly = joy.get_axis(AXIS_LX), joy.get_axis(AXIS_LY)
            v_key = "p1_vel" if i == 0 else "p2_vel"

            # Steering only from the front pixel (affects the NEXT move)
            if abs(lx) > 0.5:
                new_vx = GRID_SIZE if lx > 0 else -GRID_SIZE
                if new_vx != -state[v_key][0]:  # No 180s
                    state[v_key] = [new_vx, 0]
            elif abs(ly) > 0.5:
                new_vy = GRID_SIZE if ly > 0 else -GRID_SIZE
                if new_vy != -state[v_key][1]:  # No 180s
                    state[v_key] = [0, new_vy]

        # --- MOVEMENT LOGIC ---
        for i in range(2):
            p_body = "p1_body" if i == 0 else "p2_body"
            p_trail = "trail_p1" if i == 0 else "trail_p2"
            p_vel = "p1_vel" if i == 0 else "p2_vel"

            # 1. Old tail becomes trail
            old_tail = state[p_body].pop()  # Remove the last segment
            state[p_trail].add(old_tail)

            # 2. New head based on velocity
            current_head = state[p_body][0]
            new_head = (current_head[0] + state[p_vel][0], current_head[1] + state[p_vel][1])

            # 3. Update body (New head at index 0, old head becomes tail at index 1)
            state[p_body].insert(0, new_head)

        # --- COLLISION ---
        p1_hit, p2_hit = False, False
        head1, head2 = state["p1_body"][0], state["p2_body"][0]
        tail1, tail2 = state["p1_body"][1], state["p2_body"][1]

        # Wall Check
        if not (4 <= head1[0] < 792 and 4 <= head1[1] < 592): p1_hit = True
        if not (4 <= head2[0] < 792 and 4 <= head2[1] < 592): p2_hit = True

        # Trail Check (Hit self or opponent)
        if head1 in state["trail_p1"] or head1 in state["trail_p2"]: p1_hit = True
        if head2 in state["trail_p1"] or head2 in state["trail_p2"]: p2_hit = True

        # Bike Body Check (Hitting the opponent's tail segment)
        if head1 == head2 or head1 == tail2: p1_hit = True
        if head2 == head1 or head2 == tail1: p2_hit = True

        # Resolve
        if p1_hit and p2_hit:
            end_game("Tie")
        elif p1_hit:
            end_game("Team B")
        elif p2_hit:
            end_game("Team A")
        else:
            update_visuals()
            parent_frame.after(25, check_inputs)

    def end_game(winner):
        if state["game_ending"]: return
        state["game_ending"] = True
        state["active"] = False
        on_game_over(winner)

    check_inputs()