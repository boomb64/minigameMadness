#This program runs on the pi only.

from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import socket
import time

# Hardware-timed PWM
factory = PiGPIOFactory()

# --- HARDWARE CONFIG ---
TEAM_NAME = "Team A"  # Change to "Team B" on the other Pi
UDP_PORT = 5005

# Speed Progression
START_LIMIT = 0.22  # Slightly higher starting floor for better low-end torque
SPEED_STEP = 0.08
win_count = 0

# --- PHYSICAL CALIBRATION ---
LEFT_SIDE_FLIP = 1
RIGHT_SIDE_FLIP = -1
LEFT_TRIM = 1.0
RIGHT_TRIM = 0.96  # Adjust if car veers slightly

# --- HARDWARE SETUP ---
esc_left = Servo(18, min_pulse_width=1 / 1000, max_pulse_width=2 / 1000, pin_factory=factory)
esc_right = Servo(19, min_pulse_width=1 / 1000, max_pulse_width=2 / 1000, pin_factory=factory)


def arcade_drive(x, y, ceiling):
    """
    Translates stick input to motor values with a natural 'Game Feel'.
    """
    # 1. Curve the inputs (Exponential Scaling)
    # This makes the center of the stick more precise
    y = (y ** 3) if y >= 0 else -(abs(y) ** 3)
    x = (x ** 3) if x >= 0 else -(abs(x) ** 3)

    # 2. Arcade Mixing
    # Forward/Back + Left/Right
    l_raw = y + x
    r_raw = y - x

    # 3. Dynamic Steering Dampening
    # If we are moving fast forward, reduce steering sensitivity by 20%
    if abs(y) > 0.5:
        l_raw = y + (x * 0.8)
        r_raw = y - (x * 0.8)

    # 4. Apply Speed Ceiling and Calibration
    final_l = max(min(l_raw * ceiling * LEFT_SIDE_FLIP * LEFT_TRIM, 1.0), -1.0)
    final_r = max(min(r_raw * ceiling * RIGHT_SIDE_FLIP * RIGHT_TRIM, 1.0), -1.0)

    return final_l, final_r


def main():
    global win_count
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    sock.settimeout(0.2)  # Safety timeout

    print(f"[{TEAM_NAME}] ARMING... Port: {UDP_PORT}")
    esc_left.value = 0
    esc_right.value = 0
    time.sleep(2)
    print(f"[{TEAM_NAME}] ARCADE LINK ONLINE.")

    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode('utf-8')

                if msg == "WIN":
                    win_count += 1
                    print(f"LEVEL UP! Speed is now {START_LIMIT + (win_count * SPEED_STEP):.2f}")
                    continue

                if "," in msg:
                    parts = msg.split(",")
                    x_input = float(parts[0])
                    y_input = float(parts[1])

                    # Apply Deadzone (Shared with PC logic)
                    if abs(x_input) < 0.12 and abs(y_input) < 0.12:
                        esc_left.value, esc_right.value = 0, 0
                        continue

                    # Calculate Speed Progression
                    ceiling = min(1.0, START_LIMIT + (win_count * SPEED_STEP))

                    # Process Arcade Drive
                    l_val, r_val = arcade_drive(x_input, y_input, ceiling)

                    # Write to hardware
                    esc_left.value = l_val
                    esc_right.value = r_val

            except socket.timeout:
                # SAFE STOP: No signal for 200ms
                esc_left.value = 0
                esc_right.value = 0

    except KeyboardInterrupt:
        esc_left.value = 0
        esc_right.value = 0


if __name__ == "__main__":
    main()