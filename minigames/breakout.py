import tkinter as tk
import pygame
import random
import math

# Xbox Mapping
STICK_X = 0


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # Constants
    CANVAS_W, CANVAS_H = 800, 600
    WALL_WIDTH = 10
    PADDLE_W, PADDLE_H = 85, 15
    BALL_RAD = 8
    BRICK_ROWS, BRICK_COLS = 4, 5
    POWERUP_RAD = 10
    ACCEL_FACTOR = 1.05
    MAX_SPEED = 14.0

    state = {
        "active": True,
        "Team A": {
            "color": "blue", "paddle_x": 200, "lives": 3,
            "balls": [{"x": 200, "y": 400, "vx": 4.5, "vy": -4.5}],
            "bricks": [], "powerups": []
        },
        "Team B": {
            "color": "pink", "paddle_x": 600, "lives": 3,
            "balls": [{"x": 600, "y": 400, "vx": 4.5, "vy": -4.5}],
            "bricks": [], "powerups": []
        }
    }

    # Initialize Bricks (Solid wall with white outlines)
    for team in ["Team A", "Team B"]:
        lane_min = WALL_WIDTH if team == "Team A" else 400 + (WALL_WIDTH / 2)
        lane_max = 400 - (WALL_WIDTH / 2) if team == "Team A" else 800 - WALL_WIDTH
        play_area_w = lane_max - lane_min

        brick_w = play_area_w / BRICK_COLS
        brick_h = 35

        for r in range(BRICK_ROWS):
            for c in range(BRICK_COLS):
                state[team]["bricks"].append(tkRect(
                    lane_min + (c * brick_w),
                    100 + (r * brick_h),
                    brick_w,
                    brick_h
                ))

        # Pick one random brick per side to hold the hidden 3x multiplier
        if state[team]["bricks"]:
            random.choice(state[team]["bricks"]).is_hidden_mult = True

    canvas = tk.Canvas(parent_frame, width=CANVAS_W, height=CANVAS_H, bg="black", highlightthickness=0)
    canvas.pack(expand=True)

    def draw_game():
        if not state["active"]: return
        canvas.delete("all")

        # Static Environment (Walls)
        canvas.create_rectangle(0, 0, WALL_WIDTH, 600, fill="gray30", outline="white")
        canvas.create_rectangle(400 - WALL_WIDTH / 2, 0, 400 + WALL_WIDTH / 2, 600, fill="gray30", outline="white")
        canvas.create_rectangle(800 - WALL_WIDTH, 0, 800, 600, fill="gray30", outline="white")
        canvas.create_rectangle(0, 0, 800, 80, fill="#050505", outline="white")

        for i, team_name in enumerate(["Team A", "Team B"]):
            t = state[team_name]
            joy = joysticks[i] if i < len(joysticks) else None
            lane_min, lane_max = (WALL_WIDTH, 400 - WALL_WIDTH / 2) if team_name == "Team A" else (400 + WALL_WIDTH / 2,
                                                                                                   800 - WALL_WIDTH)

            # 1. Paddle Logic
            if joy:
                axis = joy.get_axis(STICK_X)
                if abs(axis) > 0.1:
                    t["paddle_x"] += axis * 16
            t["paddle_x"] = max(lane_min + PADDLE_W / 2, min(lane_max - PADDLE_W / 2, t["paddle_x"]))

            # 2. Ball Physics & Collision
            for b in t["balls"][:]:
                b["x"] += b["vx"]
                b["y"] += b["vy"]

                # Side Bounce
                if b["x"] - BALL_RAD < lane_min:
                    b["vx"] = abs(b["vx"])
                    b["x"] = lane_min + BALL_RAD
                elif b["x"] + BALL_RAD > lane_max:
                    b["vx"] = -abs(b["vx"])
                    b["x"] = lane_max - BALL_RAD

                # Top Bounce
                if b["y"] - BALL_RAD < 80:
                    b["vy"] = abs(b["vy"])
                    b["y"] = 80 + BALL_RAD

                # Paddle Interaction
                px = t["paddle_x"]
                if (px - PADDLE_W / 2 < b["x"] < px + PADDLE_W / 2) and (550 < b["y"] + BALL_RAD < 565):
                    b["vy"] = -abs(b["vy"]) * ACCEL_FACTOR
                    b["vx"] = (b["vx"] + (b["x"] - px) / 4) * ACCEL_FACTOR

                    # Cap Speed
                    speed = math.sqrt(b["vx"] ** 2 + b["vy"] ** 2)
                    if speed > MAX_SPEED:
                        b["vx"] *= (MAX_SPEED / speed)
                        b["vy"] *= (MAX_SPEED / speed)

                # Brick Interaction
                for brk in t["bricks"][:]:
                    if brk.collidepoint(b["x"], b["y"]):
                        # Determine if hit was side or top/bottom
                        if abs(b["x"] - (brk.x + brk.w / 2)) > (brk.w / 2 * 0.9):
                            b["vx"] *= -ACCEL_FACTOR
                        else:
                            b["vy"] *= -ACCEL_FACTOR

                        t["bricks"].remove(brk)

                        # Trigger hidden multiplier OR normal drop
                        if brk.is_hidden_mult:
                            # Spawn 2 new balls with slight trajectory offsets
                            t["balls"].append({"x": b["x"], "y": b["y"], "vx": b["vx"] + 1.5, "vy": b["vy"]})
                            t["balls"].append({"x": b["x"], "y": b["y"], "vx": b["vx"] - 1.5, "vy": b["vy"]})
                        elif random.random() < 0.25:
                            t["powerups"].append({"x": brk.x + brk.w / 2, "y": brk.y + brk.h / 2})
                        break

                if b["y"] > 600: t["balls"].remove(b)

            # 3. Powerup Collection
            for p in t["powerups"][:]:
                p["y"] += 4.5
                if (t["paddle_x"] - PADDLE_W / 2 < p["x"] < t["paddle_x"] + PADDLE_W / 2) and (550 < p["y"] < 570):
                    t["balls"].append({"x": t["paddle_x"], "y": 540, "vx": random.choice([-5, 5]), "vy": -5})
                    t["powerups"].remove(p)
                elif p["y"] > 600:
                    t["powerups"].remove(p)

            # 4. Win/Loss Logic
            if not t["balls"]:
                t["lives"] -= 1
                if t["lives"] <= 0:
                    end_game("Team B" if team_name == "Team A" else "Team A")
                    return
                t["balls"].append({"x": (lane_min + lane_max) / 2, "y": 400, "vx": 5, "vy": -5})

            if not t["bricks"]:
                end_game(team_name)
                return

            # --- RENDERING ---
            # Paddle & HUD
            canvas.create_rectangle(t["paddle_x"] - PADDLE_W / 2, 550, t["paddle_x"] + PADDLE_W / 2, 565,
                                    fill=t["color"], outline="white")
            canvas.create_text(lane_min + 60, 40, text=f"LIVES: {t['lives']}", fill="white",
                               font=("Courier", 18, "bold"))

            # Bricks with Small White Outlines
            for brk in t["bricks"]:
                canvas.create_rectangle(brk.x, brk.y, brk.x + brk.w, brk.y + brk.h,
                                        fill=t["color"], outline="white", width=1)

            # Balls & Powerups
            for b in t["balls"]:
                canvas.create_oval(b["x"] - BALL_RAD, b["y"] - BALL_RAD, b["x"] + BALL_RAD, b["y"] + BALL_RAD,
                                   fill="white", outline="gray")
            for p in t["powerups"]:
                canvas.create_oval(p["x"] - POWERUP_RAD, p["y"] - POWERUP_RAD, p["x"] + POWERUP_RAD,
                                   p["y"] + POWERUP_RAD, fill="yellow", outline="white")

        parent_frame.after(16, draw_game)

    def end_game(winner):
        state["active"] = False
        canvas.destroy()
        on_game_over(winner)

    draw_game()


class tkRect:
    def __init__(self, x, y, w, h, is_hidden_mult=False):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.is_hidden_mult = is_hidden_mult

    def collidepoint(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h