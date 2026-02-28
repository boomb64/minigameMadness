import tkinter as tk
import pygame
import random
import time

# Xbox Mapping
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

    # 2. Assign Roles Randomly
    teams = ["Team A", "Team B"]
    team_x = random.choice(teams)
    team_o = "Team B" if team_x == "Team A" else "Team A"

    state = {
        "active": True,
        "board": [["", "", ""], ["", "", ""], ["", "", ""]],
        "roles": {team_x: "X", team_o: "O"},
        "turn": team_x,  # X always goes first
        "turn_start": time.time(),
        "cursors": {
            # Team A is always Blue, Team B is always Pink
            "Team A": {"x": 300, "y": 300, "prev_a": False, "color": "blue"},
            "Team B": {"x": 300, "y": 300, "prev_a": False, "color": "pink"}
        }
    }

    # 3. Setup GUI
    # Using a 600x600 board with a 100px header
    canvas = tk.Canvas(parent_frame, width=600, height=700, bg="black", highlightthickness=0)
    canvas.pack(expand=True)

    def draw_static_board():
        # Grid Lines
        canvas.create_line(200, 100, 200, 700, fill="white", width=4)
        canvas.create_line(400, 100, 400, 700, fill="white", width=4)
        canvas.create_line(0, 300, 600, 300, fill="white", width=4)
        canvas.create_line(0, 500, 600, 500, fill="white", width=4)

        # Header Text (Now pulling colors dynamically from the state dictionary)
        canvas.create_text(150, 50, text=f"Team A: {state['roles']['Team A']}",
                           fill=state["cursors"]["Team A"]["color"], font=("Arial", 20, "bold"))
        canvas.create_text(450, 50, text=f"Team B: {state['roles']['Team B']}",
                           fill=state["cursors"]["Team B"]["color"], font=("Arial", 20, "bold"))

    draw_static_board()

    # UI Elements we update every frame
    timer_text = canvas.create_text(300, 30, text="", fill="yellow", font=("Courier", 24, "bold"))
    turn_text = canvas.create_text(300, 70, text="", fill="white", font=("Arial", 16))

    def check_win(board, mark):
        # Rows and Cols
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] == mark: return True
            if board[0][i] == board[1][i] == board[2][i] == mark: return True
        # Diagonals
        if board[0][0] == board[1][1] == board[2][2] == mark: return True
        if board[0][2] == board[1][1] == board[2][0] == mark: return True
        return False

    def check_tie(board):
        for row in board:
            if "" in row: return False
        return True

    def get_grid_cell(x, y):
        """Converts raw canvas coordinates to board indices (row, col)"""
        col = max(0, min(2, int(x // 200)))
        row = max(0, min(2, int((y - 100) // 200)))
        return row, col

    def update_game():
        if not state["active"]: return

        pygame.event.pump()
        current_time = time.time()
        time_elapsed = current_time - state["turn_start"]

        time_left = 2.0 - time_elapsed

        # A. Timer Logic (If time runs out, current turn loses)
        if time_left <= 0:
            winner = "Team B" if state["turn"] == "Team A" else "Team A"
            end_game(winner)
            return

        # Clear dynamic elements from previous frame
        canvas.delete("dynamic")

        # B. Process Inputs for BOTH teams
        cursor_speed = 18

        for i, team in enumerate(["Team A", "Team B"]):
            c_state = state["cursors"][team]

            if i < len(joysticks):
                joy = joysticks[i]

                # Analog Movement
                axis_x = joy.get_axis(AXIS_X)
                axis_y = joy.get_axis(AXIS_Y)

                # Deadzone check
                if abs(axis_x) > 0.2: c_state["x"] += axis_x * cursor_speed
                if abs(axis_y) > 0.2: c_state["y"] += axis_y * cursor_speed

                # Constrain to grid area
                c_state["x"] = max(0, min(600, c_state["x"]))
                c_state["y"] = max(100, min(700, c_state["y"]))

                # Button A Logic
                current_a = joy.get_button(BUTTON_A)

                if current_a and not c_state["prev_a"]:
                    if state["turn"] == team and time_elapsed > 0.1:

                        row, col = get_grid_cell(c_state["x"], c_state["y"])

                        if state["board"][row][col] == "":
                            state["board"][row][col] = state["roles"][team]

                            mark = state["roles"][team]
                            if check_win(state["board"], mark):
                                end_game(team)
                                return
                            elif check_tie(state["board"]):
                                end_game("Tie")
                                return

                            state["turn"] = "Team B" if team == "Team A" else "Team A"
                            state["turn_start"] = time.time()

                c_state["prev_a"] = current_a

        # C. Draw Dynamic Elements
        active_cursor = state["cursors"][state["turn"]]
        row, col = get_grid_cell(active_cursor["x"], active_cursor["y"])
        hx, hy = col * 200, 100 + (row * 200)
        canvas.create_rectangle(hx, hy, hx + 200, hy + 200, fill="#222", outline="", tags="dynamic")

        for r in range(3):
            for c in range(3):
                mark = state["board"][r][c]
                if mark != "":
                    cx, cy = (c * 200) + 100, 100 + (r * 200) + 100
                    # Determines color by checking which team owns the placed mark
                    color = state["cursors"]["Team A"]["color"] if state["roles"]["Team A"] == mark else state["cursors"]["Team B"]["color"]
                    canvas.create_text(cx, cy, text=mark, fill=color, font=("Arial", 100, "bold"), tags="dynamic")

        for team in ["Team A", "Team B"]:
            c_state = state["cursors"][team]
            rad = 8
            canvas.create_oval(c_state["x"] - rad, c_state["y"] - rad, c_state["x"] + rad, c_state["y"] + rad,
                               fill=c_state["color"], outline="white", tags="dynamic")

        canvas.itemconfig(timer_text, text=f"{time_left:.2f}s")

        # Make the timer flash red when under 0.5 seconds
        if time_left < 0.5:
            canvas.itemconfig(timer_text, fill="red")
        else:
            canvas.itemconfig(timer_text, fill="yellow")

        color_turn = state["cursors"][state["turn"]]["color"]
        canvas.itemconfig(turn_text, text=f"{state['turn']}'s Turn ({state['roles'][state['turn']]})", fill=color_turn)

        parent_frame.after(16, update_game)

    def end_game(winner):
        state["active"] = False
        canvas.destroy()
        on_game_over(winner)

    update_game()