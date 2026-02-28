#this doesn't have anything rn. it prolly will eventually.

from gpiozero import Servo
from time import sleep

# Use GPIO 18. min_pulse and max_pulse might need tuning for your specific ESC
# Standard RC range is usually 1ms to 2ms
esc = Servo(18, min_pulse_width=1/1000, max_pulse_width=2/1000)

print("Initializing ESC... setting to neutral")
esc.value = 0  # Neutral
sleep(2)

print("Testing Forward...")
esc.value = 0.2
sleep(1)

print("Stopping...")
esc.value = 0