import tkinter as tk
from PIL import Image, ImageTk
import pygame
import random
import math
import os

# Mapping for Xbox Controllers
BUTTON_A = 0
AXIS_X = 0
AXIS_Y = 1


def start_game(parent_frame, on_game_over):
    pygame.init()
    pygame.joystick.init()

    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joy in joysticks:
        joy.init()

    # --- ASSET LOADING ---
    # 1. Anchor the path to the directory where pacman.py lives
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    def load_sprite(path, size=(32, 32)):
        full_path = os.path.join(BASE_DIR, path)
        try:
            img = Image.open(full_path).resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading {full_path}: {e}")
            return None

    GHOST_COLOR_KEYS = ["ghost_red", "ghost_cyan", "ghost_orange", "ghost_pink"]

    # 2. Attach sprites to parent_frame to prevent Tkinter garbage collection
    parent_frame.sprites = {
        "pac_open": load_sprite("assets/pac_open.png"),
        "pac_closed": load_sprite("assets/pac_closed.png"),
        "ghost_red": load_sprite("assets/ghost_red.png"),
        "ghost_cyan": load_sprite("assets/ghost_cyan.png"),
        "ghost_orange": load_sprite("assets/ghost_orange.png"),
        "ghost_pink": load_sprite("assets/ghost_pink.png"),
        "ghost_dead": load_sprite("assets/ghost_dead.png"),
        "power": load_sprite("assets/power_pellet.png", (22, 22))
    }

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
        for c in range(cols): grid[mid_row][c] = 0
        return grid

    # UI & Game Settings
    main_container = tk.Frame(parent_frame, bg="black")
    main_container.pack(expand=True, fill="both")
    game_columns = tk.Frame(main_container, bg="black")
    game_columns.pack(expand=True)

    ROWS, COLS = 13, 13
    CELL_SIZE = 35
    MOVE_SPEED = 0.20
    GHOST_SPEED = 0.08
    NUM_POWERS = 4  # Number of random power pellets per player

    canvases = []
    for i in range(2):
        c = tk.Canvas(game_columns, width=COLS * CELL_SIZE, height=ROWS * CELL_SIZE, bg="black", highlightthickness=0)
        c.pack(side="left", padx=50)
        canvases.append(c)

    state = {"active": True, "frame_count": 0, "players": []}

    for i in range(2):
        m = generate_maze(ROWS, COLS)
        m[6][6] = 0  # Ghost spawn
        m[1][1] = 0  # Player spawn

        # 1. Find all available floor tiles
        floor_tiles = [(r, c) for r in range(ROWS) for c in range(COLS) if m[r][c] == 0]

        # 2. Safety: remove spawns so you don't start on a power pellet
        if (1, 1) in floor_tiles: floor_tiles.remove((1, 1))
        if (6, 6) in floor_tiles: floor_tiles.remove((6, 6))

        # 3. Randomize Power Pellet locations
        random_powers = random.sample(floor_tiles, min(NUM_POWERS, len(floor_tiles)))

        # 4. Every OTHER floor tile becomes a regular pellet
        random_pellets = [tile for tile in floor_tiles if tile not in random_powers]

        state["players"].append({
            "x": 1.0, "y": 1.0, "vx": MOVE_SPEED, "vy": 0, "maze": m,
            "pellets": set(random_pellets),
            "powers": set(random_powers),
            "power_timer": 0,
            "angle": 0,
            "ghosts": [{"x": 6.0, "y": 6.0, "vx": GHOST_SPEED, "vy": 0, "color": random.choice(GHOST_COLOR_KEYS)}]
        })

    def draw_screens():
        state["frame_count"] += 1
        is_open = (state["frame_count"] // 5) % 2 == 0
        for i in range(2):
            canvas = canvases[i]
            p = state["players"][i]
            canvas.delete("all")
            for r in range(ROWS):
                for c in range(COLS):
                    x1, y1 = c * CELL_SIZE, r * CELL_SIZE
                    if p["maze"][r][c] == 1:
                        canvas.create_rectangle(x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE, fill="#1919A6", outline="")
                    elif (r, c) in p["powers"]:
                        # 3. Update dictionary references
                        if parent_frame.sprites["power"]: canvas.create_image(x1 + 17, y1 + 17,
                                                                              image=parent_frame.sprites["power"])
                    elif (r, c) in p["pellets"]:
                        canvas.create_oval(x1 + 15, y1 + 15, x1 + 19, y1 + 19, fill="#FFB8AE", outline="")
            for g in p["ghosts"]:
                img_key = "ghost_dead" if p["power_timer"] > 0 else g["color"]
                g_img = parent_frame.sprites.get(img_key)
                if g_img: canvas.create_image(g["x"] * CELL_SIZE + 17, g["y"] * CELL_SIZE + 17, image=g_img)
            p_img = parent_frame.sprites["pac_open"] if is_open else parent_frame.sprites["pac_closed"]
            if p_img: canvas.create_image(p["x"] * CELL_SIZE + 17, p["y"] * CELL_SIZE + 17, image=p_img)

    def check_inputs():
        if not state["active"]: return
        pygame.event.pump()
        for i in range(min(len(joysticks), 2)):
            joy, p = joysticks[i], state["players"][i]
            raw_x, raw_y = joy.get_axis(AXIS_X), joy.get_axis(AXIS_Y)
            if abs(raw_x) > 0.5:
                tx, ty = int(round(p["x"] + (1 if raw_x > 0 else -1))), int(round(p["y"]))
                if 0 <= tx < COLS and p["maze"][ty][tx] == 0:
                    p["vx"], p["vy"], p["y"] = (MOVE_SPEED if raw_x > 0 else -MOVE_SPEED), 0, round(p["y"])
            elif abs(raw_y) > 0.5:
                tx, ty = int(round(p["x"])), int(round(p["y"] + (1 if raw_y > 0 else -1)))
                if 0 <= ty < ROWS and p["maze"][ty][tx] == 0:
                    p["vx"], p["vy"], p["x"] = 0, (MOVE_SPEED if raw_y > 0 else -MOVE_SPEED), round(p["x"])

            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["x"] < -0.4:
                p["x"] = COLS - 0.6
            elif p["x"] > COLS - 0.6:
                p["x"] = -0.4

            fx, fy = p["x"] + (0.55 if p["vx"] > 0 else -0.55 if p["vx"] < 0 else 0), p["y"] + (
                0.55 if p["vy"] > 0 else -0.55 if p["vy"] < 0 else 0)
            gcx, gcy = int(round(fx)), int(round(fy))
            if 0 <= gcx < COLS and 0 <= gcy < ROWS and p["maze"][gcy][gcx] == 1:
                p["vx"], p["vy"], p["x"], p["y"] = 0, 0, round(p["x"]), round(p["y"])

            cur = (int(round(p["y"])), int(round(p["x"])))
            if cur in p["pellets"]: p["pellets"].remove(cur)
            if cur in p["powers"]:
                p["powers"].remove(cur)
                p["power_timer"] = 110

            if p["power_timer"] > 0: p["power_timer"] -= 1

            for g in p["ghosts"]:
                nx, ny = g["x"] + g["vx"], g["y"] + g["vy"]
                if p["maze"][int(round(ny % ROWS))][int(round(nx % COLS))] == 1:
                    g["vx"], g["vy"] = random.choice(
                        [(GHOST_SPEED, 0), (-GHOST_SPEED, 0), (0, GHOST_SPEED), (0, -GHOST_SPEED)])
                else:
                    g["x"], g["y"] = nx, ny

                if g["x"] < 0:
                    g["x"] = COLS - 1
                elif g["x"] > COLS - 1:
                    g["x"] = 0

                if math.dist((p["x"], p["y"]), (g["x"], g["y"])) < 0.6:
                    if p["power_timer"] > 0:
                        g["x"], g["y"], g["color"] = 6.0, 6.0, random.choice(GHOST_COLOR_KEYS)
                    else:
                        p["x"], p["y"], p["vx"], p["vy"] = 1.0, 1.0, 0, 0

        draw_screens()

        # Win condition check
        if not state["players"][0]["pellets"] or not state["players"][1]["pellets"]:
            if not state["players"][0]["pellets"] and not state["players"][1]["pellets"]:
                winner = "Tie"
            elif not state["players"][0]["pellets"]:
                winner = "Blue Wins"
            else:
                winner = "Pink Wins"
            end_game(winner)
        else:
            parent_frame.after(16, check_inputs)

    def end_game(winner_text):
        state["active"] = False
        for widget in parent_frame.winfo_children(): widget.destroy()
        on_game_over(winner_text)

    check_inputs()