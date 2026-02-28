import tkinter as tk
import pygame
import random

# Mapping for Xbox Controllers (Standard)
BUTTON_A = 0
AXIS_X = 0
AXIS_Y = 1


def start_game(parent_frame, on_game_over):
    # 1. Initialize Pygame Joysticks
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # 2. Maze Generation with Guaranteed Tunnel Path
    def generate_maze(rows, cols):
        grid = [[1 for _ in range(cols)] for _ in range(rows)]
        mid_row = rows // 2

        def walk(r, c):
            grid[r][c] = 0
            dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(dirs)
            for dr, dc in dirs:
                nr, nc = r + (dr * 2), c + (dc * 2)
                if 0 < nr < rows - 1 and 0 < nc < cols - 1 and grid[nr][nc] == 1:
                    grid[r + dr][c + dc] = 0
                    walk(nr, nc)

        walk(1, 1)
        # Clear the entire middle row for the tunnel
        for c in range(cols):
            grid[mid_row][c] = 0
        return grid

    # 3. Setup GUI
    main_container = tk.Frame(parent_frame, bg="black")
    main_container.pack(expand=True, fill="both")

    label = tk.Label(main_container, text="PAC-MAN SPEED RACE", font=("Arial", 22, "bold"), fg="yellow", bg="black")
    label.pack(pady=15)

    game_columns = tk.Frame(main_container, bg="black")
    game_columns.pack(expand=True)

    ROWS, COLS = 13, 13
    CELL_SIZE = 35
    MOVE_SPEED = 0.20  # Consistent speed

    maze_a = generate_maze(ROWS, COLS)
    maze_b = generate_maze(ROWS, COLS)

    state = {
        "active": True,
        "frame_count": 0,
        "players": [
            {
                "x": 1.0, "y": 1.0, "vx": MOVE_SPEED, "vy": 0, "maze": maze_a, "color": "#FFFF00",
                "pellets": set([(r, c) for r in range(ROWS) for c in range(COLS) if maze_a[r][c] == 0]),
                "angle": 0
            },
            {
                "x": 1.0, "y": 1.0, "vx": MOVE_SPEED, "vy": 0, "maze": maze_b, "color": "#00FFFF",
                "pellets": set([(r, c) for r in range(ROWS) for c in range(COLS) if maze_b[r][c] == 0]),
                "angle": 0
            }
        ]
    }

    canvases = []
    for i in range(2):
        canvas = tk.Canvas(game_columns, width=COLS * CELL_SIZE, height=ROWS * CELL_SIZE, bg="black", borderwidth=0,
                           highlightthickness=3, highlightbackground="#333333")
        canvas.pack(side="left", padx=50)
        canvases.append(canvas)

    def draw_screens():
        state["frame_count"] += 1
        mouth_open = 45 if (state["frame_count"] // 5) % 2 == 0 else 15

        for i in range(2):
            canvas = canvases[i]
            p = state["players"][i]
            canvas.delete("all")

            for r in range(ROWS):
                for c in range(COLS):
                    x1, y1 = c * CELL_SIZE, r * CELL_SIZE
                    if p["maze"][r][c] == 1:
                        canvas.create_rectangle(x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE, fill="#1919A6",
                                                outline="#000055")
                    elif (r, c) in p["pellets"]:
                        cx, cy = x1 + CELL_SIZE // 2, y1 + CELL_SIZE // 2
                        canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill="#FFB8AE")

            px, py = p["x"] * CELL_SIZE, p["y"] * CELL_SIZE
            start_angle = p["angle"] + mouth_open
            extent_angle = 360 - (2 * mouth_open)
            canvas.create_arc(px + 3, py + 3, px + CELL_SIZE - 3, py + CELL_SIZE - 3, start=start_angle,
                              extent=extent_angle, fill=p["color"], outline=p["color"])

    def check_inputs():
        if not state["active"]: return
        pygame.event.pump()

        for i in range(min(len(joysticks), 2)):
            joy = joysticks[i]
            p = state["players"][i]

            raw_x, raw_y = joy.get_axis(AXIS_X), joy.get_axis(AXIS_Y)

            # Directional Buffering & Grid Snapping
            if abs(raw_x) > 0.5:
                tx, ty = int(round(p["x"]) + (1 if raw_x > 0 else -1)), int(round(p["y"]))
                if 0 <= tx < COLS and p["maze"][ty][tx] == 0:
                    p["vx"], p["vy"] = (MOVE_SPEED if raw_x > 0 else -MOVE_SPEED), 0
                    p["y"] = round(p["y"])  # SNAP to center of path
                    p["angle"] = 0 if raw_x > 0 else 180
            elif abs(raw_y) > 0.5:
                tx, ty = int(round(p["x"])), int(round(p["y"]) + (1 if raw_y > 0 else -1))
                if 0 <= ty < ROWS and p["maze"][ty][tx] == 0:
                    p["vx"], p["vy"] = 0, (MOVE_SPEED if raw_y > 0 else -MOVE_SPEED)
                    p["x"] = round(p["x"])  # SNAP to center of path
                    p["angle"] = 270 if raw_y > 0 else 90

            # Predicted Movement
            p["x"] += p["vx"]
            p["y"] += p["vy"]

            # Screen Wrap
            if p["x"] < -0.4:
                p["x"] = COLS - 0.6
            elif p["x"] > COLS - 0.6:
                p["x"] = -0.4

            # Precise Collision: check 0.5 units ahead of the pivot
            front_x = p["x"] + (0.55 if p["vx"] > 0 else -0.55 if p["vx"] < 0 else 0)
            front_y = p["y"] + (0.55 if p["vy"] > 0 else -0.55 if p["vy"] < 0 else 0)

            grid_cx, grid_cy = int(round(front_x)), int(round(front_y))

            if 0 <= grid_cx < COLS and 0 <= grid_cy < ROWS:
                if p["maze"][grid_cy][grid_cx] == 1:
                    # STOP: Re-align perfectly to current cell center
                    p["vx"], p["vy"] = 0, 0
                    p["x"], p["y"] = round(p["x"]), round(p["y"])

            # Pellet Collection
            cur_pos = (int(round(p["y"])), int(round(p["x"])))
            if cur_pos in p["pellets"]:
                p["pellets"].remove(cur_pos)

        draw_screens()

        if len(state["players"][0]["pellets"]) == 0 or len(state["players"][1]["pellets"]) == 0:
            winner = "PLAYER 1" if len(state["players"][0]["pellets"]) == 0 else "PLAYER 2"
            end_game(f"{winner} WINS!")
        else:
            parent_frame.after(16, check_inputs)

    def end_game(winner_text):
        state["active"] = False
        for widget in parent_frame.winfo_children(): widget.destroy()
        on_game_over(winner_text)

    check_inputs()