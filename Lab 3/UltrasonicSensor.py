
from machine import Pin, time_pulse_us
import time


class UltrasonicSensor:
    """
    HC-SR04 ultrasonic distance sensor.
    Measures distance in centimeters.
    """

    def __init__(self, trigger_pin=4, echo_pin=5,
                 threshold_cm=30):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.threshold_cm = threshold_cm

        self.trigger.value(0)
        time.sleep_ms(100)

    def getDistance(self):
        """Return distance in cm, or None if no echo."""

        self.trigger.value(0)
        time.sleep_us(2)

        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)

        try:
            duration = time_pulse_us(
                self.echo, 1, 30000
            )

            if duration < 0:
                return None

            return duration / 58.0

        except OSError:
            return None

    def isDetected(self):
        """Check whether someone is nearby."""
        distance = self.getDistance()

        return (
            distance is not None
            and 2 <= distance <= self.threshold_cm
        )
