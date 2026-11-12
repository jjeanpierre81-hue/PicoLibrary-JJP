
from UltrasonicSensor import UltrasonicSensor
import time

sensor = UltrasonicSensor(
    trigger_pin=4,
    echo_pin=5,
    threshold_cm=30
)

while True:
    distance = sensor.getDistance()

    if distance is None:
        print("No echo detected")
    else:
        print("Distance:", round(distance, 1), "cm")

        if sensor.isDetected():
            print("Customer detected!")

    time.sleep(1)
