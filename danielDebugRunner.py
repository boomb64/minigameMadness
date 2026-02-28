import tkinter as tk
import importlib
import os
import sys


class GameDebugger:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini-Game Debugger")
        self.root.geometry("800x700")
        self.root.configure(bg="#222")

        # --- Sidebar / Controls ---
        self.controls = tk.Frame(self.root, bg="#333", width=200)
        self.controls.pack(side="left", fill="y")

        tk.Label(self.controls, text="Debug Panel", fg="white", bg="#333", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(self.controls, text="Game Filename:", fg="white", bg="#333").pack(pady=(10, 0))
        self.entry = tk.Entry(self.controls)
        self.entry.insert(0, "pong.py")  # Default suggestion
        self.entry.pack(pady=5, padx=10)

        self.btn_run = tk.Button(self.controls, text="Load / Restart", command=self.load_game, bg="#4CAF50", fg="white")
        self.btn_run.pack(pady=10, fill="x", padx=10)

        self.status_label = tk.Label(self.controls, text="Status: Idle", fg="gray", bg="#333")
        self.status_label.pack(side="bottom", pady=10)

        # --- Game Display Area ---
        self.game_container = tk.Frame(self.root, bg="black", highlightbackground="white", highlightthickness=1)
        self.game_container.pack(side="right", expand=True, fill="both", padx=20, pady=20)

    def load_game(self):
        # 1. Clear existing game
        for widget in self.game_container.winfo_children():
            widget.destroy()

        filename = self.entry.get().strip()
        if filename.endswith(".py"):
            module_name = filename[:-3]
        else:
            module_name = filename

        try:
            # 2. Dynamic Import from the minigames folder
            # Ensure the folder is in the path
            if "minigames" not in sys.modules:
                full_module_path = f"minigames.{module_name}"
            else:
                full_module_path = f"minigames.{module_name}"

            game_module = importlib.import_module(full_module_path)
            importlib.reload(game_module)  # Force reload to catch latest code changes

            # 3. Start the game
            # We pass a dummy 'handle_winner' so it doesn't try to loop the whole handler
            game_module.start_game(self.game_container, self.dummy_callback)

            self.status_label.config(text=f"Status: Playing {module_name}", fg="#4CAF50")
            print(f"DEBUG: Successfully loaded {module_name}")

        except Exception as e:
            self.status_label.config(text="Status: Error", fg="red")
            print(f"DEBUG ERROR: {e}")

    def dummy_callback(self, winner):
        """Replaces the handler's win logic so we can see the result without crashing."""
        print(f"DEBUG RESULT: Game ended. Winner would have been: {winner}")
        # Automatically show a 'Game Over' overlay in the debug window
        lbl = tk.Label(self.game_container, text=f"DEBUG: {winner} WON", font=("Arial", 20), fg="yellow", bg="black")
        lbl.place(relx=0.5, rely=0.5, anchor="center")


if __name__ == "__main__":
    root = tk.Tk()
    app = GameDebugger(root)
    root.mainloop()