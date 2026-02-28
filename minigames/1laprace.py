import tkinter as tk
import pygame
import random
import math
from PIL import Image, ImageTk
import os

AXIS_X = 0
AXIS_Y = 1


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    WIDTH = 1100
    HEIGHT = 700

    canvas = tk.Canvas(parent_frame, width=WIDTH, height=HEIGHT, bg="darkgreen")
    canvas.pack()

    info_label = tk.Label(parent_frame, text="Complete 1 Lap to Win!", font=("Arial", 16),
                          bg="black", fg="white")
    info_label.pack()

    state = {"active": True}

    ROAD_WIDTH = 140
    GRASS_SLOW = 0.1
    SPEED = 8
    DEADZONE = 0.15

    # ---------------- TRACK ----------------
    margin = 100
    variation = random.randint(100, 180)

    left = margin
    right = WIDTH - margin
    top = margin
    bottom = HEIGHT - margin

    center_points = [
        (left + variation, top),
        (right - variation, top),
        (right, top + variation),
        (right, bottom - variation),
        (right - variation, bottom),
        (left + variation, bottom),
        (left, bottom - variation),
        (left, top + variation),
    ]

    canvas.create_line(
        *sum(center_points + [center_points[0]], ()),
        fill="gray30",
        width=ROAD_WIDTH,
        joinstyle=tk.ROUND
    )

    # ---------------- FINISH LINE ----------------
    x1, y1 = center_points[0]
    x2, y2 = center_points[1]
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    nx = -dy / length
    ny = dx / length
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    half = ROAD_WIDTH / 2

    fx1 = mid_x + nx * half
    fy1 = mid_y + ny * half
    fx2 = mid_x - nx * half
    fy2 = mid_y - ny * half

    segments = 12
    for i in range(segments):
        t1 = i / segments
        t2 = (i + 1) / segments
        sx1 = fx1 + (fx2 - fx1) * t1
        sy1 = fy1 + (fy2 - fy1) * t1
        sx2 = fx1 + (fx2 - fx1) * t2
        sy2 = fy1 + (fy2 - fy1) * t2
        color = "white" if i % 2 == 0 else "black"
        canvas.create_line(sx1, sy1, sx2, sy2, fill=color, width=18)

    FINISH_BOUNDS = (
        min(fx1, fx2) - 10,
        min(fy1, fy2) - 10,
        max(fx1, fx2) + 10,
        max(fy1, fy2) + 10
    )

    finish_vector = (dx / length, dy / length)

    # ---------------- FINISH ARROW ----------------
    arrow_length = 60
    arrow_head_size = 12
    arrow_start_x = mid_x - finish_vector[0] * 40
    arrow_start_y = mid_y - finish_vector[1] * 40
    arrow_end_x = arrow_start_x - finish_vector[0] * arrow_length
    arrow_end_y = arrow_start_y - finish_vector[1] * arrow_length

    canvas.create_line(
        arrow_start_x, arrow_start_y,
        arrow_end_x, arrow_end_y,
        fill="yellow",
        width=6,
        arrow=tk.LAST,
        arrowshape=(arrow_head_size, arrow_head_size, arrow_head_size // 2)
    )

    # ---------------- SPAWN ----------------
    spawn_offset = 80
    spawn_A_x = mid_x - dx / length * spawn_offset + nx * 40
    spawn_A_y = mid_y - dy / length * spawn_offset + ny * 40
    spawn_B_x = mid_x - dx / length * spawn_offset - nx * 40
    spawn_B_y = mid_y - dy / length * spawn_offset - ny * 40

    # ---------------- LOAD CAR IMAGES ----------------
    BASE_DIR = os.path.dirname(__file__)

    def load_car_image(path, target_width=80):
        full_path = os.path.join(BASE_DIR, path)
        try:
            # Convert to RGBA ensures alpha channel for transparency works
            img = Image.open(full_path).convert("RGBA")
            w, h = img.size
            scale = target_width / w
            new_size = (int(w * scale), int(h * scale))
            # Use Image.Resampling.LANCZOS (ANTIALIAS is deprecated)
            return img.resize(new_size, Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            # Return a small placeholder rectangle if file is missing
            return Image.new("RGBA", (target_width, target_width // 2), "red")

    # Store originals on the canvas object to prevent garbage collection
    canvas.orig_A = load_car_image("assets/blue_car.png")
    canvas.orig_B = load_car_image("assets/pink_car.png")

    # Create initial PhotoImages
    canvas.tk_A = ImageTk.PhotoImage(canvas.orig_A)
    canvas.tk_B = ImageTk.PhotoImage(canvas.orig_B)

    car_A = canvas.create_image(spawn_A_x, spawn_A_y, image=canvas.tk_A)
    car_B = canvas.create_image(spawn_B_x, spawn_B_y, image=canvas.tk_B)

    velocity = {"A": [0, 0], "B": [0, 0]}
    crossed_away = {"A": False, "B": False}

    # ---------------- TRACK CHECK ----------------
    def point_near_track(x, y):
        for i in range(len(center_points)):
            x1, y1 = center_points[i]
            x2, y2 = center_points[(i + 1) % len(center_points)]
            px, py = x2 - x1, y2 - y1
            norm = px * px + py * py
            u = ((x - x1) * px + (y - y1) * py) / (norm + 1e-6)
            u = max(0, min(1, u))
            ix, iy = x1 + u * px, y1 + u * py
            if math.hypot(x - ix, y - iy) <= ROAD_WIDTH / 2:
                return True
        return False

    # ---------------- ROTATE CAR IMAGE ----------------
    def rotate_car_image(player, angle):
        angle_deg = -math.degrees(angle)
        if player == "A":
            rotated = canvas.orig_A.rotate(angle_deg, expand=True)
            canvas.tk_A = ImageTk.PhotoImage(rotated)
            return canvas.tk_A
        else:
            rotated = canvas.orig_B.rotate(angle_deg, expand=True)
            canvas.tk_B = ImageTk.PhotoImage(rotated)
            return canvas.tk_B

    # ---------------- MOVE CAR ----------------
    def move_car(car, vel, player):
        coords = canvas.coords(car)
        cx, cy = coords[0], coords[1]

        # Rotate the car image based on velocity direction
        if abs(vel[0]) > 0.2 or abs(vel[1]) > 0.2:
            angle = math.atan2(vel[1], vel[0])
            new_img = rotate_car_image(player, angle)
            canvas.itemconfig(car, image=new_img)

        # Move the car
        speed_mult = 1.0 if point_near_track(cx, cy) else GRASS_SLOW
        canvas.move(car, vel[0] * speed_mult, vel[1] * speed_mult)

        # -------- Finish Detection --------
        if FINISH_BOUNDS[0] <= cx <= FINISH_BOUNDS[2] and FINISH_BOUNDS[1] <= cy <= FINISH_BOUNDS[3]:
            vel_dot = vel[0] * finish_vector[0] + vel[1] * finish_vector[1]
            if vel_dot < -0.5 and crossed_away[player]:
                end_game(f"{'Blue' if player == 'A' else 'Pink'} Wins!")
        else:
            crossed_away[player] = True

    # ---------------- INPUT LOOP ----------------
    def check_inputs():
        if not state["active"]:
            return

        pygame.event.pump()

        # Player A (Joystick 0)
        if len(joysticks) >= 1:
            x = joysticks[0].get_axis(AXIS_X)
            y = joysticks[0].get_axis(AXIS_Y)
            velocity["A"][0] = 0 if abs(x) < DEADZONE else x * SPEED
            velocity["A"][1] = 0 if abs(y) < DEADZONE else y * SPEED

        # Player B (Joystick 1)
        if len(joysticks) >= 2:
            x = joysticks[1].get_axis(AXIS_X)
            y = joysticks[1].get_axis(AXIS_Y)
            velocity["B"][0] = 0 if abs(x) < DEADZONE else x * SPEED
            velocity["B"][1] = 0 if abs(y) < DEADZONE else y * SPEED

        move_car(car_A, velocity["A"], "A")
        move_car(car_B, velocity["B"], "B")

        parent_frame.after(16, check_inputs)

    def end_game(winner):
        state["active"] = False
        for widget in parent_frame.winfo_children():
            widget.destroy()
        on_game_over(winner)

    check_inputs()